#!/bin/bash
# Complete development environment setup script
# Sets up everything needed for AI-OS agent development

set -e

echo "=== AI-OS Development Environment Setup ==="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    echo "Please install Python 3.10+ first"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION found"

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Not in project root directory"
    echo "Please run this script from /home/aaroh/Downloads/AgentOS"
    exit 1
fi

echo ""
echo "=== Step 1: Virtual Environment ==="
echo ""

# Create or activate virtualenv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtualenv
source .venv/bin/activate

echo "✓ Virtual environment activated"
echo ""
echo "=== Step 2: Installing Dependencies ==="
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install package in editable mode
echo "Installing ai-os-agent package..."
pip install -e .

echo "✓ All dependencies installed"
echo ""
echo "=== Step 3: Development Tools ==="
echo ""

# Install development tools
echo "Installing development tools..."
pip install black isort flake8 mypy pre-commit

echo "✓ Development tools installed"
echo ""
echo "=== Step 4: Running Tests ==="
echo ""

# Run tests to verify setup
echo "Running test suite..."
pytest tests/ -v --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "⚠️  Some tests failed - please review above"
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Your development environment is ready. Next steps:"
echo ""
echo "1. Activate virtualenv (if not already active):"
echo "   source .venv/bin/activate"
echo ""
echo "2. Install llama.cpp (optional, for LLM integration):"
echo "   ./scripts/setup-llama-cpp.sh"
echo ""
echo "3. Download models (optional):"
echo "   ./scripts/download-models.sh"
echo ""
echo "4. Run tests:"
echo "   pytest tests/ -v"
echo ""
echo "5. Start coding!"
echo ""
