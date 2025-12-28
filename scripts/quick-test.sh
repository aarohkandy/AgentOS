#!/bin/bash
# Ultra-simple test launcher - minimal checks
# Just starts both components, assumes you're in project root

cd "$(dirname "$0")/.." || exit 1

# Kill any existing instance
pkill -f "core/ai_engine/main.py" 2>/dev/null || true
rm -f /tmp/cosmic-ai.sock

# Start daemon in background
python3 core/ai_engine/main.py &
DAEMON_PID=$!

# Wait a moment for socket
sleep 2

# Start sidebar (foreground)
python3 core/gui/sidebar.py

# Cleanup on exit
kill $DAEMON_PID 2>/dev/null || true
rm -f /tmp/cosmic-ai.sock

