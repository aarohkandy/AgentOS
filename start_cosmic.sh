#!/bin/bash
# Cosmic OS - Production Launcher
# Starts everything you need - daemon + sidebar
# Usage: ./start_cosmic.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[Cosmic]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Cleanup function
cleanup() {
    log "Shutting down..."
    pkill -f "core/ai_engine/main.py" 2>/dev/null || true
    pkill -f "core/gui/sidebar.py" 2>/dev/null || true
    rm -f /tmp/cosmic-ai.sock
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Check Python
if ! command -v python3 &> /dev/null; then
    error "python3 not found"
    exit 1
fi

# Kill any existing instances
log "Cleaning up old instances..."
pkill -f "core/ai_engine/main.py" 2>/dev/null || true
pkill -f "core/gui/sidebar.py" 2>/dev/null || true
rm -f /tmp/cosmic-ai.sock
sleep 1

# Start AI daemon
log "Starting AI daemon..."
export PYTHONPATH="$SCRIPT_DIR"
export PYTHONUNBUFFERED=1
python3 core/ai_engine/main.py > /tmp/cosmic-ai.log 2>&1 &
DAEMON_PID=$!

log "AI daemon started (PID: $DAEMON_PID)"
log "Waiting for daemon to be ready..."

# Wait for socket
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if [ -S "/tmp/cosmic-ai.sock" ]; then
        log "Daemon ready!"
        break
    fi
    
    if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
        error "Daemon crashed! Check /tmp/cosmic-ai.log"
        tail -20 /tmp/cosmic-ai.log
        exit 1
    fi
    
    sleep 0.5
    WAITED=$((WAITED + 1))
done

if [ ! -S "/tmp/cosmic-ai.sock" ]; then
    error "Daemon not ready after ${MAX_WAIT}s"
    tail -30 /tmp/cosmic-ai.log
    kill "$DAEMON_PID" 2>/dev/null || true
    exit 1
fi

# Start sidebar
log "Starting sidebar..."
log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  🌌 Cosmic OS is running!"
log "  Press Meta+Shift (Windows+Shift) to toggle sidebar"
log "  Press Ctrl+C to stop"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log ""

# Start sidebar with proper error handling
export DISPLAY="${DISPLAY:-:0}"
export PYTHONPATH="$SCRIPT_DIR"
python3 core/gui/sidebar.py || {
    error "Sidebar failed to start"
    error "Check if PyQt6 is installed: pip3 install --user PyQt6"
    kill "$DAEMON_PID" 2>/dev/null || true
    exit 1
}

