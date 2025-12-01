#!/bin/bash
# Simple test runner - no VM needed for 99% of tests

set -e

cd "$(dirname "$0")/.."

echo "=== Running Tests (No VM Required) ==="
echo ""

# Activate venv if it exists, otherwise use system python
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

# Run tests with nice output
$PYTHON -m pytest tests/ -v --tb=short "$@"

echo ""
echo "✓ All tests passed!"
echo ""
echo "Note: These tests run locally - no VM needed."
echo "Only use VM for E2E tests that need full OS (rare)."


