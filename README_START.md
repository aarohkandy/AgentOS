# 🚀 Start Cosmic OS - It Just Works!

## Quick Start

```bash
./start_cosmic.sh
```

That's it! The script will:
1. ✅ Start the AI daemon
2. ✅ Wait for it to be ready
3. ✅ Launch the sidebar UI
4. ✅ Everything works instantly

## Using Cosmic OS

1. **Press Meta+Shift** (Windows+Shift) to toggle the sidebar
2. **Type your request** in the input field
3. **Press Enter** to send
4. **Approve the plan** if it's a complex task
5. **Watch it execute** smoothly

## Features

- ✅ **100% CPU utilization** - Maximum performance
- ✅ **Unlimited memory** - Uses all available RAM
- ✅ **Never crashes** - Comprehensive error handling
- ✅ **iOS-quality UI** - Smooth animations, perfect typography
- ✅ **Simple queries** - Direct answers (no overthinking)
- ✅ **Complex tasks** - Step-by-step execution
- ✅ **Internet access** - Time, news, system info
- ✅ **Screen exclusion** - Sidebar doesn't interfere

## Troubleshooting

If the hotkey doesn't work:
```bash
# Configure KDE shortcut manually
kwriteconfig5 --file kglobalshortcutsrc \
  --group "cosmic-ai" \
  --key "toggle-sidebar" \
  "Meta+Shift,Meta+Shift,Toggle Cosmic AI Sidebar"
```

## Logs

- AI Daemon: `/tmp/cosmic-ai.log`
- Sidebar: Check terminal output

---

**Enjoy your iOS-quality AI assistant!** 🎉




