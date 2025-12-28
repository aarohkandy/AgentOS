#!/bin/bash
# Quick AI Setup Script
# Installs llama-cpp-python and optionally downloads models

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_step "Cosmic OS - AI Integration Setup"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    log_warn "python3 not found"
    exit 1
fi

# Check if llama-cpp-python is installed
log_step "Checking llama-cpp-python..."
if python3 -c "from llama_cpp import Llama" 2>/dev/null; then
    log_info "✓ llama-cpp-python already installed"
else
    log_warn "llama-cpp-python not installed"
    echo ""
    echo "Installing llama-cpp-python..."
    echo "This may take a few minutes (compiles from source)..."
    
    # Install dependencies
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq cmake build-essential python3-dev 2>/dev/null || true
    fi
    
    # Install llama-cpp-python
    pip3 install --user llama-cpp-python || {
        log_warn "Installation failed. Try: pip3 install --user llama-cpp-python"
        exit 1
    }
    
    log_info "✓ llama-cpp-python installed"
fi

# Check for models
log_step "Checking for AI models..."
cd "$PROJECT_ROOT"

MODEL_FOUND=false
for tier in 1 2 3; do
    model_path="core/ai_engine/models/tier${tier}/model.gguf"
    if [ -f "$model_path" ]; then
        log_info "✓ Found model: $model_path"
        MODEL_FOUND=true
        break
    fi
done

if [ "$MODEL_FOUND" = false ]; then
    log_warn "No AI models found"
    echo ""
    echo "To download models, run:"
    echo "  ./scripts/install-models.sh --tier 2"
    echo ""
    echo "Or use the interactive menu:"
    echo "  ./scripts/install-models.sh"
    echo ""
    read -p "Download models now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        "$SCRIPT_DIR/install-models.sh"
    fi
else
    log_info "✓ Models found - AI is ready!"
fi

echo ""
log_info "Setup complete! Restart the AI daemon to use AI models."
echo ""
log_info "Test with: ./scripts/start-cosmic-test.sh"

