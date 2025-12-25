#!/bin/bash
# Configure KDE Plasma for Cosmic OS in ANOS

# This will run on first boot, but we can pre-configure some settings

mkdir -p /etc/skel/.config

# Configure KDE for minimal, clean look
cat > /etc/skel/.config/kdeglobals << 'EOF'
[General]
ColorScheme=BreezeDark
Name=Breeze Dark
font=Inter,10,-1,5,50,0,0,0,0,0
fixed=JetBrains Mono,10,-1,5,50,0,0,0,0,0
menuFont=Inter,10,-1,5,50,0,0,0,0,0
smallestReadableFont=Inter,8,-1,5,50,0,0,0,0,0
toolBarFont=Inter,10,-1,5,50,0,0,0,0,0

[Icons]
Theme=Papirus-Dark

[KDE]
AnimationDurationFactor=0.5
SingleClick=false
EOF

# Configure KWin
mkdir -p /etc/skel/.config
cat > /etc/skel/.config/kwinrc << 'EOF'
[Compositing]
Backend=OpenGL
Enabled=true
GLCore=true
HiddenPreviews=5
OpenGLIsUnsafe=false
AnimationSpeed=3

[org.kde.kdecoration2]
BorderSize=None
BorderSizeAuto=false
ButtonsOnLeft=
ButtonsOnRight=IAX
CloseOnDoubleClickOnMenu=false

[Plugins]
blurEnabled=true
contrastEnabled=true
slideEnabled=true
fadeEnabled=true
scaleEnabled=true

[Effect-Blur]
BlurStrength=10
NoiseStrength=0
EOF

echo "KDE configuration prepared"




