#!/bin/bash
# Hot-Reload Dev Sync Script

WATCH_DIR="core/"
SERVICE_NAME="cosmic-ai"

echo "Starting Hot-Reload Watcher for $WATCH_DIR..."

if ! command -v inotifywait &> /dev/null; then
    echo "inotifywait not found. Please install inotify-tools."
    exit 1
fi

inotifywait -m -r -e modify,create,delete "$WATCH_DIR" |
while read path action file; do
    if [[ "$file" =~ .*\.py$ ]]; then
        echo "Change detected in $file. Restarting $SERVICE_NAME..."
        
        # In a real systemd setup:
        # systemctl --user restart $SERVICE_NAME
        
        # For development (manual process restart simulation):
        pkill -f "core/ai_engine/main.py" || true
        # We assume the service manager (systemd) auto-restarts it, 
        # or we rely on the developer running it in a loop.
        
        # Send notification
        if command -v notify-send &> /dev/null; then
            notify-send "Cosmic AI" "Code reloaded: $file" -t 2000
        fi
        
        # Optional: Run tests
        # python3 scripts/test-ai.py
    fi
done
