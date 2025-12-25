#!/bin/bash
# Watch ANOS build progress

BUILD_LOG="/home/a_a_k/Downloads/agentOS/anos-builder/anos-build/build.log"
CHROOT_DIR="/home/a_a_k/Downloads/agentOS/anos-builder/anos-build/chroot"

echo "🔨 ANOS Build Monitor"
echo "===================="
echo ""

if [ ! -f "$BUILD_LOG" ]; then
    echo "❌ Build not started yet"
    exit 1
fi

echo "📊 Current Status:"
echo "------------------"
tail -5 "$BUILD_LOG" | sed 's/^/  /'

echo ""
echo "📁 Build Progress:"
echo "------------------"

# Check chroot size
if [ -d "$CHROOT_DIR" ]; then
    chroot_size=$(du -sh "$CHROOT_DIR" 2>/dev/null | cut -f1)
    echo "  Chroot size: $chroot_size"
    
    # Check if Cosmic OS is installed
    if [ -d "$CHROOT_DIR/opt/cosmic-os" ]; then
        echo "  ✅ Cosmic OS files copied"
        if [ -d "$CHROOT_DIR/opt/cosmic-os/venv" ]; then
            echo "  ✅ Python venv created"
        else
            echo "  ⏳ Installing Python packages..."
        fi
    else
        echo "  ⏳ Installing system packages..."
    fi
else
    echo "  ⏳ Extracting filesystem..."
fi

# Check if build is still running
if pgrep -f "build-anos-iso.sh" > /dev/null; then
    echo ""
    echo "✅ Build is RUNNING"
    echo ""
    echo "💡 Watch live: tail -f $BUILD_LOG"
else
    echo ""
    if ls /home/a_a_k/Downloads/agentOS/anos-builder/anos-*.iso 2>/dev/null | grep -q .; then
        iso_file=$(ls -t /home/a_a_k/Downloads/agentOS/anos-builder/anos-*.iso 2>/dev/null | head -1)
        iso_size=$(du -h "$iso_file" 2>/dev/null | cut -f1)
        echo "🎉 BUILD COMPLETE!"
        echo "   ISO: $(basename $iso_file) ($iso_size)"
    else
        echo "⏸️  Build stopped (may have completed or failed)"
        echo "   Check: $BUILD_LOG"
    fi
fi


