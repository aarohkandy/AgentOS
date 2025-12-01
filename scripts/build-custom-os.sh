#!/bin/bash
# Build Custom AI-OS using Buildroot

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILDROOT_DIR="$PROJECT_DIR/buildroot"
CONFIG_DIR="$PROJECT_DIR/buildroot-config"
OVERLAY_DIR="$CONFIG_DIR/overlay"

echo "========================================"
echo "Building Custom AI-OS with Buildroot"
echo "========================================"
echo ""

# Check if Buildroot exists
if [ ! -d "$BUILDROOT_DIR" ]; then
    echo "ERROR: Buildroot directory not found at $BUILDROOT_DIR"
    echo "Please run the setup script first."
    exit 1
fi

cd "$BUILDROOT_DIR"

# Use a minimal qemu x86_64 configuration as base
echo "Step 1: Loading base configuration..."
make qemu_x86_64_defconfig

# Now customize it
echo "Step 2: Applying customizations..."

# Enable Python packages
echo "  Enabling Python3..."
sed -i 's/# BR2_PACKAGE_PYTHON3 is not set/BR2_PACKAGE_PYTHON3=y/' .config
echo "BR2_PACKAGE_PYTHON_PIP=y" >> .config
echo "BR2_PACKAGE_PYTHON_SETUPTOOLS=y" >> .config

# Set overlay directory
echo "Step 3: Setting overlay directory..."
echo "BR2_ROOTFS_OVERLAY=\"$OVERLAY_DIR\"" >> .config

# Set hostname and system config
echo "BR2_TARGET_GENERIC_HOSTNAME=\"ai-os\"" >> .config
echo "BR2_TARGET_GENERIC_ISSUE=\"Welcome to AI-OS\"" >> .config

# Enable ISO generation
echo "  Enabling ISO output..."
echo "BR2_TARGET_ROOTFS_ISO9660=y" >> .config
echo "BR2_TARGET_SYSLINUX=y" >> .config
echo "BR2_TARGET_SYSLINUX_ISOLINUX=y" >> .config
echo "BR2_TARGET_ROOTFS_INITRAMFS=n" >> .config

# Reprocess the configuration to resolve dependencies
make olddefconfig

echo "Step 4: Building (this will take 30-60 minutes)..."
echo "Building started at: $(date)"
echo ""

# Build with all CPU cores
make -j$(nproc)

echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"
echo "Build finished at: $(date)"
echo ""
echo "Output files:"
ls -lh output/images/*.iso 2>/dev/null || echo "  (ISO not found - check build log)"
ls -lh output/images/rootfs.ext2 2>/dev/null || true
echo ""
echo "To test the OS:"
echo "  ./scripts/test-custom-os.sh"
echo ""
