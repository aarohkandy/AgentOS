# Cosmic OS - Quick Start Guide

## 🚀 Instant Start

```bash
./start_cosmic.sh
```

That's it! The script will:
1. ✅ Check dependencies
2. ✅ Start AI daemon
3. ✅ Wait for it to be ready
4. ✅ Launch sidebar
5. ✅ Show you the hotkey

## ⌨️ Hotkey

**Press `Meta+Shift` (Windows+Shift)** to toggle the sidebar

## 🎯 First Commands to Try

1. **Simple Math**: `5*5`
2. **Time Query**: `what time is it`
3. **System Info**: `system info`
4. **Open App**: `open firefox`
5. **Complex Task**: `download and install firefox`

## 🔧 Troubleshooting

### Sidebar doesn't appear
- Check if PyQt6 is installed: `pip3 install --user PyQt6`
- Check logs: `tail -f /tmp/cosmic-ai.log`

### AI not responding
- Check if daemon is running: `ps aux | grep main.py`
- Check socket: `ls -l /tmp/cosmic-ai.sock`
- Restart: `./start_cosmic.sh`

### Hotkey not working
- On KDE: Check System Settings → Shortcuts → Custom Shortcuts
- The hotkey should be: `Meta+Shift`

## 📦 Dependencies

Install all dependencies:
```bash
pip3 install --user -r requirements.txt
```

Or install individually:
```bash
pip3 install --user PyQt6 psutil requests
```

## 🎨 Features

- ✅ **Instant responses** for cached queries
- ✅ **Smooth animations** (iOS-quality)
- ✅ **100% CPU usage** when processing
- ✅ **Unlimited memory** for AI
- ✅ **No crashes** - comprehensive error handling
- ✅ **Screen space management** - sidebar excluded
- ✅ **Step-by-step planning** for complex tasks
- ✅ **Internet & system access** - time, news, web search

## 🐛 Report Issues

If something doesn't work:
1. Check logs: `/tmp/cosmic-ai.log`
2. Run test suite: `python3 test_all_features.py`
3. Check dependencies: `python3 -c "import PyQt6; print('OK')"`




