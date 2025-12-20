#!/bin/bash
# Cosmic OS KDE Plasma Setup
# Configures KDE Plasma for an iOS-like desktop experience

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLASMA_CONFIGS="$SCRIPT_DIR/plasma-configs"
BACKUP_DIR="$HOME/.config/cosmic-os-backup"

echo "╔══════════════════════════════════════════╗"
echo "║      Cosmic OS KDE Plasma Setup          ║"
echo "╚══════════════════════════════════════════╝"

# Create backup directory
mkdir -p "$BACKUP_DIR"

backup_config() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename "$file").backup.$(date +%Y%m%d_%H%M%S)"
        echo "  ✓ Backed up $(basename "$file")"
    fi
}

echo ""
echo "▶ Backing up current configuration..."
backup_config "$HOME/.config/kdeglobals"
backup_config "$HOME/.config/kwinrc"
backup_config "$HOME/.config/plasmashellrc"
backup_config "$HOME/.config/lattedockrc"

echo ""
echo "▶ Installing required packages..."
# Check if running on Ubuntu/Debian
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y \
        latte-dock \
        plasma-widgets-addons \
        breeze \
        kvantum-qt5 \
        qt5-style-kvantum
fi

# Check if running on Arch
if command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm --needed \
        latte-dock \
        plasma-addons \
        breeze \
        kvantum-qt5
fi

echo ""
echo "▶ Applying KDE global settings..."

# Copy plasma configs
if [ -d "$PLASMA_CONFIGS" ]; then
    cp "$PLASMA_CONFIGS/kdeglobals" "$HOME/.config/kdeglobals" 2>/dev/null || true
    cp "$PLASMA_CONFIGS/kwinrc" "$HOME/.config/kwinrc" 2>/dev/null || true
    cp "$PLASMA_CONFIGS/plasmashellrc" "$HOME/.config/plasmashellrc" 2>/dev/null || true
fi

# Apply settings using kwriteconfig5
echo "  Setting theme..."
kwriteconfig5 --file kdeglobals --group General --key ColorScheme "BreezeDark"
kwriteconfig5 --file kdeglobals --group General --key Name "Breeze Dark"
kwriteconfig5 --file kdeglobals --group KDE --key LookAndFeelPackage "org.kde.breezedark.desktop"

echo "  Setting icon theme..."
kwriteconfig5 --file kdeglobals --group Icons --key Theme "breeze-dark"

echo "  Configuring window decorations..."
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key library "org.kde.breeze"
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key theme "Breeze"
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft ""
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight "IAX"

echo "  Enabling compositor effects..."
kwriteconfig5 --file kwinrc --group Compositing --key OpenGLIsUnsafe "false"
kwriteconfig5 --file kwinrc --group Compositing --key Backend "OpenGL"
kwriteconfig5 --file kwinrc --group Compositing --key GLCore "true"
kwriteconfig5 --file kwinrc --group Compositing --key AnimationSpeed "3"

echo "  Configuring blur effect..."
kwriteconfig5 --file kwinrc --group Effect-blur --key BlurStrength "10"
kwriteconfig5 --file kwinrc --group Effect-blur --key NoiseStrength "0"
kwriteconfig5 --file kwinrc --group Plugins --key blurEnabled "true"

echo "  Setting panel configuration..."
# Hide top panel (will use Latte Dock instead)
kwriteconfig5 --file plasmashellrc --group PlasmaViews --group "Panel 2" --key panelVisibility "2"

echo ""
echo "▶ Configuring desktop behavior..."

# Disable desktop icons
kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group Containments --group 1 --group General --key positions ""
kwriteconfig5 --file plasmanotifyrc --group Notifications --key PopupPosition "BottomRight"

# Full-screen app launcher
kwriteconfig5 --file klaunchrc --group BusyCursorSettings --key Bouncing "false"
kwriteconfig5 --file klaunchrc --group FeedbackStyle --key BusyCursor "false"

# Smooth animations
kwriteconfig5 --file kwinrc --group Plugins --key slideEnabled "true"
kwriteconfig5 --file kwinrc --group Effect-slide --key Duration "200"

echo ""
echo "▶ Setting up global shortcuts..."

# Ctrl+Space for Cosmic AI
kwriteconfig5 --file kglobalshortcutsrc --group cosmic-ai.desktop --key _launch "Ctrl+Space,Ctrl+Space,Cosmic AI"

# Copy custom shortcuts
if [ -f "$SCRIPT_DIR/keybindings/cosmic-shortcuts.kksrc" ]; then
    cp "$SCRIPT_DIR/keybindings/cosmic-shortcuts.kksrc" "$HOME/.config/kglobalshortcutsrc.d/cosmic-shortcuts.kksrc"
fi

echo ""
echo "▶ Restarting Plasma shell..."

# Restart KWin for effects
qdbus org.kde.KWin /KWin reconfigure 2>/dev/null || true

# Restart Plasma shell
kquitapp5 plasmashell 2>/dev/null || true
sleep 1
kstart5 plasmashell &>/dev/null &

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      KDE Plasma Setup Complete!          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Run latte-dock-config.sh to set up the dock"
echo "  2. Run theme-setup.sh for Cosmic OS theme"
echo "  3. Log out and back in for all changes to take effect"
echo ""
