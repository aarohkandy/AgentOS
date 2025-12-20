#!/bin/bash
# Cosmic OS Latte Dock Configuration
# Sets up an iOS-like bottom dock

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LATTE_CONFIG_DIR="$HOME/.config/latte"

echo "╔══════════════════════════════════════════╗"
echo "║    Cosmic OS Latte Dock Setup            ║"
echo "╚══════════════════════════════════════════╝"

# Check if Latte Dock is installed
if ! command -v latte-dock &> /dev/null; then
    echo "❌ Latte Dock not found. Installing..."
    
    if command -v apt &> /dev/null; then
        sudo apt install -y latte-dock
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm latte-dock
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y latte-dock
    else
        echo "Please install latte-dock manually and run this script again."
        exit 1
    fi
fi

echo ""
echo "▶ Creating Latte Dock configuration..."

mkdir -p "$LATTE_CONFIG_DIR/layouts"

# Kill existing Latte Dock
killall latte-dock 2>/dev/null || true
sleep 1

# Create Cosmic OS layout configuration
cat > "$LATTE_CONFIG_DIR/layouts/CosmicOS.layout.latte" << 'EOF'
[ActionPlugins][1]
MiddleButton;NoModifier=org.kde.latte.contextmenu
RightButton;NoModifier=org.kde.latte.contextmenu

[ActionPlugins][1][RightButton;NoModifier]
_add panel=true
_context menu=true
_layouts menu=true

[Containments][1]
activityId=
byPassWM=false
dockWindowBehavior=true
enableKWinEdges=true
formfactor=2
immutability=1
isPreferredForShortcuts=false
lastScreen=0
location=4
name=Cosmic Dock
onPrimary=true
plugin=org.kde.latte.containment
raiseOnActivityChange=false
raiseOnDesktopChange=false
timerHide=700
timerShow=100
visibility=2
wallpaper=

[Containments][1][Applets][2]
immutability=1
plugin=org.kde.latte.plasmoid

[Containments][1][Applets][2][Configuration]
PreloadWeight=100

[Containments][1][Applets][2][Configuration][General]
isInLatteDock=true
launchers59=applications:org.kde.dolphin.desktop,applications:firefox.desktop,applications:org.kde.konsole.desktop,applications:systemsettings.desktop

[Containments][1][ConfigDialog]
DialogHeight=600
DialogWidth=586

[Containments][1][General]
advanced=false
alignment=10
alignmentUpgraded=true
appletOrder=2
autoDecreaseIconSize=true
background=3
blurEnabled=true
configurationSticker=true
editBackgroundOpacity=70
hoverAction=4
iconSize=48
indicatorStyle=org.kde.latte.default
launchers=
lengthIntMargin=8
lengthExtMargin=0
maxIconSize=64
maxLength=90
minLength=90
mouseWheelActions=true
offset=0
parabolic=false
panelSize=100
panelTransparency=-1
plasmaBackgroundForPopups=false
proportionIconSize=4
screenEdgeMargin=8
shadowOpacity=60
shadowSize=35
shadowsUpgraded=true
showGlow=true
solidBackgroundForMaximized=false
splitterPosition=1
splitterPosition2=2
zoomLevel=16

[Containments][1][Latte]
configIsReady=true
version=2

[LayoutSettings]
activities=
backgroundStyle=0
color=blue
customBackground=
customTextColor=
disableBordersForMaximizedWindows=false
icon=
lastUsedActivity=
launchers=
popUpMargin=12
preferredForShortcutsTouched=false
showInMenu=true
textColor=
version=2
EOF

# Create global Latte configuration
cat > "$LATTE_CONFIG_DIR/lattedockrc" << 'EOF'
[PlasmaCalendarIntegration]
enabledCalendarPlugins=holidaysEvents,

[UniversalSettings]
badges3DStyle=true
canDisableBorders=true
contextMenuActionsAlwaysShown=_layouts,_separator1,_quit
currentLayout=CosmicOS
downloadWindowSize=800,550
isAvailableGeometryBroadcastedToPlasma=true
launchers=
memoryUsage=1
metaPressAndHoldEnabled=true
mouseSensitivity=1
parabolicSpread=2
parabolicZoom=30
screenTrackerInterval=2500
showInfoWindow=true
singleModeLayoutName=CosmicOS
version=2
EOF

echo "  ✓ Created CosmicOS dock layout"

echo ""
echo "▶ Starting Latte Dock..."

# Start Latte Dock with Cosmic layout
latte-dock --layout CosmicOS &>/dev/null &
disown

sleep 2

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    Latte Dock Setup Complete!            ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "The dock should now be visible at the bottom of your screen."
echo ""
echo "Features:"
echo "  • Auto-hide enabled"
echo "  • 48px icons (up to 64px on hover)"
echo "  • Blur background"
echo "  • Centered alignment"
echo "  • Glow effect on hover"
echo ""
echo "To customize: Right-click the dock → Configure Latte"
echo ""
