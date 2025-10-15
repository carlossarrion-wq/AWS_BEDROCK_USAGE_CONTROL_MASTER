#!/bin/bash
# Helper script to run provision_bedrock_user.py with the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run the provision script with all arguments passed to this script
python3 "$SCRIPT_DIR/provision_bedrock_user.py" "$@"

# Deactivate virtual environment
deactivate
