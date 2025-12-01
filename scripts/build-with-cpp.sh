#!/bin/bash
# Build Buildroot WITH C++ support first

cd buildroot

# Clean completely
make clean
rm -rf output

# Start with defconfig
make pc_x86_64_bios_defconfig

# Enable C++ FIRST, before anything else
sed -i 's/# BR2_TOOLCHAIN_BUILDROOT_CXX is not set/BR2_TOOLCHAIN_BUILDROOT_CXX=y/' .config

# Apply our packages after toolchain config
cat >> .config << 'EOF'

# Ensure wchar and locale
BR2_TOOLCHAIN_BUILDROOT_WCHAR=y
BR2_TOOLCHAIN_BUILDROOT_LOCALE=y

# Filesystem size
BR2_TARGET_ROOTFS_EXT2_SIZE="1G"

# X11
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_VESA=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_KEYBOARD=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_MOUSE=y

# Openbox (needs C++)
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

# olddefconfig will enable dependencies
make olddefconfig

# Check if C++ is really enabled
if grep -q "BR2_TOOLCHAIN_BUILDROOT_CXX=y" .config; then
    echo "✓ C++ enabled"
else
    echo "✗ C++ NOT enabled - forcing it"
    sed -i 's/# BR2_TOOLCHAIN_BUILDROOT_CXX is not set/BR2_TOOLCHAIN_BUILDROOT_CXX=y/' .config
    make olddefconfig
fi

# Build
sed -i 's/BR2_LEGACY=y/# BR2_LEGACY is not set/' .config
make -j$(nproc)

echo "Build complete!"
