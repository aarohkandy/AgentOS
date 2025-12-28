#!/bin/bash
# Run this script IN THE VM to check if models are visible

echo "=== VM Model Visibility Check ==="
echo ""

# Check if shared folder is mounted
if [ -d "/media/sf_agentOS" ]; then
    echo "✓ Shared folder mounted at /media/sf_agentOS"
else
    echo "✗ Shared folder NOT mounted at /media/sf_agentOS"
    echo "  Run: sudo mount -t vboxsf agentOS /media/sf_agentOS"
    exit 1
fi

# Check permissions
echo ""
echo "=== Permissions Check ==="
if groups | grep -q vboxsf; then
    echo "✓ User is in vboxsf group"
else
    echo "✗ User NOT in vboxsf group"
    echo "  Run: sudo usermod -aG vboxsf $USER"
    echo "  Then log out and back in"
fi

# Check models
echo ""
echo "=== Model Files Check ==="
for tier in 1 2 3 4; do
    model_file="/media/sf_agentOS/models/tier$tier/model.gguf"
    if [ -f "$model_file" ]; then
        size=$(stat -c%s "$model_file" 2>/dev/null || echo "unknown")
        size_mb=$((size / 1024 / 1024))
        echo "✓ Tier $tier: EXISTS - ${size_mb}MB"
        if [ "$size" = "0" ] || [ "$size" = "unknown" ]; then
            echo "  ⚠ WARNING: File is 0 bytes or unreadable"
        fi
    else
        echo "✗ Tier $tier: NOT FOUND at $model_file"
    fi
done

echo ""
echo "=== Python Path Resolution Test ==="
python3 << 'PYEOF'
from pathlib import Path
import sys

# Simulate what model_manager.py does
project_root = Path("/media/sf_agentOS")
print(f"Project root (VM): {project_root}")
print(f"Exists: {project_root.exists()}")

for tier in [1, 2, 3, 4]:
    model_path = project_root / "models" / f"tier{tier}" / "model.gguf"
    print(f"Tier {tier}: {model_path}")
    print(f"  Exists: {model_path.exists()}")
    if model_path.exists():
        size = model_path.stat().st_size
        print(f"  Size: {size:,} bytes ({size / (1024**2):.2f} MB)")
    print()
PYEOF


