#!/bin/bash
# Quick script to check ISO build progress

echo "=== ISO Build Status ==="
echo ""

# Check if build process is running
if pgrep -f "lb build" > /dev/null; then
    echo "✓ Build process is running"
    echo ""
    echo "Recent build log (last 10 lines):"
    tail -10 /tmp/lb-build-final.log 2>/dev/null || echo "  (log file not found yet)"
else
    echo "✗ Build process is not running"
    echo ""
    echo "Last build log (last 20 lines):"
    tail -20 /tmp/lb-build-final.log 2>/dev/null || echo "  (log file not found)"
fi

echo ""
echo "=== ISO Files ==="
ls -lh /home/aaroh/Downloads/AgentOS/iso-build/*.iso 2>/dev/null || echo "  No ISO files found yet"

