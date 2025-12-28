#!/bin/bash
# Install 'anos' command to PATH
# Makes 'anos' available system-wide

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_step "Installing 'anos' command..."

# Detect shell
SHELL_NAME=$(basename "$SHELL" 2>/dev/null || echo "bash")
CONFIG_FILE=""

case "$SHELL_NAME" in
    bash)
        if [ -f "$HOME/.bashrc" ]; then
            CONFIG_FILE="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            CONFIG_FILE="$HOME/.bash_profile"
        fi
        ;;
    zsh)
        if [ -f "$HOME/.zshrc" ]; then
            CONFIG_FILE="$HOME/.zshrc"
        fi
        ;;
    fish)
        CONFIG_FILE="$HOME/.config/fish/config.fish"
        mkdir -p "$HOME/.config/fish"
        ;;
esac

# Option 1: Add to PATH via symlink in ~/.local/bin (recommended)
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

if [ -L "$LOCAL_BIN/anos" ]; then
    rm "$LOCAL_BIN/anos"
fi

ln -sf "$PROJECT_ROOT/scripts/anos" "$LOCAL_BIN/anos"
log_info "Created symlink: $LOCAL_BIN/anos -> $PROJECT_ROOT/scripts/anos"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    log_info "Adding $LOCAL_BIN to PATH..."
    
    if [ -n "$CONFIG_FILE" ]; then
        if [ "$SHELL_NAME" = "fish" ]; then
            echo "" >> "$CONFIG_FILE"
            echo "# ANOS - Agent OS" >> "$CONFIG_FILE"
            echo "set -gx PATH \$HOME/.local/bin \$PATH" >> "$CONFIG_FILE"
        else
            echo "" >> "$CONFIG_FILE"
            echo "# ANOS - Agent OS" >> "$CONFIG_FILE"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$CONFIG_FILE"
        fi
        log_info "Added to $CONFIG_FILE"
    else
        log_info "Please add this to your shell config:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
else
    log_info "PATH already includes $LOCAL_BIN"
fi

echo ""
log_step "✅ Installation complete!"
echo ""
log_info "To use 'anos' command:"
echo "  1. Restart your terminal, or"
echo "  2. Run: source $CONFIG_FILE"
echo ""
log_info "Then just type: anos"
echo ""

