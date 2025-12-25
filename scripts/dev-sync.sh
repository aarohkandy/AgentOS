#!/bin/bash
# Cosmic OS - Development Hot-Reload File Watcher
# Monitors shared folder for changes and restarts services

set -e

echo "🔄 Cosmic OS - Hot-Reload System"
echo "================================="

# Configuration
WATCH_DIR="${COSMIC_WATCH_DIR:-/mnt/cosmic-os}"
DEBOUNCE_SECONDS=1
LAST_RELOAD=0

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $1"; }
log_change() { echo -e "${YELLOW}[$(date +%H:%M:%S)]${NC} $1"; }
log_debug() { echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} $1"; }

# Check dependencies
if ! command -v inotifywait &> /dev/null; then
    echo "Error: inotify-tools not installed"
    echo "Install with: sudo apt install inotify-tools"
    exit 1
fi

# Check watch directory
if [ ! -d "$WATCH_DIR" ]; then
    echo "Error: Watch directory not found: $WATCH_DIR"
    echo "Make sure the shared folder is mounted"
    exit 1
fi

log_info "Watching: $WATCH_DIR/core/"
log_info "Press Ctrl+C to stop"
echo ""

# Reload function with debouncing
reload_service() {
    local now=$(date +%s)
    local diff=$((now - LAST_RELOAD))
    
    if [ $diff -lt $DEBOUNCE_SECONDS ]; then
        log_debug "Debouncing... (wait ${DEBOUNCE_SECONDS}s between reloads)"
        return
    fi
    
    LAST_RELOAD=$now
    
    # Check if service is running
    if systemctl --user is-active cosmic-ai.service &>/dev/null; then
        log_info "Restarting cosmic-ai.service..."
        
        # Measure restart time
        local start_time=$(date +%s%N)
        
        systemctl --user restart cosmic-ai.service
        
        local end_time=$(date +%s%N)
        local duration=$(( (end_time - start_time) / 1000000 ))
        
        log_info "✅ Restarted in ${duration}ms"
        
        # Send desktop notification
        notify-send "Cosmic OS" "AI daemon reloaded (${duration}ms)" -t 2000 2>/dev/null || true
    else
        log_debug "cosmic-ai.service not running, skipping restart"
    fi
    
    # Optional: run quick test
    if [ "${COSMIC_RUN_TESTS:-false}" = "true" ]; then
        log_info "Running quick test..."
        python3 "$WATCH_DIR/scripts/test-ai.py" --quick 2>&1 | while read line; do
            log_debug "  $line"
        done
    fi
}

# File filter - ignore temp files, cache, etc.
should_ignore() {
    local file="$1"
    
    # Ignore patterns
    case "$file" in
        *.swp|*.swo|*~|*.pyc|*.pyo)
            return 0
            ;;
        *__pycache__*|*.git/*|*.idea/*|*.vscode/*)
            return 0
            ;;
        *.log|*.tmp)
            return 0
            ;;
    esac
    
    return 1
}

# Main watch loop
inotifywait -m -r \
    -e modify \
    -e create \
    -e delete \
    -e move \
    --format '%w%f|%e' \
    "$WATCH_DIR/core/" \
    2>/dev/null |
while IFS='|' read filepath event; do
    # Skip ignored files
    if should_ignore "$filepath"; then
        continue
    fi
    
    # Get relative path for cleaner output
    relative_path="${filepath#$WATCH_DIR/}"
    
    # Log the change
    case "$event" in
        *CREATE*)
            log_change "Created: $relative_path"
            ;;
        *DELETE*)
            log_change "Deleted: $relative_path"
            ;;
        *MODIFY*)
            log_change "Modified: $relative_path"
            ;;
        *MOVED*)
            log_change "Moved: $relative_path"
            ;;
        *)
            log_change "Changed: $relative_path ($event)"
            ;;
    esac
    
    # Trigger reload
    reload_service
done

log_info "File watcher stopped"
