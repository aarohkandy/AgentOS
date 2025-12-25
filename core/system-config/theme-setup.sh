#!/bin/bash
# Cosmic OS - Theme Setup Script
# Installs and configures custom theme

set -e

echo "🎨 Cosmic OS - Theme Setup"
echo "=========================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Theme directories
PLASMA_LOOK_DIR="$HOME/.local/share/plasma/look-and-feel"
COLOR_SCHEME_DIR="$HOME/.local/share/color-schemes"
KVANTUM_DIR="$HOME/.config/Kvantum"
ICON_DIR="$HOME/.local/share/icons"

mkdir -p "$PLASMA_LOOK_DIR" "$COLOR_SCHEME_DIR" "$KVANTUM_DIR" "$ICON_DIR"

# Create Cosmic Dark color scheme
log_info "Creating Cosmic Dark color scheme..."

cat > "$COLOR_SCHEME_DIR/CosmicDark.colors" << 'EOF'
[ColorEffects:Disabled]
Color=56,56,56
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color=112,111,110
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate=45,45,45
BackgroundNormal=60,60,60
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=160,160,160
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=246,116,0
ForegroundNormal=224,224,224
ForegroundPositive=39,174,96
ForegroundVisited=155,89,182

[Colors:Complementary]
BackgroundAlternate=45,45,45
BackgroundNormal=30,30,30
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=160,160,160
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=246,116,0
ForegroundNormal=224,224,224
ForegroundPositive=39,174,96
ForegroundVisited=155,89,182

[Colors:Header]
BackgroundAlternate=37,37,37
BackgroundNormal=37,37,37
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=160,160,160
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=246,116,0
ForegroundNormal=224,224,224
ForegroundPositive=39,174,96
ForegroundVisited=155,89,182

[Colors:Selection]
BackgroundAlternate=0,100,180
BackgroundNormal=0,120,212
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=255,255,255
ForegroundInactive=224,224,224
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=246,116,0
ForegroundNormal=255,255,255
ForegroundPositive=39,174,96
ForegroundVisited=155,89,182

[Colors:Tooltip]
BackgroundAlternate=45,45,45
BackgroundNormal=45,45,45
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=160,160,160
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=246,116,0
ForegroundNormal=224,224,224
ForegroundPositive=39,174,96
ForegroundVisited=155,89,182

[Colors:View]
BackgroundAlternate=37,37,37
BackgroundNormal=30,30,30
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=160,160,160
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=246,116,0
ForegroundNormal=224,224,224
ForegroundPositive=39,174,96
ForegroundVisited=155,89,182

[Colors:Window]
BackgroundAlternate=37,37,37
BackgroundNormal=30,30,30
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=160,160,160
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=246,116,0
ForegroundNormal=224,224,224
ForegroundPositive=39,174,96
ForegroundVisited=155,89,182

[General]
ColorScheme=CosmicDark
Name=Cosmic Dark
shadeSortColumn=true

[KDE]
contrast=4

[WM]
activeBackground=37,37,37
activeBlend=224,224,224
activeForeground=224,224,224
inactiveBackground=30,30,30
inactiveBlend=160,160,160
inactiveForeground=160,160,160
EOF

# Apply the color scheme
log_info "Applying Cosmic Dark color scheme..."
kwriteconfig5 --file kdeglobals --group General --key ColorScheme "CosmicDark"

# Install Papirus icons if not present
if [ ! -d "$HOME/.local/share/icons/Papirus-Dark" ]; then
    log_info "Installing Papirus icons..."
    if command -v apt &> /dev/null; then
        sudo apt install -y papirus-icon-theme
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm papirus-icon-theme
    else
        log_warn "Please install Papirus icon theme manually"
    fi
fi

# Configure Kvantum (Qt theme engine)
log_info "Configuring Kvantum..."

cat > "$KVANTUM_DIR/kvantum.kvconfig" << 'EOF'
[General]
theme=KvFlatDark
EOF

# Install fonts
log_info "Installing fonts..."
FONT_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONT_DIR"

# Download Inter font if not present
if ! fc-list | grep -qi "inter"; then
    log_info "Downloading Inter font..."
    cd /tmp
    wget -q "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip" -O inter.zip || log_warn "Could not download Inter font"
    if [ -f inter.zip ]; then
        unzip -q -o inter.zip -d inter_font
        cp inter_font/Inter-*/*.ttf "$FONT_DIR/" 2>/dev/null || true
        rm -rf inter.zip inter_font
        fc-cache -f
        log_info "Inter font installed"
    fi
fi

# Apply font settings
log_info "Applying font settings..."
kwriteconfig5 --file kdeglobals --group General --key font "Inter,10,-1,5,50,0,0,0,0,0"
kwriteconfig5 --file kdeglobals --group General --key fixed "JetBrains Mono,10,-1,5,50,0,0,0,0,0"
kwriteconfig5 --file kdeglobals --group General --key menuFont "Inter,10,-1,5,50,0,0,0,0,0"
kwriteconfig5 --file kdeglobals --group General --key smallestReadableFont "Inter,8,-1,5,50,0,0,0,0,0"
kwriteconfig5 --file kdeglobals --group General --key toolBarFont "Inter,10,-1,5,50,0,0,0,0,0"

# Configure window decorations
log_info "Configuring window decorations..."
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key theme "Breeze"
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key BorderSize "None"

echo ""
log_info "✅ Theme setup complete!"
log_info "Theme components installed:"
log_info "  • Cosmic Dark color scheme"
log_info "  • Papirus-Dark icons"
log_info "  • Inter font family"
log_info "  • Minimal window decorations"
echo ""
log_info "Restart Plasma to apply all changes: kquitapp5 plasmashell && kstart5 plasmashell"
