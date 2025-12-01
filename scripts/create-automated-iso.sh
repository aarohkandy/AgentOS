#!/bin/bash
# Create a Debian ISO with automated installation preseed

set -e

ISO_IN="/home/aaroh/Downloads/AgentOS/debian-netinst.iso"
ISO_OUT="/home/aaroh/Downloads/AgentOS/debian-auto.iso"
PRESEED="/home/aaroh/Downloads/AgentOS/iso-build/preseed.cfg"
WORK_DIR="/tmp/iso-custom"

echo "=== Creating Automated Installation ISO ==="
echo ""

# Check if required tools are installed
if ! command -v xorriso &> /dev/null; then
    echo "Installing xorriso..."
    sudo apt install -y xorriso
fi

# Clean up old work
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# Extract ISO
echo "1. Extracting ISO..."
xorriso -osirrox on -indev "$ISO_IN" -extract / "$WORK_DIR/"

# Add preseed file
echo "2. Adding preseed configuration..."
mkdir -p "$WORK_DIR/preseed"
cp "$PRESEED" "$WORK_DIR/preseed/custom.cfg"

# Modify isolinux to use preseed
echo "3. Configuring boot to use preseed..."
if [ -f "$WORK_DIR/isolinux/isolinux.cfg" ]; then
    # Add preseed to kernel command line
    sed -i 's/append vga=normal initrd=\/install.amd\/initrd.gz/append vga=normal initrd=\/install.amd\/initrd.gz auto=true priority=critical preseed\/file=\/cdrom\/preseed\/custom.cfg/' "$WORK_DIR/isolinux/isolinux.cfg"
fi

# Build new ISO
echo "4. Building automated ISO..."
xorriso -as mkisofs \
    -r -J -joliet-long \
    -V "DEBIAN AUTO" \
    -o "$ISO_OUT" \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -b isolinux/isolinux.bin \
    -c isolinux/boot.cat \
    -boot-load-size 4 \
    -boot-info-table \
    -no-emul-boot \
    "$WORK_DIR"

echo ""
echo "✓ Automated ISO created: $ISO_OUT"
echo ""
echo "This ISO will install Debian automatically with:"
echo "  - User: ai / Password: ai-os-dev"
echo "  - Root password: ai-os-dev"
echo "  - All dev tools pre-installed"
echo "  - XFCE desktop environment"


