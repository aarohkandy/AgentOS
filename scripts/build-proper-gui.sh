#!/bin/bash
# Properly configure Buildroot with full toolchain for GUI

cd buildroot

# Start fresh
make pc_x86_64_bios_defconfig

# Enable full toolchain capabilities
cat >> .config << 'EOF'

# Toolchain - enable everything needed
BR2_TOOLCHAIN_BUILDROOT_CXX=y
BR2_TOOLCHAIN_BUILDROOT_LOCALE=y
BR2_TOOLCHAIN_BUILDROOT_WCHAR=y
BR2_PTHREAD_DEBUG=y
BR2_TOOLCHAIN_BUILDROOT_USE_SSP=y

# Larger filesystem
BR2_TARGET_ROOTFS_EXT2_SIZE="1G"

# X11
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_VESA=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_FBDEV=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_KEYBOARD=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_MOUSE=y

# Window manager (Openbox - needs C++)
BR2_PACKAGE_OPENBOX=y

# Terminal
BR2_PACKAGE_XTERM=y

# File manager
BR2_PACKAGE_PCMANFM=y

# Panel/taskbar
BR2_PACKAGE_TINT2=y

# Python (for AI later)
BR2_PACKAGE_PYTHON3=y

# Fonts
BR2_PACKAGE_LIBERATION=y
BR2_PACKAGE_DEJAVU=y

# Overlay
BR2_ROOTFS_OVERLAY="../buildroot-config/overlay"
EOF

# Process config
make olddefconfig

echo "Configuration complete - building..."

# Fix legacy and build
sed -i 's/BR2_LEGACY=y/# BR2_LEGACY is not set/' .config
make -j$(nproc)

echo "Build complete!"
