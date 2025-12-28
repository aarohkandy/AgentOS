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
declare -A TIER1_MODELS=(
    ["smollm"]="https://huggingface.co/TheBloke/SmolLM-1.7B-GGUF/resolve/main/smollm-1.7b.Q4_K_M.gguf"
    ["phi3-mini"]="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
)

declare -A TIER2_MODELS=(
    ["llama3.2-3b"]="https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf"
    ["qwen2.5-3b"]="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
)

declare -A TIER3_MODELS=(
    ["qwen2.5-7b"]="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
    ["llama3.1-8b"]="https://huggingface.co/TheBloke/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct.Q4_K_M.gguf"
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
    
    if [ "$HF_CLI" = true ]; then
        # Use HuggingFace CLI for better resumption and progress
        local repo=$(echo "$url" | sed -n 's|.*/\([^/]*/[^/]*\)/resolve.*|\1|p')
        local file=$(basename "$url")
        huggingface-cli download "$repo" "$file" --local-dir "$(dirname "$output")" --local-dir-use-symlinks False
    elif command -v wget &> /dev/null; then
        wget --progress=bar:force -c "$url" -O "$output"
    else
        curl -L -C - --progress-bar "$url" -o "$output"
    fi
    
    if [ -f "$output" ]; then
        log_info "✅ Downloaded $name successfully"
        return 0
    else
        log_error "Failed to download $name"
        return 1
    fi
}

# Detect hardware and recommend tier
detect_tier() {
    log_step "Detecting hardware tier..."
    
    # Check RAM
    local ram_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local ram_gb=$((ram_kb / 1024 / 1024))
    
    # Check for GPU
    local has_nvidia=false
    if command -v nvidia-smi &> /dev/null; then
        has_nvidia=true
    fi
    
    log_info "System RAM: ${ram_gb}GB"
    log_info "NVIDIA GPU: $has_nvidia"
    
    if [ "$ram_gb" -gt 16 ] || [ "$has_nvidia" = true ]; then
        RECOMMENDED_TIER=3
    elif [ "$ram_gb" -ge 8 ]; then
        RECOMMENDED_TIER=2
    else
        RECOMMENDED_TIER=1
    fi
    
    log_info "Recommended tier: $RECOMMENDED_TIER"
}

# Install tier 1 models
install_tier1() {
    log_step "Installing Tier 1 models (lightweight)..."
    
    mkdir -p "$MODEL_DIR/tier1"
    check_disk_space 2
    
    # Default to SmolLM
    local url="${TIER1_MODELS[smollm]}"
    local output="$MODEL_DIR/tier1/model.gguf"
    
    download_file "$url" "$output" "SmolLM 1.7B"
}

# Install tier 2 models
install_tier2() {
    log_step "Installing Tier 2 models (balanced)..."
    
    mkdir -p "$MODEL_DIR/tier2"
    check_disk_space 4
    
    # Default to Qwen2.5-3B
    local url="${TIER2_MODELS[qwen2.5-3b]}"
    local output="$MODEL_DIR/tier2/model.gguf"
    
    download_file "$url" "$output" "Qwen2.5 3B"
}

# Install tier 3 models
install_tier3() {
    log_step "Installing Tier 3 models (powerful)..."
    
    mkdir -p "$MODEL_DIR/tier3"
    check_disk_space 8
    
    # Default to Qwen2.5-7B
    local url="${TIER3_MODELS[qwen2.5-7b]}"
    local output="$MODEL_DIR/tier3/model.gguf"
    
    download_file "$url" "$output" "Qwen2.5 7B"
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
    echo "2) Install Tier 1 (Lightweight - ~2GB)"
    echo "3) Install Tier 2 (Balanced - ~4GB)"
    echo "4) Install Tier 3 (Powerful - ~8GB)"
    echo "5) Install all tiers"
    echo "6) Install validators only"
    echo "7) Exit"
    echo ""
    read -p "Enter choice [1-7]: " choice
    
    case $choice in
        1)
            case $RECOMMENDED_TIER in
                1) install_tier1 ;;
                2) install_tier2 ;;
                3) install_tier3 ;;
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
            install_tier1
            install_tier2
            install_tier3
            install_validators
            ;;
        6)
            install_validators
            ;;
        7)
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
    mkdir -p "$MODEL_DIR"/{tier1,tier2,tier3,validators}
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
    mkdir -p "$MODEL_DIR"/{tier1,tier2,tier3,validators}
    
    case $2 in
        1) install_tier1; install_validators; update_config 1 ;;
        2) install_tier2; install_validators; update_config 2 ;;
        3) install_tier3; install_validators; update_config 3 ;;
        *) log_error "Invalid tier: $2"; exit 1 ;;
    esac
else
    main
fi
