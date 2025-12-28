#!/bin/bash
# Quick test script to run in VM

echo "=== Model Test in VM ==="
echo ""

cd /media/sf_agentOS

echo "File sizes:"
for tier in 1 2 3 4; do
    file="models/tier$tier/model.gguf"
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || echo "0")
        if [ "$size" -gt 0 ]; then
            size_mb=$((size / 1024 / 1024))
            size_gb=$((size / 1024 / 1024 / 1024))
            if [ "$size_gb" -gt 0 ]; then
                echo "✓ Tier $tier: ${size_gb}GB"
            else
                echo "✓ Tier $tier: ${size_mb}MB"
            fi
        else
            echo "✗ Tier $tier: 0 bytes (incomplete)"
        fi
    else
        echo "✗ Tier $tier: Not found"
    fi
done

echo ""
echo "Python path check:"
python3 << 'PYEOF'
from pathlib import Path

project_root = Path("/media/sf_agentOS")
print(f"Project root: {project_root}")
print(f"Exists: {project_root.exists()}")

for tier in [1, 2, 3, 4]:
    model_path = project_root / "models" / f"tier{tier}" / "model.gguf"
    if model_path.exists():
        size = model_path.stat().st_size
        if size > 0:
            size_mb = size / (1024**2)
            size_gb = size / (1024**3)
            if size_gb >= 1:
                print(f"Tier {tier}: {size_gb:.2f} GB ✓")
            else:
                print(f"Tier {tier}: {size_mb:.2f} MB ✓")
        else:
            print(f"Tier {tier}: 0 bytes ✗")
    else:
        print(f"Tier {tier}: Not found ✗")
PYEOF


