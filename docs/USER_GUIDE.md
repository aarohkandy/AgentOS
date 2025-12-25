# Cosmic OS User Guide

## Welcome to Cosmic OS

Cosmic OS brings AI directly into your desktop. Talk to your computer naturally and watch it perform actions for you.

## Getting Started

### System Requirements

- **OS**: Ubuntu 24.04 LTS or Kubuntu 24.04 LTS
- **RAM**: 
  - Minimum: 4GB (Tier 1)
  - Recommended: 8GB+ (Tier 2/3)
- **Storage**: 5-15GB for AI models
- **Display Server**: X11 (Wayland support coming)

### Installation

1. **Download Cosmic OS:**
```bash
git clone https://github.com/cosmic-os/cosmic-os.git
cd cosmic-os
```

2. **Run the installer:**
```bash
sudo ./install.sh
```

3. **Complete the setup wizard** (first boot)

4. **Log out and log back in** to activate

### First Launch

After installation, press **Ctrl+Space** to open the AI sidebar.

## Using the AI Sidebar

### Opening the Sidebar

- Press **Ctrl+Space** anywhere to toggle the sidebar
- It slides in from the right side of your screen

### Talking to the AI

Type natural language commands like:
- "Open Firefox"
- "Search for cats on Google"
- "Open the file manager and go to Documents"
- "Take a screenshot and save it to Desktop"
- "Close all windows"

### Understanding Command Plans

When you send a request, the AI shows you what it will do:

```
📋 Command Plan
Opening Firefox and navigating to Gmail

1. click Firefox @ (100, 50)
2. wait 2s
3. type "gmail.com"
4. press Return

⏱️ Estimated time: 5s

[✕ Deny]                [✓ Approve]
```

- **Review the plan** to see exactly what will happen
- **Approve** to execute the actions
- **Deny** to cancel and try a different request

### What Can the AI Do?

The AI controls your desktop through actual mouse clicks and keyboard input:

✅ **Supported Actions:**
- Open and close applications
- Navigate web browsers
- Type text and fill forms
- Click buttons and links
- Manage windows (minimize, maximize, move)
- Search and find files
- Basic system settings

❌ **Not Supported (for safety):**
- Installing/uninstalling software
- System administration tasks
- Accessing sensitive directories
- Running terminal commands

## Settings

### Opening Settings

1. Open the sidebar (Ctrl+Space)
2. Click the ⚙️ button in the header

### AI Model Settings

**Model Tier:**
- **Tier 1 (Lightweight)**: Faster responses, basic capabilities
- **Tier 2 (Balanced)**: Good balance of speed and quality
- **Tier 3 (Powerful)**: Best understanding, slower on weak hardware

**Auto** automatically selects based on your hardware.

### Permissions

Control what the AI can do:

- **File Operations**: Create, modify, delete files
- **Network Access**: Open URLs, download files
- **System Settings**: Change system configuration (disabled by default)
- **Require Confirmation**: Always show plan before executing

### Automation Settings

Fine-tune execution speed:

- **Click Delay**: Pause between clicks (100ms default)
- **Type Delay**: Pause between keystrokes (50ms default)
- **Max Retries**: Attempts before failing (3 default)

## Tips and Tricks

### Be Specific

The more specific your request, the better:

| Vague | Specific |
|-------|----------|
| "Open browser" | "Open Firefox" |
| "Go to Google" | "Open Firefox and go to google.com" |
| "Find my file" | "Open file manager and go to Documents folder" |

### Use Wait Commands

For slow applications or websites:
- "Open Firefox, wait 3 seconds, then go to gmail.com"

### Chain Actions

Combine multiple steps:
- "Open Firefox, go to google.com, search for weather, and click the first result"

### Cancel Anytime

- Press **Escape** to close the sidebar
- Click **Deny** to reject a plan
- Press **Ctrl+Shift+Escape** to cancel during execution

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Space | Toggle sidebar |
| Escape | Close sidebar / Deny plan |
| Enter | Submit message / Approve plan |
| Ctrl+Enter | Submit and auto-execute |
| Ctrl+L | Clear chat history |
| Ctrl+, | Open settings |

## Troubleshooting

### Sidebar Won't Open

1. Check if the AI daemon is running:
```bash
systemctl --user status cosmic-ai
```

2. Restart the daemon:
```bash
systemctl --user restart cosmic-ai
```

3. Check logs for errors:
```bash
journalctl --user -u cosmic-ai -n 50
```

### AI Not Responding

1. Ensure the model is downloaded:
```bash
./scripts/install-models.sh
```

2. Check if you have enough RAM for your tier

3. Try switching to a lower tier in settings

### Actions Not Working

1. **Ensure X11, not Wayland:**
   - Log out → Select "Plasma (X11)" at login

2. **Check xdotool:**
```bash
xdotool getmouselocation
```

3. **Window might not be focused:**
   - Make sure the target window is visible
   - Try: "Focus the Firefox window first"

### Dangerous Command Blocked

This is a safety feature! The AI blocks potentially harmful actions.

If you believe it's a false positive:
1. Try rephrasing your request
2. Break it into smaller steps
3. Check the blocked command list in settings

## Privacy & Safety

### What Data is Processed

- **Locally only**: All AI processing happens on your computer
- **No cloud**: Your requests never leave your machine
- **No history**: Conversations are not saved by default

### Safety Features

1. **Three Validators**: Every command is checked by 3 AI safety models
2. **Blacklist**: Known dangerous commands are always blocked
3. **Confirmation**: You approve every action before execution
4. **Permissions**: Control what the AI can access

### Blocked Operations

The AI cannot:
- Access `/etc/`, `/boot/`, `/sys/`, `/proc/`
- Read `~/.ssh/` or `~/.gnupg/`
- Run `rm -rf`, `mkfs`, `dd` or similar
- Execute shell commands directly

## FAQ

**Q: Does Cosmic OS work with Wayland?**  
A: Currently X11 only. Wayland support is planned.

**Q: Can I use my own AI model?**  
A: Yes! Place a GGUF model in `core/ai_engine/models/` and update the config.

**Q: Why is the AI slow?**  
A: Try using a lower tier model, or ensure no other heavy processes are running.

**Q: Can the AI see my screen?**  
A: No. It works with predefined coordinates, not actual screen content. Vision support is planned.

**Q: Is it safe to use?**  
A: Yes! All commands are validated, and you approve every action. The AI cannot execute anything without your confirmation.

## Getting Help

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/cosmic-os/cosmic-os/issues)
- **Community**: Coming soon

## Uninstalling

To remove Cosmic OS:

```bash
./uninstall.sh
```

This will:
- Stop and disable the AI daemon
- Remove installed files
- Keep your configuration (optional)
- Restore original KDE settings (optional)
