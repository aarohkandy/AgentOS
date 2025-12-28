#!/bin/bash
# Diagnostic script to check model sync between host and VM

echo "=== Model Sync Diagnostic ==="
echo ""

# Check from host perspective
echo "HOST MACHINE CHECK:"
echo "Project root: $(cd "$(dirname "$0")" && pwd)"
echo ""

for tier in 1 2 3 4; do
    model_file="models/tier$tier/model.gguf"
    if [ -f "$model_file" ]; then
        size=$(du -h "$model_file" | cut -f1)
        bytes=$(stat -f%z "$model_file" 2>/dev/null || stat -c%s "$model_file" 2>/dev/null)
        echo "✓ Tier $tier: EXISTS - $size ($bytes bytes)"
        # Check if file is readable
        if [ -r "$model_file" ]; then
            echo "  - Readable: YES"
        else
            echo "  - Readable: NO (PERMISSION ERROR)"
        fi
        # Check file type
        file_type=$(file "$model_file" 2>/dev/null | cut -d: -f2)
        echo "  - Type: $file_type"
    else
        echo "✗ Tier $tier: NOT FOUND"
    fi
    echo ""
done

echo "=== VM PERSPECTIVE (what VM should see) ==="
echo "Expected path in VM: /media/sf_agentOS/models/tierX/model.gguf"
echo ""
echo "To check from VM, run this command in the VM:"
echo "  ls -lah /media/sf_agentOS/models/tier*/model.gguf"
echo ""
echo "If files don't appear in VM, possible issues:"
echo "  1. VirtualBox shared folder not mounted"
echo "  2. User not in vboxsf group"
echo "  3. Files are 0 bytes (incomplete download)"
echo "  4. Permission issues (check with: ls -la /media/sf_agentOS/models/)"


