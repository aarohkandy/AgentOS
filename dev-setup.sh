#!/bin/bash
# Cosmic OS - Development Environment Setup
# Run on your development host (CachyOS, Arch, etc.)

set -e

echo "
╔═══════════════════════════════════════════════════════════════════╗
║                                                                    ║
║   🛠️  COSMIC OS DEVELOPMENT SETUP                                 ║
║   Setting up your development environment                          ║
║                                                                    ║
╚═══════════════════════════════════════════════════════════════════╝
"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for Python
check_python() {
    log_step "Checking Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python $PYTHON_VERSION found"
    else
        log_warn "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    log_step "Creating virtual environment..."
    
    if [ -d "$SCRIPT_DIR/venv" ]; then
        log_info "Virtual environment already exists"
    else
        python3 -m venv "$SCRIPT_DIR/venv"
        log_info "Virtual environment created"
    fi
    
    source "$SCRIPT_DIR/venv/bin/activate"
}

# Install Python packages
install_packages() {
    log_step "Installing Python packages..."
    
    pip install --upgrade pip
    pip install -r "$SCRIPT_DIR/requirements.txt"
    
    log_info "Python packages installed"
}

# Install development tools
install_dev_tools() {
    log_step "Installing development tools..."
    
    pip install \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        isort \
        mypy \
        flake8 \
        pre-commit
    
    log_info "Development tools installed"
}

# Setup pre-commit hooks
setup_precommit() {
    log_step "Setting up pre-commit hooks..."
    
    if [ -f "$SCRIPT_DIR/.pre-commit-config.yaml" ]; then
        pre-commit install
        log_info "Pre-commit hooks installed"
    else
        # Create default pre-commit config
        cat > "$SCRIPT_DIR/.pre-commit-config.yaml" << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
EOF
        pre-commit install
        log_info "Pre-commit config created and hooks installed"
    fi
}

# Check for VirtualBox
check_virtualbox() {
    log_step "Checking for VirtualBox..."
    
    if command -v VBoxManage &> /dev/null; then
        VB_VERSION=$(VBoxManage --version)
        log_info "VirtualBox $VB_VERSION found"
    else
        log_warn "VirtualBox not found"
        log_warn "Install VirtualBox for VM-based testing"
    fi
}

# Create helper scripts
create_helpers() {
    log_step "Creating helper scripts..."
    
    mkdir -p "$SCRIPT_DIR/bin"
    
    # Quick test script
    cat > "$SCRIPT_DIR/bin/test-quick" << EOF
#!/bin/bash
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/scripts/test-ai.py" --quick
EOF
    chmod +x "$SCRIPT_DIR/bin/test-quick"
    
    # Full test script
    cat > "$SCRIPT_DIR/bin/test-full" << EOF
#!/bin/bash
source "$SCRIPT_DIR/venv/bin/activate"
pytest "$SCRIPT_DIR/tests" -v
EOF
    chmod +x "$SCRIPT_DIR/bin/test-full"
    
    # Lint script
    cat > "$SCRIPT_DIR/bin/lint" << EOF
#!/bin/bash
source "$SCRIPT_DIR/venv/bin/activate"
black "$SCRIPT_DIR/core" "$SCRIPT_DIR/scripts" "$SCRIPT_DIR/tests"
isort "$SCRIPT_DIR/core" "$SCRIPT_DIR/scripts" "$SCRIPT_DIR/tests"
flake8 "$SCRIPT_DIR/core" --max-line-length=100
EOF
    chmod +x "$SCRIPT_DIR/bin/lint"
    
    # Run sidebar for testing
    cat > "$SCRIPT_DIR/bin/run-sidebar" << EOF
#!/bin/bash
source "$SCRIPT_DIR/venv/bin/activate"
export PYTHONPATH="$SCRIPT_DIR"
python3 "$SCRIPT_DIR/core/gui/sidebar.py"
EOF
    chmod +x "$SCRIPT_DIR/bin/run-sidebar"
    
    log_info "Helper scripts created in ./bin/"
}

# Print instructions
print_instructions() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║   ✅ DEVELOPMENT ENVIRONMENT READY                                ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Activate virtual environment:"
    echo "  source venv/bin/activate"
    echo ""
    echo "Helper commands (in ./bin/):"
    echo "  ./bin/test-quick    - Run quick tests"
    echo "  ./bin/test-full     - Run full test suite"
    echo "  ./bin/lint          - Format and lint code"
    echo "  ./bin/run-sidebar   - Run sidebar GUI"
    echo ""
    echo "Next steps for VM testing:"
    echo "  1. Create Ubuntu 24.04 VM in VirtualBox"
    echo "  2. Configure shared folder named 'cosmic-os'"
    echo "  3. In VM, run: /mnt/cosmic-os/scripts/vm-setup.sh"
    echo ""
    echo "Documentation:"
    echo "  docs/DEVELOPMENT.md  - Full development guide"
    echo "  docs/ARCHITECTURE.md - System architecture"
    echo "  docs/API.md          - API reference"
    echo ""
}

# Main
main() {
    check_python
    setup_venv
    install_packages
    install_dev_tools
    setup_precommit
    check_virtualbox
    create_helpers
    print_instructions
}

main
