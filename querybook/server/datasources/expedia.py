import requests
from flask_login import current_user

from app.datasource import register, api_assert
from env import QuerybookSettings
from lib.logger import get_logger

LOG = get_logger(__file__)

# Get GraphQL endpoint from environment settings
# You can set this via ANALYTICS_WORKBENCH_GRAPHQL_ENDPOINT environment variable
# or in querybook_config.yaml
GRAPHQL_ENDPOINT = getattr(
    QuerybookSettings, "ANALYTICS_WORKBENCH_GRAPHQL_ENDPOINT", None
)

if not GRAPHQL_ENDPOINT:
    LOG.warning(
        "ANALYTICS_WORKBENCH_GRAPHQL_ENDPOINT not configured. "
        "Set it in querybook_config.yaml or as an environment variable. "
        "Example: http://your-graphql-host:4000/api/v1/graphql"
    )


@register("/expedia/personalized-cost/", methods=["GET"])
def get_personalized_cost(username: str = None):
    """
    Fetch personalized cost data from GraphQL endpoint.

    Args:
        username (str, optional): Username to fetch costs for.
                                  If not provided, uses current user's username.

    Returns:
        dict: Personalized cost summary dashboard data
    """
    # Check if endpoint is configured
    if not GRAPHQL_ENDPOINT:
        api_assert(
            False,
            "EXPEDIA_GRAPHQL_ENDPOINT is not configured. "
            "Please set it in your environment or config file.",
        )

    # Use provided username or default to current user
    if not username:
        username = current_user.username

    api_assert(username, "Username is required")

    # GraphQL query
    query = """
        query PersonalizedSummaryDashboard($username: String!) {
            personalizedCost(username: $username) {
                personalizedSummaryDashboard {
                    totalCostEstimate
                    numberDataDocs
                    numberDags
                    numberExtracts
                    numberTeradataQueries
                    numberTrinoQueries
                }
            }
        }
    """

    try:
        # Make the GraphQL request
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={
                "operationName": "PersonalizedSummaryDashboard",
                "query": query,
                "variables": {"username": username},
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        response.raise_for_status()
        result = response.json()

        # Check for GraphQL errors
        if "errors" in result and result["errors"]:
            error_message = result["errors"][0].get("message", "Unknown GraphQL error")
            LOG.error(f"GraphQL error for user {username}: {error_message}")
            api_assert(False, f"GraphQL error: {error_message}")

        # Extract the data
        cost_data = result.get("data", {}).get("personalizedCost", {})
        dashboard_data = cost_data.get("personalizedSummaryDashboard", {})

        return dashboard_data

    except requests.exceptions.RequestException as e:
        LOG.error(f"Failed to fetch personalized costs for user {username}: {str(e)}")
        api_assert(False, f"Failed to fetch personalized costs: {str(e)}")
    except Exception as e:
        LOG.error(
            f"Unexpected error fetching personalized costs for user {username}: {str(e)}"
        )
        api_assert(False, f"Unexpected error: {str(e)}")
