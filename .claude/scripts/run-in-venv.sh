#!/bin/bash
# Activate virtualenv and run command
# Usage: ./run-in-venv.sh <command>

set -e

# Get the repo root (parent of .claude directory)
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV_PATH="$REPO_ROOT/.virtualenv"

if [ ! -d "$VENV_PATH" ]; then
    echo "Error: virtualenv not found at $VENV_PATH, run /setup skill first"
    exit 1
fi

# Activate virtualenv and run command
source "$VENV_PATH/bin/activate"
exec "$@"
