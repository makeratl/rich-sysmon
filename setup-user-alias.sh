#!/bin/bash
# Rich System Monitor - User Alias Setup
# Adds alias to your shell profile so you can run 'sysmon' from anywhere

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSMON_SCRIPT="$SCRIPT_DIR/sysmon"

echo "🚀 Rich System Monitor - User Alias Setup"
echo "=========================================="

# Check if script exists
if [ ! -f "$SYSMON_SCRIPT" ]; then
    echo "❌ Error: sysmon script not found at $SYSMON_SCRIPT"
    echo "   Please run this from the rich-sysmon directory."
    exit 1
fi

# Make sure the sysmon script is executable
chmod +x "$SYSMON_SCRIPT"

# Determine which shell profile to use
SHELL_PROFILE=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_PROFILE="$HOME/.profile"
else
    echo "❌ Could not find a shell profile file to modify."
    echo "   Please manually add this line to your shell profile:"
    echo "   alias sysmon='$SYSMON_SCRIPT'"
    exit 1
fi

# Create the alias line
ALIAS_LINE="alias sysmon='$SYSMON_SCRIPT'"

# Check if alias already exists
if grep -q "alias sysmon=" "$SHELL_PROFILE" 2>/dev/null; then
    echo "🔄 Updating existing sysmon alias in $SHELL_PROFILE"
    # Remove old alias and add new one
    sed -i '/alias sysmon=/d' "$SHELL_PROFILE"
else
    echo "➕ Adding new sysmon alias to $SHELL_PROFILE"
fi

# Add the alias
echo "" >> "$SHELL_PROFILE"
echo "# Rich System Monitor alias" >> "$SHELL_PROFILE"
echo "$ALIAS_LINE" >> "$SHELL_PROFILE"

echo ""
echo "✅ Alias added successfully!"
echo ""
echo "To use the alias immediately, run:"
echo "  source $SHELL_PROFILE"
echo ""
echo "Or open a new terminal and use:"
echo "  sysmon           # Single report"
echo "  sysmon --live    # Live monitoring"
echo "  sysmon --fast    # Fast live monitoring"
echo "  sysmon --help    # Show help"
echo ""
echo "Test it now (after sourcing):"
echo "  source $SHELL_PROFILE && sysmon"
