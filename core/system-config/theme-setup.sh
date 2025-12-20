#!/bin/bash
# Cosmic OS Theme Setup
# Applies Cosmic OS custom theme elements

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES_DIR="$HOME/.local/share/plasma/desktoptheme"
COLOR_SCHEMES_DIR="$HOME/.local/share/color-schemes"
WALLPAPERS_DIR="$HOME/.local/share/wallpapers"

echo "╔══════════════════════════════════════════╗"
echo "║      Cosmic OS Theme Setup               ║"
echo "╚══════════════════════════════════════════╝"

# Create directories
mkdir -p "$THEMES_DIR"
mkdir -p "$COLOR_SCHEMES_DIR"
mkdir -p "$WALLPAPERS_DIR/CosmicOS/contents/images"

echo ""
echo "▶ Installing Cosmic OS color scheme..."

# Create Cosmic Dark color scheme
cat > "$COLOR_SCHEMES_DIR/CosmicDark.colors" << 'EOF'
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
BackgroundAlternate=59,64,69
BackgroundNormal=49,54,59
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=189,195,199
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=224,224,224
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[Colors:Complementary]
BackgroundAlternate=30,30,30
BackgroundNormal=30,30,30
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=189,195,199
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=224,224,224
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[Colors:Selection]
BackgroundAlternate=0,102,184
BackgroundNormal=0,120,212
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=252,252,252
ForegroundInactive=189,195,199
ForegroundLink=253,188,75
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=252,252,252
ForegroundPositive=76,175,80
ForegroundVisited=189,195,199

[Colors:Tooltip]
BackgroundAlternate=30,30,30
BackgroundNormal=45,45,45
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=189,195,199
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=224,224,224
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[Colors:View]
BackgroundAlternate=30,30,30
BackgroundNormal=37,37,37
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=189,195,199
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=224,224,224
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[Colors:Window]
BackgroundAlternate=45,45,45
BackgroundNormal=30,30,30
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=189,195,199
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=224,224,224
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[General]
ColorScheme=CosmicDark
Name=Cosmic Dark
shadeSortColumn=true

[KDE]
contrast=4

[WM]
activeBackground=30,30,30
activeBlend=252,252,252
activeForeground=224,224,224
inactiveBackground=45,45,45
inactiveBlend=127,140,141
inactiveForeground=189,195,199
EOF

echo "  ✓ Created Cosmic Dark color scheme"

echo ""
echo "▶ Creating Cosmic Light color scheme..."

cat > "$COLOR_SCHEMES_DIR/CosmicLight.colors" << 'EOF'
[ColorEffects:Disabled]
Color=112,111,110
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[Colors:Button]
BackgroundAlternate=230,230,230
BackgroundNormal=245,245,245
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=100,100,100
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=30,30,30
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[Colors:Selection]
BackgroundAlternate=0,102,184
BackgroundNormal=0,120,212
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=252,252,252
ForegroundInactive=200,200,200
ForegroundLink=253,188,75
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=252,252,252
ForegroundPositive=76,175,80
ForegroundVisited=100,100,100

[Colors:View]
BackgroundAlternate=245,245,245
BackgroundNormal=252,252,252
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=100,100,100
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=30,30,30
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[Colors:Window]
BackgroundAlternate=240,240,240
BackgroundNormal=245,245,245
DecorationFocus=0,120,212
DecorationHover=0,120,212
ForegroundActive=0,120,212
ForegroundInactive=100,100,100
ForegroundLink=0,120,212
ForegroundNegative=218,68,83
ForegroundNeutral=255,160,0
ForegroundNormal=30,30,30
ForegroundPositive=76,175,80
ForegroundVisited=127,140,141

[General]
ColorScheme=CosmicLight
Name=Cosmic Light
shadeSortColumn=true

[WM]
activeBackground=245,245,245
activeBlend=30,30,30
activeForeground=30,30,30
inactiveBackground=230,230,230
inactiveBlend=100,100,100
inactiveForeground=100,100,100
EOF

echo "  ✓ Created Cosmic Light color scheme"

echo ""
echo "▶ Creating wallpaper metadata..."

cat > "$WALLPAPERS_DIR/CosmicOS/metadata.desktop" << 'EOF'
[Desktop Entry]
Name=Cosmic OS
X-KDE-PluginInfo-Author=Cosmic OS Team
X-KDE-PluginInfo-Email=hello@cosmicos.dev
X-KDE-PluginInfo-License=CC-BY-SA
X-KDE-PluginInfo-Name=cosmicos
X-KDE-PluginInfo-Version=1.0
EOF

echo "  ✓ Created wallpaper metadata"

echo ""
echo "▶ Applying color scheme..."

# Apply Cosmic Dark by default
kwriteconfig5 --file kdeglobals --group General --key ColorScheme "CosmicDark"

# Apply window decoration settings for iOS-like appearance
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key BorderSize "None"
kwriteconfig5 --file kwinrc --group org.kde.kdecoration2 --key BorderSizeAuto "false"

# Enable window shadows
kwriteconfig5 --file kwinrc --group Effect-kwin4_effect_shapecorners --key shadowEnabled "true"

echo ""
echo "▶ Setting desktop effects..."

# Enable overview effect (like macOS Mission Control)
kwriteconfig5 --file kwinrc --group Plugins --key overviewEnabled "true"
kwriteconfig5 --file kwinrc --group Plugins --key desktopgridEnabled "true"

# Set corner rounding if available
kwriteconfig5 --file kwinrc --group Plugins --key kwin4_effect_shapecornersEnabled "true" 2>/dev/null || true

echo ""
echo "▶ Refreshing Plasma..."

qdbus org.kde.KWin /KWin reconfigure 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      Theme Setup Complete!               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Installed themes:"
echo "  • Cosmic Dark (applied)"
echo "  • Cosmic Light"
echo ""
echo "To switch themes:"
echo "  System Settings → Appearance → Colors"
echo ""
echo "For best experience, also install:"
echo "  • Lightly or Klassy window decorations"
echo "  • Papirus icon theme"
echo ""
