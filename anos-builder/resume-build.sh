#!/bin/bash
# Resume ANOS build from squashfs creation step

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/anos-build"
CHROOT_DIR="$BUILD_DIR/chroot"
EXTRACT_DIR="$BUILD_DIR/extracted"

echo "Resuming ANOS build from squashfs creation..."

# Update ISO files
echo "Updating ISO files..."

# Regenerate manifest
sudo chmod +w "$EXTRACT_DIR/casper/filesystem.manifest" 2>/dev/null || true
sudo chroot "$CHROOT_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' > "$EXTRACT_DIR/casper/filesystem.manifest" 2>/dev/null || \
sudo chroot "$CHROOT_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' > "$EXTRACT_DIR/install/filesystem.manifest" 2>/dev/null || true

# Update filesystem size
size=$(sudo du -s "$CHROOT_DIR" | cut -f1)
echo "$size" | sudo tee "$EXTRACT_DIR/casper/filesystem.size" > /dev/null 2>/dev/null || \
echo "$size" | sudo tee "$EXTRACT_DIR/install/filesystem.size" > /dev/null 2>/dev/null || true

# Remove old squashfs
sudo rm -f "$EXTRACT_DIR/casper/filesystem.squashfs" "$EXTRACT_DIR/install/filesystem.squashfs" 2>/dev/null || true

# Create new squashfs with lzo (fastest compression)
echo "Creating squashfs with lzo compression (fastest - 2-5 minutes)..."
squashfs_path="$EXTRACT_DIR/casper/filesystem.squashfs"
[ ! -f "$squashfs_path" ] && squashfs_path="$EXTRACT_DIR/install/filesystem.squashfs"

# Use lzo for fastest compression with parallel processing
compress_opts="-comp lzo"
if mksquashfs -help 2>&1 | grep -q "processors"; then
    compress_opts="$compress_opts -processors $(nproc)"
fi

sudo mksquashfs "$CHROOT_DIR" "$squashfs_path" \
    $compress_opts -e boot/boot* -progress 2>&1 | \
while IFS= read -r line; do
    if [[ $line =~ ([0-9]+)% ]]; then
        percent="${BASH_REMATCH[1]}"
        echo -ne "\rCompressing: ${percent}%"
    fi
done

echo ""
echo "Squashfs created!"

# Calculate checksums
echo "Calculating checksums..."
cd "$EXTRACT_DIR"
find . -type f -print0 | xargs -0 md5sum | grep -v "\./md5sum.txt" > md5sum.txt 2>/dev/null || true
cd "$SCRIPT_DIR"

# Build ISO
echo "Building final ISO..."
ISO_OUTPUT="$SCRIPT_DIR/anos-$(date +%Y%m%d-%H%M%S).iso"

if command -v xorriso &> /dev/null; then
    sudo xorriso -as mkisofs \
        -r -V "ANOS" \
        -cache-inodes -J -l \
        -b isolinux/isolinux.bin \
        -c isolinux/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot \
        -isohybrid-gpt-basdat \
        -isohybrid-apm-hfsplus \
        -o "$ISO_OUTPUT" \
        "$EXTRACT_DIR"
else
    sudo genisoimage -r -V "ANOS" \
        -cache-inodes -J -l \
        -b isolinux/isolinux.bin \
        -c isolinux/boot.cat \
        -no-emul-boot -boot-load-size 4 -boot-info-table \
        -o "$ISO_OUTPUT" \
        "$EXTRACT_DIR"
fi

if command -v isohybrid &> /dev/null; then
    sudo isohybrid "$ISO_OUTPUT" 2>/dev/null || true
fi

size=$(du -h "$ISO_OUTPUT" | cut -f1)
echo ""
echo "✅ ANOS ISO created: $ISO_OUTPUT (${size})"


