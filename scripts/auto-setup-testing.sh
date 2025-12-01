#!/bin/bash
# Automated setup for fast testing - I can run this for you

set -e

echo "=== Automated Testing Setup ==="
echo ""

# 1. Install pytest-xdist for parallel testing
echo "1. Installing pytest-xdist for parallel test execution..."
cd "$(dirname "$0")/.."
.venv/bin/pip install -q pytest-xdist
echo "   ✓ pytest-xdist installed"

# 2. Build Docker test image (if Docker available)
if command -v docker &> /dev/null; then
    echo ""
    echo "2. Building Docker test image..."
    docker build -f Dockerfile.test -t ai-os-test:latest . > /dev/null 2>&1
    echo "   ✓ Docker test image ready"
else
    echo ""
    echo "2. Docker not available (skipping Docker setup)"
fi

# 3. Check VirtualBox
if command -v VBoxManage &> /dev/null; then
    echo ""
    echo "3. VirtualBox detected - snapshot commands available"
    echo "   Note: You'll need to create the first snapshot manually after VM setup"
    echo "   Run: ./scripts/vm-snapshot-helper.sh create"
else
    echo ""
    echo "3. VirtualBox not detected"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "You can now run tests fast:"
echo "  - Local: pytest tests/ (runs in parallel automatically)"
echo "  - Docker: ./scripts/run-tests-fast.sh"
echo "  - VM: Use snapshots after initial setup"


