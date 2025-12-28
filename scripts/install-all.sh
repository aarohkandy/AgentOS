#!/bin/bash
# Cosmic OS - Complete AI Installation
# Installs llama-cpp-python, downloads models to base folder, sets up everything

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Base folder for models (persists across installs)
BASE_MODEL_DIR="${BASE_MODEL_DIR:-$PROJECT_ROOT/models}"
LOCAL_MODEL_DIR="$PROJECT_ROOT/core/ai_engine/models"

log_step "╔═══════════════════════════════════════════════════════════════╗"
log_step "║   Cosmic OS - Complete AI Installation                        ║"
log_step "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Detect tier
detect_tier() {
    log_step "Detecting hardware tier..."
    
    RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")
    RAM_GB=$((RAM_KB / 1024 / 1024))
    
    HAS_GPU=false
    GPU_VRAM_GB=0
    if command -v nvidia-smi &> /dev/null; then
        HAS_GPU=true
        # Try to get VRAM
        VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$VRAM_MB" ]; then
            GPU_VRAM_GB=$((VRAM_MB / 1024))
        fi
    fi
    
    # Tier detection: 4 tiers
    if [ "$RAM_GB" -ge 64 ] || [ "$GPU_VRAM_GB" -ge 40 ]; then
        TIER=4  # Very Powerful
    elif [ "$RAM_GB" -ge 16 ] || [ "$GPU_VRAM_GB" -ge 8 ]; then
        TIER=3  # Medium
    elif [ "$RAM_GB" -ge 2 ]; then
        TIER=2  # Low
    else
        TIER=1  # EXTREME Easy
    fi
    
    if [ "$HAS_GPU" = true ]; then
        log_info "Detected: ${RAM_GB}GB RAM, ${GPU_VRAM_GB}GB VRAM → Tier $TIER"
    else
        log_info "Detected: ${RAM_GB}GB RAM, No GPU → Tier $TIER"
    fi
    echo ""
}

# Install llama-cpp-python
install_llama_cpp() {
    log_step "Installing llama-cpp-python..."
    
    if python3 -c "from llama_cpp import Llama" 2>/dev/null; then
        log_info "✓ llama-cpp-python already installed"
        return 0
    fi
    
    log_info "Installing dependencies..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq cmake build-essential python3-dev 2>/dev/null || {
            log_warn "Some dependencies may be missing, continuing anyway..."
        }
    fi
    
    log_info "Compiling llama-cpp-python (this may take 5-10 minutes)..."
    
    # Try different installation methods based on system
    INSTALLED=false
    
    # Method 1: --user flag (works on Ubuntu/Debian)
    if pip3 install --user llama-cpp-python 2>&1 | tee /tmp/llama-install.log; then
        log_info "✓ llama-cpp-python installed with --user flag"
        INSTALLED=true
    # Method 2: --break-system-packages (Arch Linux)
    elif pip3 install --break-system-packages --user llama-cpp-python 2>&1 | tee -a /tmp/llama-install.log; then
        log_info "✓ llama-cpp-python installed (with --break-system-packages)"
        INSTALLED=true
    # Method 3: Try without --user (some systems)
    elif pip3 install llama-cpp-python 2>&1 | tee -a /tmp/llama-install.log; then
        log_info "✓ llama-cpp-python installed"
        INSTALLED=true
    fi
    
    if [ "$INSTALLED" = false ]; then
        log_error "Failed to install llama-cpp-python"
        log_info "Try manually:"
        log_info "  pip3 install --break-system-packages --user llama-cpp-python"
        log_info "Or create venv: python3 -m venv venv && source venv/bin/activate && pip install llama-cpp-python"
        log_info "Install log: /tmp/llama-install.log"
        exit 1
    fi
    
    log_info "✓ llama-cpp-python installed"
}

# Setup model directories
setup_model_dirs() {
    log_step "Setting up model directories..."
    
    # Create base model directory (persists)
    mkdir -p "$BASE_MODEL_DIR"/{tier1,tier2,tier3,tier4,validators}
    log_info "Base models: $BASE_MODEL_DIR"
    
    # Create local model directory (for symlinks)
    mkdir -p "$LOCAL_MODEL_DIR"/{tier1,tier2,tier3,tier4,validators}
    
    # Create symlinks from local to base (if base has models)
    for tier in tier1 tier2 tier3 tier4; do
        if [ -f "$BASE_MODEL_DIR/$tier/model.gguf" ]; then
            if [ ! -L "$LOCAL_MODEL_DIR/$tier/model.gguf" ]; then
                ln -sf "$BASE_MODEL_DIR/$tier/model.gguf" "$LOCAL_MODEL_DIR/$tier/model.gguf"
                log_info "Linked $tier model"
            fi
        fi
    done
    
    for validator in safety logic efficiency; do
        if [ -f "$BASE_MODEL_DIR/validators/$validator.gguf" ]; then
            if [ ! -L "$LOCAL_MODEL_DIR/validators/$validator.gguf" ]; then
                ln -sf "$BASE_MODEL_DIR/validators/$validator.gguf" "$LOCAL_MODEL_DIR/validators/$validator.gguf"
                log_info "Linked $validator validator"
            fi
        fi
    done
    
    log_info "✓ Model directories ready"
}

# Download models to base folder
download_models() {
    log_step "Downloading AI models..."
    
    # Check if models already exist
    if [ -f "$BASE_MODEL_DIR/tier$TIER/model.gguf" ]; then
        log_info "✓ Tier $TIER model already exists in base folder"
        read -p "Re-download? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping download (using existing models)"
            setup_model_dirs
            return 0
        fi
    fi
    
    log_info "Models will be downloaded to: $BASE_MODEL_DIR"
    log_info "This location persists across installs!"
    echo ""
    
    # Set environment variable for install-models.sh
    export MODEL_BASE_DIR="$BASE_MODEL_DIR"
    
    # Call install-models.sh with tier (it will use MODEL_BASE_DIR env var)
    "$SCRIPT_DIR/install-models.sh" --tier "$TIER" || {
        log_error "Model download failed"
        exit 1
    }
    
    # Create symlinks
    setup_model_dirs
}

# Update model manager to check base folder
update_model_paths() {
    log_step "Configuring model paths..."
    
    # The model_manager.py already checks multiple paths, but we'll ensure
    # the base folder is in the search path by creating symlinks
    # (already done in setup_model_dirs)
    
    log_info "✓ Model paths configured"
}

# Main installation
main() {
    detect_tier
    
    # Step 1: Install llama-cpp-python
    install_llama_cpp
    echo ""
    
    # Step 2: Setup directories
    setup_model_dirs
    echo ""
    
    # Step 3: Download models
    download_models
    echo ""
    
    # Step 4: Verify
    log_step "Verifying installation..."
    
    if python3 -c "from llama_cpp import Llama" 2>/dev/null; then
        log_info "✓ llama-cpp-python: OK"
    else
        log_error "✗ llama-cpp-python: FAILED"
    fi
    
    if [ -f "$BASE_MODEL_DIR/tier$TIER/model.gguf" ]; then
        log_info "✓ Main model (Tier $TIER): OK"
    else
        log_warn "✗ Main model: Not found"
    fi
    
    if [ -f "$BASE_MODEL_DIR/validators/safety.gguf" ]; then
        log_info "✓ Validator models: OK"
    else
        log_warn "✗ Validator models: Not found"
    fi
    
    echo ""
    log_step "╔═══════════════════════════════════════════════════════════════╗"
    log_step "║   ✅ Installation Complete!                                  ║"
    log_step "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Models are stored in: $BASE_MODEL_DIR"
    log_info "This folder persists across installs!"
    echo ""
    log_info "Restart the AI daemon to use the models:"
    log_info "  ./scripts/start-cosmic-test.sh"
    echo ""
}

# Run
main

