#!/bin/bash
# Script to install llama-cpp-python with appropriate hardware acceleration
# Detects system capabilities and installs the best available variant

set -e

echo "=== llama-cpp-python Installation Script ==="
echo ""

# Detect Python
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python not found. Please install Python 3.10+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Found Python $PYTHON_VERSION"

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Recommend: source .venv/bin/activate"
    echo ""
    read -p "Continue anyway? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi
fi

echo ""
echo "=== Detecting Hardware Acceleration ==="
echo ""

# Detect CUDA
HAS_CUDA=false
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA GPU detected"
    nvidia-smi --query-gpu=name --format=csv,noheader | head -1
    HAS_CUDA=true
elif [ -d /usr/local/cuda ] || [ -d /opt/cuda ]; then
    echo "✓ CUDA toolkit found (GPU may be available)"
    HAS_CUDA=true
else
    echo "✗ No CUDA detected"
fi

# Detect Metal (macOS)
HAS_METAL=false
if [ "$(uname)" == "Darwin" ]; then
    echo "✓ macOS detected - Metal acceleration available"
    HAS_METAL=true
else
    echo "✗ Not macOS - Metal not available"
fi

echo ""
echo "=== Installation Options ==="
echo ""

# Determine installation variant
if [ "$HAS_CUDA" = true ]; then
    echo "Installing llama-cpp-python with CUDA support..."
    echo ""
    CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python
elif [ "$HAS_METAL" = true ]; then
    echo "Installing llama-cpp-python with Metal support..."
    echo ""
    CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
else
    echo "Installing llama-cpp-python (CPU-only)..."
    echo ""
    pip install llama-cpp-python
fi

# Verify installation
echo ""
echo "=== Verifying Installation ==="
echo ""

$PYTHON_CMD -c "
import llama_cpp
print('✓ llama-cpp-python version:', llama_cpp.__version__)
print('✓ Import successful')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation complete!"
    echo ""
    if [ "$HAS_CUDA" = true ]; then
        echo "Hardware acceleration: CUDA (NVIDIA GPU)"
    elif [ "$HAS_METAL" = true ]; then
        echo "Hardware acceleration: Metal (Apple Silicon)"
    else
        echo "Hardware acceleration: CPU-only"
        echo "Note: For GPU support, install CUDA toolkit or use Apple Silicon"
    fi
    echo ""
    echo "Next steps:"
    echo "  1. Download a model: ./scripts/download-models.sh"
    echo "  2. Run tests: pytest tests/test_llama_cpp_backend.py -v"
else
    echo ""
    echo "❌ Installation verification failed"
    exit 1
fi
