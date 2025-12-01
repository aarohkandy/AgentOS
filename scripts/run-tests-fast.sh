#!/bin/bash
# Fast test runner - uses Docker for speed

echo "=== Fast Test Runner ==="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Running tests locally instead..."
    cd "$(dirname "$0")/.."
    .venv/bin/python -m pytest tests/ -v
    exit $?
fi

echo "Building test Docker image..."
docker build -f Dockerfile.test -t ai-os-test:latest .

if [ $? -ne 0 ]; then
    echo "✗ Docker build failed. Falling back to local tests..."
    cd "$(dirname "$0")/.."
    .venv/bin/python -m pytest tests/ -v
    exit $?
fi

echo ""
echo "Running tests in Docker (fast, isolated)..."
docker run --rm ai-os-test:latest



