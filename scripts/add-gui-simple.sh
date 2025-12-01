#!/bin/bash
# Simple GUI Login for Buildroot - Clean approach

cd buildroot

# Add essential packages only
cat >> .config << 'EOF'
# X11 server
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y

# Basic drivers
BR2_PACKAGE_XDRIVER_XF86_VIDEO_VESA=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_MOUSE=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_KEYBOARD=y

# Window manager
BR2_PACKAGE_OPENBOX=y

# Display manager (auto-login)
BR2_PACKAGE_NODM=y

# Terminal
BR2_PACKAGE_XTERM=y

# Fonts
BR2_PACKAGE_LIBERATION=y

# Python (you need this)
BR2_PACKAGE_PYTHON3=y

# Enable ISO
BR2_TARGET_ROOTFS_ISO9660=y
BR2_TARGET_SYSLINUX=y
BR2_TARGET_SYSLINUX_ISOLINUX=y
EOF

# Fix dependencies
make olddefconfig

echo "Config updated! Ready to build."
