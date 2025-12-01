#!/bin/bash
# Fresh Buildroot X11 + GUI setup - Latest version

cd buildroot

# Enable X11 and desktop - minimal set
cat >> .config << 'EOF'

# X11
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_VESA=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_KEYBOARD=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_MOUSE=y

# Window manager (lightweight)
BR2_PACKAGE_OPENBOX=y

# Terminal
BR2_PACKAGE_XTERM=y

# Python
BR2_PACKAGE_PYTHON3=y

# Fonts
BR2_PACKAGE_LIBERATION=y

# Overlay
BR2_ROOTFS_OVERLAY="../buildroot-config/overlay"
EOF

make olddefconfig

echo "✓ Config ready"
