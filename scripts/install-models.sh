#!/bin/bash
# Cosmic OS - AI Model Installation Script
# Downloads and installs appropriate models based on hardware tier

set -e

echo "🤖 Cosmic OS - AI Model Installer"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Support base directory for persistent models
if [ -n "$MODEL_BASE_DIR" ]; then
    MODEL_DIR="$MODEL_BASE_DIR"
    log_info "Using base model directory: $MODEL_DIR"
else
MODEL_DIR="$PROJECT_DIR/core/ai_engine/models"
fi

CONFIG_FILE="$PROJECT_DIR/config/model-urls.json"

# Model URLs (GGUF format for llama.cpp)
# Tier 1: EXTREME Easy - Qwen 2.5 0.5B (<1GB RAM)
# Using TinyLlama as fallback (known to work, <1GB)
declare -A TIER1_MODELS=(
    ["tinyllama"]="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
)

# Tier 2: Low - Llama 3.2 3B (2-4GB RAM)
declare -A TIER2_MODELS=(
    ["llama3.2-3b"]="https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf"
)

# Tier 3: Medium - Llama 3.1 8B (16-32GB RAM, 8-12GB VRAM)
# Using Qwen 2.5 7B as it's verified to work
declare -A TIER3_MODELS=(
    ["qwen2.5-7b"]="https://huggingface.co/TheBloke/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct.Q4_K_M.gguf"
)

# Tier 4: Very Powerful - Llama 3.1 70B (64GB+ RAM, 40GB+ VRAM)
declare -A TIER4_MODELS=(
    ["llama3.1-70b"]="https://huggingface.co/TheBloke/Llama-3.1-70B-Instruct-GGUF/resolve/main/llama-3.1-70b-instruct.Q4_K_M.gguf"
)

declare -A VALIDATOR_MODELS=(
    ["safety"]="https://huggingface.co/TheBloke/TinyLlama-1.1B-GGUF/resolve/main/tinyllama-1.1b.Q4_K_M.gguf"
    ["logic"]="https://huggingface.co/TheBloke/TinyLlama-1.1B-GGUF/resolve/main/tinyllama-1.1b.Q4_K_M.gguf"
    ["efficiency"]="https://huggingface.co/TheBloke/TinyLlama-1.1B-GGUF/resolve/main/tinyllama-1.1b.Q4_K_M.gguf"
)

# Check dependencies
check_dependencies() {
    log_step "Checking dependencies..."
    
    if ! command -v wget &> /dev/null && ! command -v curl &> /dev/null; then
        log_error "Neither wget nor curl found. Please install one of them."
        exit 1
    fi
    
    if command -v huggingface-cli &> /dev/null; then
        HF_CLI=true
        log_info "HuggingFace CLI available (preferred method)"
    else
        HF_CLI=false
        log_info "HuggingFace CLI not found, using direct download"
    fi
}

# Check disk space
check_disk_space() {
    local required_gb=$1
    local available_gb=$(df -BG "$MODEL_DIR" | awk 'NR==2 {print $4}' | tr -d 'G')
    
    if [ "$available_gb" -lt "$required_gb" ]; then
        log_error "Insufficient disk space. Need ${required_gb}GB, have ${available_gb}GB"
        exit 1
    fi
    
    log_info "Disk space check passed: ${available_gb}GB available"
}

# Download with progress
download_file() {
    local url=$1
    local output=$2
    local name=$3
    
    log_info "Downloading $name..."
    
    # Extract repo and file from URL
    local repo=$(echo "$url" | sed -n 's|.*huggingface\.co/\([^/]*/[^/]*\)/.*|\1|p')
        local file=$(basename "$url")
    local output_dir=$(dirname "$output")
    
    # Try Python huggingface_hub first (most reliable)
    if python3 -c "import huggingface_hub" 2>/dev/null; then
        log_info "Using Python huggingface_hub to download from $repo"
        python3 << EOF
from huggingface_hub import hf_hub_download
import os
try:
    downloaded = hf_hub_download(
        repo_id="$repo",
        filename="$file",
        local_dir="$output_dir",
        local_dir_use_symlinks=False,
        resume_download=True
    )
    print(f"Downloaded to: {downloaded}")
except Exception as e:
    print(f"Error: {e}")
    exit(1)
EOF
        if [ $? -eq 0 ] && [ -f "$output" ]; then
            log_info "✅ Downloaded $name successfully ($(du -h "$output" | cut -f1))"
            return 0
        fi
    fi
    
    # Fallback: Try direct download with wget/curl
    log_info "Attempting direct download from HuggingFace..."
    
    if command -v wget &> /dev/null; then
        # Use wget with retry and proper headers
        wget --progress=bar:force -c --header="User-Agent: Mozilla/5.0" "$url" -O "$output" 2>&1 | grep -E "(saving|%|ERROR)" || true
    else
        # Use curl with retry
        curl -L -C - --progress-bar --header "User-Agent: Mozilla/5.0" "$url" -o "$output" 2>&1 || true
    fi
    
    if [ -f "$output" ] && [ -s "$output" ]; then
        log_info "✅ Downloaded $name successfully ($(du -h "$output" | cut -f1))"
        return 0
    else
        log_error "Failed to download $name"
        log_info "URL: $url"
        log_info "Repo: $repo, File: $file"
        log_info "Try manually: python3 -c \"from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='$repo', filename='$file', local_dir='$output_dir')\""
        return 1
    fi
}

# Detect hardware and recommend tier
detect_tier() {
    log_step "Detecting hardware tier..."
    
    # Check RAM
    local ram_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local ram_gb=$((ram_kb / 1024 / 1024))
    
    # Check for GPU and VRAM
    local has_nvidia=false
    local gpu_vram_gb=0
    if command -v nvidia-smi &> /dev/null; then
        has_nvidia=true
        # Try to get VRAM
        VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
        if [ -n "$VRAM_MB" ]; then
            gpu_vram_gb=$((VRAM_MB / 1024))
        fi
    fi
    
    log_info "System RAM: ${ram_gb}GB"
    if [ "$has_nvidia" = true ]; then
        log_info "NVIDIA GPU: Yes (${gpu_vram_gb}GB VRAM)"
    else
        log_info "NVIDIA GPU: No"
    fi
    
    # Tier detection: 4 tiers
    if [ "$ram_gb" -ge 64 ] || [ "$gpu_vram_gb" -ge 40 ]; then
        RECOMMENDED_TIER=4  # Very Powerful
    elif [ "$ram_gb" -ge 16 ] || [ "$gpu_vram_gb" -ge 8 ]; then
        RECOMMENDED_TIER=3  # Medium
    elif [ "$ram_gb" -ge 2 ]; then
        RECOMMENDED_TIER=2  # Low
    else
        RECOMMENDED_TIER=1  # EXTREME Easy
    fi
    
    log_info "Recommended tier: $RECOMMENDED_TIER"
}

# Install tier 1 models (EXTREME Easy - TinyLlama)
install_tier1() {
    log_step "Installing Tier 1 models (EXTREME Easy - <1GB RAM)..."
    
    mkdir -p "$MODEL_DIR/tier1"
    check_disk_space 1
    
    # Using TinyLlama (verified to work, <1GB)
    local url="${TIER1_MODELS[tinyllama]}"
    local output="$MODEL_DIR/tier1/model.gguf"
    
    download_file "$url" "$output" "TinyLlama 1.1B"
}

# Install tier 2 models (Low - Llama 3.2 3B)
install_tier2() {
    log_step "Installing Tier 2 models (Low - 2-4GB RAM)..."
    
    mkdir -p "$MODEL_DIR/tier2"
    check_disk_space 3
    
    # Default to Llama 3.2 3B
    local url="${TIER2_MODELS[llama3.2-3b]}"
    local output="$MODEL_DIR/tier2/model.gguf"
    
    download_file "$url" "$output" "Llama 3.2 3B"
}

# Install tier 3 models (Medium - Qwen 2.5 7B)
install_tier3() {
    log_step "Installing Tier 3 models (Medium - 16-32GB RAM)..."
    
    mkdir -p "$MODEL_DIR/tier3"
    check_disk_space 6
    
    # Using Qwen 2.5 7B (verified to work)
    local url="${TIER3_MODELS[qwen2.5-7b]}"
    local output="$MODEL_DIR/tier3/model.gguf"
    
    download_file "$url" "$output" "Qwen 2.5 7B"
}

# Install tier 4 models (Very Powerful - Llama 3.1 70B)
install_tier4() {
    log_step "Installing Tier 4 models (Very Powerful - 64GB+ RAM or 40GB+ VRAM)..."
    
    mkdir -p "$MODEL_DIR/tier4"
    check_disk_space 40
    
    # Using Llama 3.1 70B
    local url="${TIER4_MODELS[llama3.1-70b]}"
    local output="$MODEL_DIR/tier4/model.gguf"
    
    download_file "$url" "$output" "Llama 3.1 70B"
}

# Install validator models
install_validators() {
    log_step "Installing validator models..."
    
    mkdir -p "$MODEL_DIR/validators"
    check_disk_space 3
    
    for name in "${!VALIDATOR_MODELS[@]}"; do
        local url="${VALIDATOR_MODELS[$name]}"
        local output="$MODEL_DIR/validators/${name}.gguf"
        
        if [ ! -f "$output" ]; then
            download_file "$url" "$output" "$name validator"
        else
            log_info "$name validator already exists, skipping"
        fi
    done
}

# Update config
update_config() {
    log_step "Updating configuration..."
    
    local tier=$1
    local config_path="$PROJECT_DIR/config/cosmic-os.conf"
    
    if [ -f "$config_path" ]; then
        # Update the tier setting
        sed -i "s/^tier = .*/tier = $tier/" "$config_path"
        sed -i "s|^main_model_path = .*|main_model_path = core/ai_engine/models/tier${tier}/model.gguf|" "$config_path"
        log_info "Configuration updated for tier $tier"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Select installation option:"
    echo "1) Auto-detect and install recommended tier ($RECOMMENDED_TIER)"
    echo "2) Install Tier 1 (EXTREME Easy - Qwen 2.5 0.5B - ~0.4GB)"
    echo "3) Install Tier 2 (Low - Llama 3.2 3B - ~2GB)"
    echo "4) Install Tier 3 (Medium - Phi-4 14B - ~8.5GB)"
    echo "5) Install Tier 4 (Very Powerful - Llama 3.1 70B - ~38GB)"
    echo "6) Install all tiers"
    echo "7) Install validators only"
    echo "8) Exit"
    echo ""
    read -p "Enter choice [1-8]: " choice
    
    case $choice in
        1)
            case $RECOMMENDED_TIER in
                1) install_tier1 ;;
                2) install_tier2 ;;
                3) install_tier3 ;;
                4) install_tier4 ;;
            esac
            install_validators
            update_config $RECOMMENDED_TIER
            ;;
        2)
            install_tier1
            install_validators
            update_config 1
            ;;
        3)
            install_tier2
            install_validators
            update_config 2
            ;;
        4)
            install_tier3
            install_validators
            update_config 3
            ;;
        5)
            install_tier4
            install_validators
            update_config 4
            ;;
        6)
            install_tier1
            install_tier2
            install_tier3
            install_tier4
            install_validators
            ;;
        7)
            install_validators
            ;;
        8)
            echo "Exiting..."
            exit 0
            ;;
        *)
            log_error "Invalid choice"
            show_menu
            ;;
    esac
}

# Main
main() {
    echo ""
    
    check_dependencies
    
    # Create model directories
    mkdir -p "$MODEL_DIR"/{tier1,tier2,tier3,tier4,validators}
    touch "$MODEL_DIR/.gitkeep"
    
    detect_tier
    show_menu
    
    echo ""
    log_info "✅ Model installation complete!"
    echo ""
    log_info "Model locations:"
    ls -la "$MODEL_DIR"/*/ 2>/dev/null || log_warn "No models installed yet"
    echo ""
}

# Handle command line arguments
BASE_DIR_ARG=""
if [ "$1" = "--base-dir" ] && [ -n "$2" ]; then
    MODEL_DIR="$2"
    BASE_DIR_ARG="$1 $2"
    shift 2
fi

if [ "$1" = "--tier" ] && [ -n "$2" ]; then
    check_dependencies
    mkdir -p "$MODEL_DIR"/{tier1,tier2,tier3,tier4,validators}
    
    case $2 in
        1) install_tier1; install_validators; update_config 1 ;;
        2) install_tier2; install_validators; update_config 2 ;;
        3) install_tier3; install_validators; update_config 3 ;;
        4) install_tier4; install_validators; update_config 4 ;;
        *) log_error "Invalid tier: $2 (must be 1-4)"; exit 1 ;;
    esac
else
    main
fi
