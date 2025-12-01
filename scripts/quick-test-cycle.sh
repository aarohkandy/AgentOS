#!/bin/bash
# Complete test cycle: local tests + VM reset

set -e

echo "=== Complete Test Cycle ==="
echo ""

# 1. Run local tests (fast)
echo "1. Running local tests..."
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest tests/ -v --tb=short

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Local tests failed - fix these first!"
    exit 1
fi

echo ""
echo "✓ Local tests passed"

# 2. Reset VM if snapshot exists
VM_NAME="AgenticOS"
SNAPSHOT_NAME="Clean Base"

if VBoxManage snapshot "$VM_NAME" list 2>/dev/null | grep -q "$SNAPSHOT_NAME"; then
    echo ""
    echo "2. Resetting VM to clean state..."
    VBoxManage controlvm "$VM_NAME" poweroff 2>/dev/null || true
    sleep 2
    VBoxManage snapshot "$VM_NAME" restore "$SNAPSHOT_NAME"
    echo "   ✓ VM reset (ready for OS testing)"
else
    echo ""
    echo "2. No VM snapshot found (skipping VM reset)"
fi

echo ""
echo "=== Test Cycle Complete ==="
echo ""
echo "Local tests: ✓ Passed"
echo "VM: Reset and ready"
echo ""
echo "Start VM in VirtualBox to test OS-level features"


