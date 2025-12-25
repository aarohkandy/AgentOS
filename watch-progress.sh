#!/bin/bash
# Quick script to watch ISO build progress

BUILD_DIR="/home/a_a_k/Downloads/agentOS/iso-build"
BUILD_LOG="$BUILD_DIR/build.log"

echo "🌌 Cosmic OS ISO Build Progress Monitor"
echo "========================================"
echo ""

# Check if build is running
if pgrep -f "build-iso.sh" > /dev/null; then
    echo "✅ Build is RUNNING"
else
    echo "⏸️  Build is NOT running (may have completed or failed)"
fi

echo ""
echo "📊 Current Status:"
echo "------------------"

# Show last few log lines
if [ -f "$BUILD_LOG" ]; then
    echo ""
    echo "Recent activity:"
    tail -5 "$BUILD_LOG" | sed 's/^/  /'
fi

echo ""
echo "📁 Files:"
echo "-------"

# Check ISO download
if [ -f "$BUILD_DIR/kubuntu-24.04.3-desktop-amd64.iso" ]; then
    size=$(du -h "$BUILD_DIR/kubuntu-24.04.3-desktop-amd64.iso" | cut -f1)
    echo "  ✅ ISO downloaded: $size"
else
    echo "  ⏳ ISO not downloaded yet"
fi

# Check extraction
if [ -d "$BUILD_DIR/extracted" ] && [ "$(ls -A $BUILD_DIR/extracted 2>/dev/null)" ]; then
    echo "  ✅ ISO extracted"
else
    echo "  ⏳ ISO not extracted yet"
fi

# Check chroot
if [ -d "$BUILD_DIR/chroot" ] && [ -d "$BUILD_DIR/chroot/usr" ]; then
    chroot_size=$(du -sh "$BUILD_DIR/chroot" 2>/dev/null | cut -f1)
    echo "  ✅ Chroot filesystem: $chroot_size"
    
    # Check if Cosmic OS is installed
    if [ -d "$BUILD_DIR/chroot/opt/cosmic-os" ]; then
        echo "  ✅ Cosmic OS files copied"
        if [ -d "$BUILD_DIR/chroot/opt/cosmic-os/venv" ]; then
            echo "  ✅ Python venv created"
        else
            echo "  ⏳ Installing Python packages..."
        fi
    else
        echo "  ⏳ Copying Cosmic OS files..."
    fi
else
    echo "  ⏳ Chroot not set up yet"
fi

# Check final ISO
if ls "$BUILD_DIR/../cosmic-os-"*.iso 2>/dev/null | grep -q .; then
    iso_file=$(ls -t "$BUILD_DIR/../cosmic-os-"*.iso 2>/dev/null | head -1)
    iso_size=$(du -h "$iso_file" 2>/dev/null | cut -f1)
    echo "  ✅ Final ISO: $(basename $iso_file) ($iso_size)"
else
    echo "  ⏳ Final ISO not created yet"
fi

echo ""
echo "💡 Tips:"
echo "  • Watch live: tail -f $BUILD_LOG"
echo "  • Check processes: ps aux | grep build-iso"
echo "  • Run this script again: ./watch-progress.sh"
echo ""






