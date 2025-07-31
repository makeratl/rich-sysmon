#!/bin/bash
# Rich System Monitor - System-wide Alias Installation
# Creates a system-wide alias so you can run 'sysmon' from anywhere

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSMON_SCRIPT="$SCRIPT_DIR/sysmon"
INSTALL_DIR="/usr/local/bin"
SYMLINK_NAME="sysmon"
SYMLINK_PATH="$INSTALL_DIR/$SYMLINK_NAME"

echo "🚀 Rich System Monitor - System-wide Installation"
echo "=================================================="

# Check if script exists
if [ ! -f "$SYSMON_SCRIPT" ]; then
    echo "❌ Error: sysmon script not found at $SYSMON_SCRIPT"
    echo "   Please run this from the rich-sysmon directory."
    exit 1
fi

# Check if we have sudo access
if [ "$EUID" -ne 0 ]; then
    echo "🔐 This script needs sudo access to install to $INSTALL_DIR"
    echo "   You will be prompted for your password."
    echo ""
fi

# Make sure the sysmon script is executable
chmod +x "$SYSMON_SCRIPT"

# Remove existing symlink if it exists
if [ -L "$SYMLINK_PATH" ]; then
    echo "🗑️  Removing existing sysmon symlink..."
    sudo rm -f "$SYMLINK_PATH"
fi

# Create symlink
echo "🔗 Creating symlink: $SYMLINK_PATH -> $SYSMON_SCRIPT"
sudo ln -sf "$SYSMON_SCRIPT" "$SYMLINK_PATH"

# Verify installation
if [ -L "$SYMLINK_PATH" ] && [ -x "$SYMLINK_PATH" ]; then
    echo ""
    echo "✅ Installation completed successfully!"
    echo ""
    echo "You can now run the Rich System Monitor from anywhere using:"
    echo "  sysmon           # Single report"
    echo "  sysmon --live    # Live monitoring"
    echo "  sysmon --fast    # Fast live monitoring"
    echo "  sysmon --help    # Show help"
    echo ""
    echo "Test it now:"
    echo "  sysmon"
else
    echo "❌ Installation failed. Please check permissions and try again."
    exit 1
fi
