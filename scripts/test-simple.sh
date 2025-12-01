#!/bin/bash
# ULTRA SIMPLE testing - no VM, no complexity

set -e

echo "=== Super Simple Testing ==="
echo ""

# Just run tests locally - that's it!
cd "$(dirname "$0")/.."

if [ -d ".venv" ]; then
    .venv/bin/python -m pytest tests/ -v
else
    python3 -m pytest tests/ -v
fi

echo ""
echo "✓ Done! That's it - no VM needed."


