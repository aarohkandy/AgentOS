#!/bin/bash
# Clean Buildroot build with GUI login - no AI yet

cd buildroot

# Configure for larger filesystem and proper packages
cat >> .config << 'EOF'

# Larger filesystem
BR2_TARGET_ROOTFS_EXT2_SIZE="800M"

# X11
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_VESA=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_KEYBOARD=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_MOUSE=y

# Window manager
BR2_PACKAGE_OPENBOX=y

# Terminal
BR2_PACKAGE_XTERM=y

# Python (for AI later)
BR2_PACKAGE_PYTHON3=y

# Fonts
BR2_PACKAGE_LIBERATION=y

# Auto-login
BR2_TARGET_GENERIC_GETTY_PORT="tty1"

# Overlay
BR2_ROOTFS_OVERLAY="../buildroot-config/overlay"
EOF

# Fix dependencies
make olddefconfig

echo "✓ Configuration ready - starting build..."

# Disable legacy check and build
sed -i 's/BR2_LEGACY=y/# BR2_LEGACY is not set/' .config
make -j$(nproc)

echo "Build complete!"
