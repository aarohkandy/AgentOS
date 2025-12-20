#!/bin/bash
# Cosmic OS - KDE Plasma Setup Script
# Configures KDE Plasma for iOS-like experience

set -e

echo "🚀 Cosmic OS - KDE Plasma Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Backup existing configs
backup_configs() {
    log_info "Backing up existing KDE configs..."
    BACKUP_DIR="$HOME/.config/cosmic-os-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    for config in kdeglobals kwinrc plasmashellrc lattedockrc; do
        if [ -f "$HOME/.config/$config" ]; then
            cp "$HOME/.config/$config" "$BACKUP_DIR/"
            log_info "Backed up $config"
        fi
    done
    
    echo "$BACKUP_DIR" > "$HOME/.config/cosmic-os-last-backup"
    log_info "Backup complete: $BACKUP_DIR"
}

# Install required packages
install_dependencies() {
    log_info "Installing dependencies..."
    
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y \
            latte-dock \
            kvantum \
            qt5-style-kvantum \
            papirus-icon-theme \
            fonts-inter \
            xdotool \
            wmctrl \
            python3-pyqt6 \
            scrot
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm \
            latte-dock \
            kvantum \
            papirus-icon-theme \
            inter-font \
            xdotool \
            wmctrl \
            python-pyqt6 \
            scrot
    else
        log_warn "Unknown package manager. Please install dependencies manually."
    fi
}

# Configure Latte Dock
setup_latte_dock() {
    log_info "Configuring Latte Dock..."
    
    mkdir -p "$HOME/.config/latte"
    
    cat > "$HOME/.config/latte/cosmic.layout.latte" << 'EOF'
[ActionPlugins][1]
RightButton;NoModifier=org.kde.latte.contextmenu

[Containments][1]
activityId=
byPassWM=false
dockWindowBehavior=true
enableKWinEdges=true
formfactor=2
immutability=1
isPreferredForShortcuts=false
location=4
name=Cosmic Dock
onPrimary=true
plugin=org.kde.latte.containment
raiseOnActivityChange=false
raiseOnDesktopChange=false
timerHide=700
timerShow=200
viewType=0
visibility=2

[Containments][1][Applets][2]
immutability=1
plugin=org.kde.latte.plasmoid

[Containments][1][Applets][2][Configuration]
isInLatteDock=true

[Containments][1][Applets][2][Configuration][General]
isInternalViewSplitter=true
launchers59=

[Containments][1][General]
advanced=false
alignment=10
alignmentUpgraded=true
appletOrder=2
iconSize=56
maxLength=85
panelSize=100
panelTransparency=-1
shadows=All
shadowsUpgraded=true
EOF
    
    # Set Latte to autostart
    mkdir -p "$HOME/.config/autostart"
    cat > "$HOME/.config/autostart/org.kde.latte-dock.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Latte Dock
Exec=latte-dock
X-KDE-autostart-phase=1
OnlyShowIn=KDE;
EOF
    
    log_info "Latte Dock configured"
}

# Configure KDE Global Settings
setup_kdeglobals() {
    log_info "Configuring KDE global settings..."
    
    kwriteconfig5 --file kdeglobals --group General --key ColorScheme "BreezeDark"
    kwriteconfig5 --file kdeglobals --group General --key Name "Breeze Dark"
    kwriteconfig5 --file kdeglobals --group General --key font "Inter,10,-1,5,50,0,0,0,0,0"
    kwriteconfig5 --file kdeglobals --group General --key fixed "JetBrains Mono,10,-1,5,50,0,0,0,0,0"
    kwriteconfig5 --file kdeglobals --group General --key menuFont "Inter,10,-1,5,50,0,0,0,0,0"
    kwriteconfig5 --file kdeglobals --group General --key smallestReadableFont "Inter,8,-1,5,50,0,0,0,0,0"
    kwriteconfig5 --file kdeglobals --group General --key toolBarFont "Inter,10,-1,5,50,0,0,0,0,0"
    
    kwriteconfig5 --file kdeglobals --group Icons --key Theme "Papirus-Dark"
    
    kwriteconfig5 --file kdeglobals --group KDE --key AnimationDurationFactor "0.5"
    kwriteconfig5 --file kdeglobals --group KDE --key SingleClick "false"
    
    log_info "KDE globals configured"
}

# Configure KWin (Window Manager)
setup_kwin() {
    log_info "Configuring KWin..."
    
    # Enable compositing with good settings
    kwriteconfig5 --file kwinrc --group Compositing --key Backend "OpenGL"
    kwriteconfig5 --file kwinrc --group Compositing --key Enabled "true"
    kwriteconfig5 --file kwinrc --group Compositing --key GLCore "true"
    kwriteconfig5 --file kwinrc --group Compositing --key HiddenPreviews "5"
    kwriteconfig5 --file kwinrc --group Compositing --key OpenGLIsUnsafe "false"
    kwriteconfig5 --file kwinrc --group Compositing --key AnimationSpeed "3"
    
    # Window decorations - minimal
    kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key BorderSize "None"
    kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key BorderSizeAuto "false"
    kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft ""
    kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight "IAX"
    kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key CloseOnDoubleClickOnMenu "false"
    
    # Effects
    kwriteconfig5 --file kwinrc --group Plugins --key blurEnabled "true"
    kwriteconfig5 --file kwinrc --group Plugins --key contrastEnabled "true"
    kwriteconfig5 --file kwinrc --group Plugins --key slideEnabled "true"
    kwriteconfig5 --file kwinrc --group Plugins --key fadeEnabled "true"
    kwriteconfig5 --file kwinrc --group Plugins --key scaleEnabled "true"
    
    # Blur settings
    kwriteconfig5 --file kwinrc --group Effect-Blur --key BlurStrength "10"
    kwriteconfig5 --file kwinrc --group Effect-Blur --key NoiseStrength "0"
    
    log_info "KWin configured"
}

# Configure Plasma Shell
setup_plasma_shell() {
    log_info "Configuring Plasma Shell..."
    
    # Hide default panel (we use Latte Dock instead)
    kwriteconfig5 --file plasmashellrc --group PlasmaViews --group "Panel 2" --key panelVisibility "2"
    
    # Disable desktop icons
    kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group Containments --group 1 --group General --key showToolbox "false"
    
    log_info "Plasma Shell configured"
}

# Set wallpaper
setup_wallpaper() {
    log_info "Setting up wallpaper..."
    
    WALLPAPER_DIR="$HOME/.local/share/wallpapers/cosmic-os"
    mkdir -p "$WALLPAPER_DIR"
    
    # Create a simple gradient wallpaper placeholder
    # In production, download actual wallpaper
    if command -v convert &> /dev/null; then
        convert -size 1920x1080 gradient:'#1a1a2e-#16213e' "$WALLPAPER_DIR/default.png"
        log_info "Created gradient wallpaper"
    else
        log_warn "ImageMagick not found. Skipping wallpaper generation."
    fi
}

# Apply changes
apply_changes() {
    log_info "Applying changes..."
    
    # Reload KWin
    if pgrep -x "kwin_x11" > /dev/null; then
        kwin_x11 --replace &
    elif pgrep -x "kwin_wayland" > /dev/null; then
        log_warn "Wayland detected. Some features may not work optimally."
    fi
    
    # Restart Plasma Shell
    kquitapp5 plasmashell 2>/dev/null || true
    sleep 1
    kstart5 plasmashell &
    
    log_info "Changes applied"
}

# Main
main() {
    echo ""
    log_info "Starting Cosmic OS KDE setup..."
    echo ""
    
    backup_configs
    
    read -p "Install dependencies? (recommended) [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        install_dependencies
    fi
    
    setup_latte_dock
    setup_kdeglobals
    setup_kwin
    setup_plasma_shell
    setup_wallpaper
    
    read -p "Apply changes now? (will restart Plasma) [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        apply_changes
    fi
    
    echo ""
    log_info "✅ Cosmic OS KDE setup complete!"
    log_info "Run the Latte Dock setup script next: ./latte-dock-config.sh"
    echo ""
}

main "$@"
