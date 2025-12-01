#!/bin/bash
# Quick status check for Buildroot build

LOG_FILE="/home/aaroh/Downloads/AgentOS/buildroot-build.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "No build in progress (log file not found)"
    exit 0
fi

echo "========================================"
echo "Buildroot Build Status"
echo "========================================"
echo ""

# Check if build process is running
if pgrep -f "build-custom-os.sh" > /dev/null; then
    echo "Status: BUILDING ⚙️"
else
    echo "Status: COMPLETE or FAILED ✓/✗"
fi

echo ""
echo "Last 10 lines of build log:"
echo "----------------------------------------"
tail -10 "$LOG_FILE"
echo "----------------------------------------"
echo ""

# Count packages built
PACKAGES_BUILT=$(grep -c ">>> .* Installing" "$LOG_FILE" 2>/dev/null || echo "0")
echo "Packages built so far: $PACKAGES_BUILT"

# Show if ISO was created
if [ -f "/home/aaroh/Downloads/AgentOS/buildroot/output/images/rootfs.iso9660" ]; then
    ISO_SIZE=$(du -h /home/aaroh/Downloads/AgentOS/buildroot/output/images/rootfs.iso9660 | cut -f1)
    echo "✓ ISO created: $ISO_SIZE"
else
    echo "⏳ ISO not yet created (build still in progress)"
fi

echo ""
echo "To view full build log:"
echo "  tail -f $LOG_FILE"
echo ""
