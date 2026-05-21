"""
Shared logic for GitHub MCP tools.

Handles serialization, data retrieval, validation, and recommendation
logic for GitHub integration operations.
"""

import re
from datetime import datetime
from typing import Any

from models.datadoc import DataDoc
from models.github import GitHubLink
from models.user import User


def validate_directory_path(directory: str) -> bool:
    """
    Validate directory path format.

    Valid patterns:
    - user/<username>
    - teams/<teamname>
    - teams/<teamname>/<subfolder>
    - shared/<name>
    - datadocs (legacy fallback)

    Must use lowercase letters, numbers, and hyphens only.
    """
    # Allow 'datadocs' as special case
    if directory == "datadocs":
        return True

    # Standard pattern for organized directories
    pattern = r"^(?:user|teams|shared)/[a-z0-9-]+(?:/[a-z0-9-]+)*$"
    return bool(re.match(pattern, directory))


def analyze_directory_structure(directories: list[str]) -> dict:
    """
    Parse flat directory list into organized structure.

    Groups directories by type (user/, teams/, shared/, etc.) with
    metadata about each directory.
    """
    structure = {
        "user": {"description": "Personal DataDocs organized by username", "directories": []},
        "teams": {"description": "Team-shared DataDocs organized by team name", "directories": []},
        "shared": {"description": "Cross-team shared resources", "directories": []},
        "datadocs": {
            "description": "Legacy/unorganized directory (use with caution)",
            "directories": [],
        },
        "other": {"description": "Other directories", "directories": []},
    }

    for dir_path in directories:
        if not dir_path:
            continue

        parts = dir_path.split("/")
        dir_type = parts[0]

        if dir_type in ["user", "teams", "shared", "datadocs"]:
            structure[dir_type]["directories"].append(dir_path)
        else:
            structure["other"]["directories"].append(dir_path)

    return structure


def get_directory_usage_stats(session) -> dict[str, dict[str, Any]]:
    """
    Get statistics about DataDoc distribution across directories.

    Returns dict mapping directory path to usage information.
    """
    from sqlalchemy import func

    stats_query = (
        session.query(
            GitHubLink.directory,
            func.count(GitHubLink.id).label("count"),
            func.max(GitHubLink.updated_at).label("last_updated"),
        )
        .group_by(GitHubLink.directory)
        .all()
    )

    stats = {}
    for directory, count, last_updated in stats_query:
        stats[directory] = {
            "datadoc_count": count,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }

    return stats


def get_smart_default_directory(
    doc: DataDoc, user: User, session
) -> dict[str, Any]:
    """
    Generate directory recommendations for a DataDoc.

    Returns all available directory options with their use cases.
    """
    return {
        "options": [
            {
                "directory": f"user/{user.username}",
                "reason": "For personal work and individual DataDocs",
            },
            {
                "directory": "teams/<your-team-name>",
                "reason": "For team-shared work. Would you like me to show you existing teams? (get_github_directories)",
            },
            {
                "directory": "datadocs",
                "reason": "For temporary/unorganized work (not recommended for long-term use)",
            },
        ],
    }


def generate_directory_recommendations(
    user: User, directories: list[str], usage_stats: dict, session
) -> list[dict]:
    """
    Generate personalized directory recommendations for a user.

    Returns list of recommended directories with reasoning.
    """
    recommendations = []

    # Always recommend user's personal directory
    user_dir = f"user/{user.username}"
    user_dir_exists = user_dir in directories

    recommendations.append(
        {
            "path": user_dir,
            "reason": "Your personal directory - recommended for individual work",
            "confidence": "high",
            "action": "link_to_this",
            "exists": user_dir_exists,
            "usage": usage_stats.get(user_dir, {"datadoc_count": 0}),
        }
    )

    # Find team directories user has contributed to
    from models.github import GitHubLink

    user_team_dirs = (
        session.query(GitHubLink.directory)
        .filter(
            GitHubLink.user_id == user.id,
            GitHubLink.directory.like("team/%"),
        )
        .distinct()
        .all()
    )

    for (team_dir,) in user_team_dirs:
        if team_dir in directories:
            usage = usage_stats.get(team_dir, {"datadoc_count": 0})
            recommendations.append(
                {
                    "path": team_dir,
                    "reason": f"You've contributed here before ({usage['datadoc_count']} docs)",
                    "confidence": "medium",
                    "action": "consider",
                    "exists": True,
                    "usage": usage,
                }
            )

    return recommendations


def format_commit_message(user_message: str, metadata: dict, datadoc_id: int) -> str:
    """
    Format commit message with metadata footers.

    Follows Git trailer format for structured metadata that's
    parseable by git log and other tools.
    """
    lines = [
        user_message,
        "",  # Blank line separator required by Git trailer convention
        f"DataDoc-ID: {datadoc_id}",
        f"Created-Via: {metadata['source'].upper()}",
    ]

    # Add MCP-specific metadata if available
    if metadata.get("tool"):
        lines.append(f"MCP-Tool: {metadata['tool']}")
    if metadata.get("client"):
        lines.append(f"MCP-Client: {metadata['client']}")

    # Always include user info
    lines.append(f"Querybook-User: {metadata['user']} (uid: {metadata['uid']})")

    return "\n".join(lines)


def serialize_commit(commit: dict) -> dict:
    """
    Serialize GitHub commit to MCP-friendly format.

    Extracts relevant fields from GitHub API commit response.
    """
    return {
        "sha": commit["sha"],
        "short_sha": commit["sha"][:7],
        "message": commit["commit"]["message"],
        "author": commit["commit"]["author"]["name"],
        "author_email": commit["commit"]["author"]["email"],
        "date": commit["commit"]["author"]["date"],
        "url": commit["html_url"],
        "committer": commit["commit"]["committer"]["name"],
    }


def serialize_github_status(
    github_link: GitHubLink,
    last_commit_info: dict | None,
    repo_name: str,
    branch: str,
    notes: str | None = None,
) -> dict:
    """
    Serialize GitHub link status to MCP-friendly format.

    Includes link information, tracking stats, latest commit info, and resource URI.
    """
    file_path = f"{github_link.directory}/datadoc_{github_link.datadoc_id}.md"
    github_url = f"https://github.com/{repo_name}/blob/{branch}/{file_path}"

    status = {
        "datadoc_id": github_link.datadoc_id,
        "linked": True,
        "directory": github_link.directory,
        "file_path": file_path,
        "github_url": github_url,
        "history_resource_uri": f"querybook://datadoc/{github_link.datadoc_id}/github-history?limit=20&offset=0",
    }

    # Add last commit info if available
    if last_commit_info:
        status["last_commit"] = last_commit_info

    if notes:
        status["notes"] = notes

    return status


def get_token_suffix(token) -> str:
    """
    Get last 6 characters of API token for identification.

    Used to correlate commits with API tokens without exposing full token.
    """
    if hasattr(token, "claims") and "token_suffix" in token.claims:
        return token.claims["token_suffix"]

    # Could also try to get from token string if accessible
    # For now, return placeholder
    return "unknown"
