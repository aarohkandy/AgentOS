#!/bin/bash
# Quick install llama-cpp-python in VM
# Run this in the VM: cd /media/sf_agentOS && ./scripts/quick-install-llama.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

log_step "Installing llama-cpp-python..."

# Check if already installed
if python3 -c "from llama_cpp import Llama" 2>/dev/null; then
    log_info "✓ llama-cpp-python already installed"
    exit 0
fi

# Install build dependencies
log_info "Installing build dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq cmake build-essential python3-dev 2>/dev/null || {
        log_warn "Some dependencies may be missing, continuing anyway..."
    }
fi

# Install llama-cpp-python
log_info "Compiling llama-cpp-python (this takes 5-10 minutes)..."
log_info "This is a one-time setup. Please wait..."

# Try --user first (works on Ubuntu/Debian)
if pip3 install --user llama-cpp-python 2>&1 | tee /tmp/llama-install.log; then
    log_info "✓ llama-cpp-python installed successfully!"
elif pip3 install --break-system-packages --user llama-cpp-python 2>&1 | tee -a /tmp/llama-install.log; then
    log_info "✓ llama-cpp-python installed successfully!"
else
    log_warn "Installation failed. Check /tmp/llama-install.log"
    log_info "Try manually: pip3 install --user llama-cpp-python"
    exit 1
fi

# Verify
if python3 -c "from llama_cpp import Llama" 2>/dev/null; then
    log_info "✓ Verification successful! llama-cpp-python is ready."
    log_info ""
    log_info "Now you can:"
    log_info "  1. Download models: ./scripts/install-models.sh --tier 3"
    log_info "  2. Or run: ./scripts/install-all.sh (installs everything)"
else
    log_warn "Installation completed but verification failed"
    exit 1
fi

