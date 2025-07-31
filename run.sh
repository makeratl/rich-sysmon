#!/bin/bash
# Rich System Monitor - Run Script
# Activates virtual environment and runs the monitor

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/sysmon_rich.py"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run ./install.sh first to set up the environment."
    exit 1
fi

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ sysmon_rich.py not found!"
    echo "   Please ensure the script is in the same directory."
    exit 1
fi

# Activate virtual environment and run the script
source "$VENV_DIR/bin/activate"
python3 "$PYTHON_SCRIPT" "$@"
