#!/bin/bash
# Complete visual testing workflow

set -e

echo "=== Visual Testing Workflow ==="
echo ""

# 1. Run code tests first (fast)
echo "1. Running code tests (fast check)..."
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest tests/ -v --tb=short -q

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Code tests failed - fix these first!"
    exit 1
fi

echo "   ✓ Code tests passed"
echo ""

# 2. Reset VM if needed
read -p "2. Reset VM to clean state? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./scripts/test-os-fast.sh
else
    echo "   Skipping VM reset"
fi

echo ""
echo "3. Starting VM for visual testing..."
./scripts/start-vm-visual.sh

echo ""
echo "=== Ready for Visual Testing ==="
echo ""
echo "In the VM, you can now:"
echo "  - See the desktop environment"
echo "  - Run your AI agent: python -m agent.agent_core"
echo "  - Test screen capture visually"
echo "  - Interact with the UI"
echo "  - See everything working in real-time"


