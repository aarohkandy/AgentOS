#!/bin/bash
# Cosmic OS - Latte Dock Configuration
# Sets up iOS-like bottom dock

set -e

echo "🚀 Cosmic OS - Latte Dock Configuration"
echo "========================================"

GREEN='\033[0;32m'
NC='\033[0m'
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

LATTE_CONFIG_DIR="$HOME/.config/latte"
mkdir -p "$LATTE_CONFIG_DIR"

# Create main layout
log_info "Creating Cosmic dock layout..."

cat > "$LATTE_CONFIG_DIR/Cosmic.layout.latte" << 'EOF'
[LayoutSettings]
activities=
backgroundStyle=0
color=blue
customBackground=
customTextColor=
icon=preferences-desktop-plasma
lastUsedActivity=
launchers=
popUpMargin=12
preferredForShortcutsTouched=false
showInMenu=true
textColor=
version=2

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
timerShow=100
viewType=0
visibility=2
wallpaperPlugin=org.kde.image

[Containments][1][Applets][2]
immutability=1
plugin=org.kde.latte.plasmoid

[Containments][1][Applets][2][Configuration]
isInLatteDock=true

[Containments][1][Applets][2][Configuration][General]
advanced=false
iconSize=56
isInternalViewSplitter=true
launchers59=applications:org.kde.dolphin.desktop,applications:firefox.desktop,applications:org.kde.konsole.desktop,applications:org.kde.kate.desktop,applications:systemsettings.desktop

[Containments][1][Applets][3]
immutability=1
plugin=org.kde.latte.separator

[Containments][1][Applets][4]
immutability=1
plugin=org.kde.plasma.icontasks

[Containments][1][Applets][4][Configuration][General]
launchers=

[Containments][1][Applets][5]
immutability=1
plugin=org.kde.latte.separator

[Containments][1][Applets][6]
immutability=1
plugin=org.kde.plasma.trash

[Containments][1][ConfigDialog]
DialogHeight=600
DialogWidth=586

[Containments][1][General]
advanced=false
alignment=10
alignmentUpgraded=true
appletOrder=2;3;4;5;6
backgroundOnlyOnMaximized=false
backgroundRadius=24
blurEnabled=true
editBackgroundOpacity=40
environment=1
iconSize=56
inConfigureAppletsMode=false
maxLength=90
panelSize=100
panelTransparency=20
plasmaBackgroundForPopups=true
shadowOpacity=80
shadowSize=45
shadowsUpgraded=true
showGlow=true
zoomLevel=8
EOF

# Create Latte config
log_info "Configuring Latte settings..."

cat > "$HOME/.config/lattedockrc" << 'EOF'
[PlasmaThemeExtended]
outlineWidth=1

[UniversalSettings]
badges3DStyle=false
canDisableBorders=true
contextMenuActionsAlwaysShown=_layouts,_preferences,_quit
currentLayout=Cosmic
downloadWindowSize=1200,800
inConfigureAppletsMode=false
isAvailableGeometryBroadcastedToPlasma=true
lastNonAssignedLayout=
launchers=
layoutsColumnWidths=64,0,0,0,0
layoutsWindowSize=1160,672
memoryUsage=0
metaPressAndHoldEnabled=false
mouseSensitivity=2
parabolicSpread=3
screenTrackerInterval=2500
showInfoWindow=true
singleModeLayoutName=Cosmic
thicknessMarginInfluence=50
EOF

# Kill and restart Latte Dock
log_info "Restarting Latte Dock..."
killall latte-dock 2>/dev/null || true
sleep 1
latte-dock --layout Cosmic &

echo ""
log_info "✅ Latte Dock configured with iOS-like layout!"
log_info "Features:"
log_info "  • Bottom dock with auto-hide"
log_info "  • 56px icons with zoom effect"
log_info "  • Blur and transparency"
log_info "  • Quick launchers + running apps + trash"
echo ""
