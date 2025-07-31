#!/bin/bash
# Rich System Monitor - Installation Script
# Creates virtual environment and installs dependencies

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "🚀 Rich System Monitor - Installation"
echo "======================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not found."
    echo "   Please install Python 3 and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if venv module is available
if ! python3 -c "import venv" &> /dev/null; then
    echo "❌ Error: Python venv module not found."
    echo "   Please install python3-venv package:"
    echo "   sudo apt install python3-venv  # On Ubuntu/Debian"
    echo "   sudo yum install python3-venv  # On CentOS/RHEL"
    exit 1
fi

# Remove existing venv if it exists
if [ -d "$VENV_DIR" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Make scripts executable
chmod +x "$SCRIPT_DIR/run.sh"
chmod +x "$SCRIPT_DIR/sysmon"

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "Usage:"
echo "  ./run.sh           # Single report"
echo "  ./run.sh --live    # Live monitoring"
echo "  ./run.sh --fast    # Fast live monitoring"
echo "  ./run.sh --help    # Show help"
echo ""
echo "Or use the convenient wrapper:"
echo "  ./sysmon           # Single report"
echo "  ./sysmon --live    # Live monitoring"
echo ""
echo "To uninstall, simply delete this directory."
