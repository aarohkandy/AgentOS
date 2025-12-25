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

# Unmount virtual filesystems before creating squashfs
echo "Unmounting virtual filesystems..."
sudo umount "$CHROOT_DIR/proc" 2>/dev/null || true
sudo umount "$CHROOT_DIR/sys" 2>/dev/null || true
sudo umount "$CHROOT_DIR/dev/pts" 2>/dev/null || true
sudo umount "$CHROOT_DIR/dev" 2>/dev/null || true
sudo umount "$CHROOT_DIR/run" 2>/dev/null || true

# Create new squashfs with lzo (fastest compression)
echo "Creating squashfs with lzo compression (fastest - 1-3 minutes)..."
squashfs_path="$EXTRACT_DIR/casper/filesystem.squashfs"
[ ! -f "$squashfs_path" ] && squashfs_path="$EXTRACT_DIR/install/filesystem.squashfs"

# Use lzo compression (fastest available) with large blocks and parallel processing
# Exclude virtual filesystems and boot files
compress_opts="-comp lzo -b 1M"
if mksquashfs -help 2>&1 | grep -q "processors"; then
    compress_opts="$compress_opts -processors $(nproc)"
fi

echo "Starting mksquashfs (should show progress immediately)..."
echo "This may take 2-5 minutes for 8.2GB filesystem..."
echo ""
# Quote exclude patterns and exclude virtual filesystems
# Run mksquashfs and show all output (progress bar format: [====] X/Y   Z%)
sudo mksquashfs "$CHROOT_DIR" "$squashfs_path" \
    $compress_opts -e 'boot/boot*' -e 'proc' -e 'sys' -e 'dev' -e 'run' -e 'tmp' \
    -progress 2>&1 | \
while IFS= read -r line; do
    # Show progress bar lines (format: [====] X/Y   Z%)
    if [[ $line =~ \[.*\]\ ([0-9]+)/([0-9]+)\ +([0-9]+)% ]]; then
        current="${BASH_REMATCH[1]}"
        total="${BASH_REMATCH[2]}"
        percent="${BASH_REMATCH[3]}"
        echo -ne "\rCreating squashfs: ${percent}% (${current}/${total} files)"
    # Show other important status lines
    elif [[ $line =~ (Creating|Parallel|filesystem|block size) ]]; then
        echo "$line"
    # Filter out noise but show everything else
    elif [[ ! $line =~ (ignoring|Failed to read|Cannot stat) ]]; then
        # Only show non-empty lines
        if [[ -n "$line" ]]; then
            echo "$line"
        fi
    fi
done
echo ""

if [ ! -f "$squashfs_path" ]; then
    echo "ERROR: Squashfs creation failed!"
    exit 1
fi

echo ""
echo "Squashfs created!"

# Calculate checksums
echo "Calculating checksums..."
cd "$EXTRACT_DIR"
find . -type f -print0 | xargs -0 md5sum | grep -v "\./md5sum.txt" > md5sum.txt 2>/dev/null || true
cd "$SCRIPT_DIR"

# Build ISO
echo "Building final ISO..."
# Single file in agentOS root that gets overwritten
ISO_OUTPUT="$SCRIPT_DIR/../anos.iso"

# Detect bootloader type
echo "Detecting bootloader..."
boot_opts=""
if [ -f "$EXTRACT_DIR/isolinux/isolinux.bin" ]; then
    echo "Using isolinux bootloader"
    boot_opts="-b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table"
elif [ -f "$EXTRACT_DIR/boot/grub/efi.img" ]; then
    echo "Using EFI bootloader"
    boot_opts="-e boot/grub/efi.img -no-emul-boot"
elif [ -f "$EXTRACT_DIR/EFI/boot/bootx64.efi" ]; then
    echo "Using EFI bootloader (EFI/boot)"
    boot_opts="-e EFI/boot/bootx64.efi -no-emul-boot"
else
    echo "⚠️  No bootloader found, creating non-bootable ISO"
    boot_opts=""
fi

if command -v xorriso &> /dev/null; then
    xorriso_cmd="sudo xorriso -as mkisofs -r -V \"ANOS\" -cache-inodes -J -l"
    if [ -n "$boot_opts" ]; then
        xorriso_cmd="$xorriso_cmd $boot_opts"
        if [ -f "$EXTRACT_DIR/boot/grub/efi.img" ] || [ -f "$EXTRACT_DIR/EFI/boot/bootx64.efi" ]; then
            xorriso_cmd="$xorriso_cmd -isohybrid-gpt-basdat -isohybrid-apm-hfsplus"
        fi
    fi
    xorriso_cmd="$xorriso_cmd -o \"$ISO_OUTPUT\" \"$EXTRACT_DIR\""
    eval "$xorriso_cmd"
else
    geniso_cmd="sudo genisoimage -r -V \"ANOS\" -cache-inodes -J -l"
    if [ -n "$boot_opts" ]; then
        geniso_cmd="$geniso_cmd $boot_opts"
    fi
    geniso_cmd="$geniso_cmd -o \"$ISO_OUTPUT\" \"$EXTRACT_DIR\""
    eval "$geniso_cmd"
fi

if command -v isohybrid &> /dev/null; then
    sudo isohybrid "$ISO_OUTPUT" 2>/dev/null || true
fi

# Verify ISO was created
if [ ! -f "$ISO_OUTPUT" ]; then
    echo ""
    echo "❌ ERROR: ISO creation failed! No ISO file found."
    echo "Check the output above for errors."
    exit 1
fi

size=$(du -h "$ISO_OUTPUT" | cut -f1)
echo ""
echo "✅ ANOS ISO created: $ISO_OUTPUT (${size})"

# Auto-push to GitHub only if build succeeded
echo ""
echo "Pushing to GitHub..."
cd "$SCRIPT_DIR/.."
if git rev-parse --git-dir > /dev/null 2>&1; then
    git add -A
    git commit -m "ANOS build: $(date +%Y%m%d-%H%M%S)" 2>&1 | grep -v "nothing to commit" || true
    git push origin main 2>&1
    echo "✅ Pushed to GitHub"
else
    echo "⚠️  Not a git repository, skipping GitHub push"
fi


