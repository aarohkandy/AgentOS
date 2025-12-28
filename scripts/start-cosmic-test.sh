#!/bin/bash
# Cosmic OS - Quick Test Launcher
# Starts AI daemon + Sidebar GUI for testing without full install
# Usage: ./scripts/start-cosmic-test.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOCKET_PATH="/tmp/cosmic-ai.sock"
DAEMON_PID=""

# Cleanup function
cleanup() {
    log_step "Cleaning up..."
    
    # Kill daemon if running
    if [ -n "$DAEMON_PID" ] && kill -0 "$DAEMON_PID" 2>/dev/null; then
        log_info "Stopping AI daemon (PID: $DAEMON_PID)..."
        kill "$DAEMON_PID" 2>/dev/null || true
        wait "$DAEMON_PID" 2>/dev/null || true
    fi
    
    # Remove socket if exists
    if [ -S "$SOCKET_PATH" ]; then
        rm -f "$SOCKET_PATH"
        log_info "Removed socket: $SOCKET_PATH"
    fi
    
    log_info "Cleanup complete"
    exit 0
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "python3 not found. Please install Python 3.11+"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/core/ai_engine/main.py" ]; then
    log_error "Cannot find core/ai_engine/main.py"
    log_error "Please run this script from the project root or scripts/ directory"
    exit 1
fi

# Check dependencies
log_step "Checking dependencies..."
MISSING_DEPS=()

if ! python3 -c "import PyQt6" 2>/dev/null; then
    MISSING_DEPS+=("PyQt6")
fi

if ! python3 -c "import dbus" 2>/dev/null && ! python3 -c "import socket" 2>/dev/null; then
    MISSING_DEPS+=("dbus-python (optional)")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log_warn "Missing dependencies: ${MISSING_DEPS[*]}"
    log_warn "Install with: pip3 install --user ${MISSING_DEPS[*]}"
    log_warn "Continuing anyway (some features may not work)..."
fi

# Check for existing socket/daemon
if [ -S "$SOCKET_PATH" ]; then
    log_warn "Socket already exists: $SOCKET_PATH"
    log_warn "Another instance may be running. Remove it first?"
    read -p "Remove and continue? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$SOCKET_PATH"
    else
        log_error "Aborted"
        exit 1
    fi
fi

# Start AI daemon in background
log_step "Starting AI daemon..."
cd "$PROJECT_ROOT"

# Set environment
export DISPLAY="${DISPLAY:-:0}"
export PYTHONPATH="$PROJECT_ROOT"
export PYTHONUNBUFFERED=1

# Start daemon
python3 core/ai_engine/main.py > /tmp/cosmic-ai-test.log 2>&1 &
DAEMON_PID=$!

log_info "AI daemon started (PID: $DAEMON_PID)"
log_info "Logs: /tmp/cosmic-ai-test.log"

# Wait for socket to be ready
log_step "Waiting for AI daemon to initialize..."
MAX_WAIT=10
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if [ -S "$SOCKET_PATH" ]; then
        log_info "Socket ready: $SOCKET_PATH"
        break
    fi
    
    # Check if daemon is still running
    if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
        log_error "AI daemon crashed! Check logs: /tmp/cosmic-ai-test.log"
        tail -20 /tmp/cosmic-ai-test.log
        exit 1
    fi
    
    sleep 0.5
    WAITED=$((WAITED + 1))
done

if [ ! -S "$SOCKET_PATH" ]; then
    log_error "Socket not created after ${MAX_WAIT}s"
    log_error "Daemon may have failed. Check logs: /tmp/cosmic-ai-test.log"
    tail -20 /tmp/cosmic-ai-test.log
    kill "$DAEMON_PID" 2>/dev/null || true
    exit 1
fi

# Start sidebar
log_step "Starting sidebar GUI..."
echo ""
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "  Cosmic OS Test Mode"
log_info "  AI Daemon: Running (PID: $DAEMON_PID)"
log_info "  Socket: $SOCKET_PATH"
log_info "  Press Ctrl+C to stop both components"
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start sidebar (foreground - will block)
python3 core/gui/sidebar.py

# If we get here, sidebar exited
log_info "Sidebar closed"

