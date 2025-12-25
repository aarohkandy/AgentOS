# Cosmic OS Development Guide

## Development Environment Setup

### Prerequisites

**On Host (CachyOS/Linux):**
- Python 3.11+
- Git
- VirtualBox 7.0+
- Text editor (VS Code, Cursor, etc.)

**In VM (Ubuntu/Kubuntu 24.04):**
- KDE Plasma desktop
- xdotool, wmctrl
- Python 3.11+ with PyQt6
- inotify-tools (for hot-reload)

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/cosmic-os/cosmic-os.git
cd cosmic-os
```

2. **Set up the development environment:**
```bash
./dev-setup.sh
```

3. **Create VirtualBox VM:**
   - Install Ubuntu 24.04 or Kubuntu 24.04
   - Install Guest Additions
   - Configure shared folder named `cosmic-os`

4. **Inside VM, run:**
```bash
cd /mnt/cosmic-os
./scripts/vm-setup.sh
```

5. **Start development:**
   - Edit code on host
   - Changes auto-sync to VM
   - Test in VM

## Project Structure

```
cosmic-os/
├── core/
│   ├── ai_engine/          # AI components
│   │   ├── main.py         # Main daemon
│   │   ├── model_manager.py
│   │   ├── command_generator.py
│   │   ├── command_validator.py
│   │   ├── executor.py
│   │   ├── ipc_server.py
│   │   └── config.py
│   │
│   ├── automation/         # GUI automation
│   │   ├── screen_controller.py
│   │   ├── window_manager.py
│   │   ├── action_primitives.py
│   │   └── accessibility.py
│   │
│   ├── gui/               # User interface
│   │   ├── sidebar.py
│   │   ├── setup_wizard.py
│   │   ├── settings_panel.py
│   │   └── assets/
│   │
│   └── system-config/     # System setup
│       ├── kde-plasma-setup.sh
│       ├── systemd/
│       └── plasma-configs/
│
├── scripts/               # Utility scripts
├── config/               # Configuration files
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Development Workflow

### Hot-Reload Development

The hot-reload system monitors your code changes and automatically restarts the AI daemon.

1. **Start the file watcher in VM:**
```bash
cosmic-watch
# or
./scripts/dev-sync.sh
```

2. **Edit code on host**

3. **Within 10-30 seconds, changes are live in VM**

4. **Test immediately**

### Running Tests

```bash
# Quick tests (for hot-reload feedback)
python3 scripts/test-ai.py --quick

# Full test suite
python3 scripts/test-ai.py --full

# Run pytest
cd /mnt/cosmic-os
pytest tests/ -v
```

### Useful Commands (VM)

```bash
# Reload AI daemon
cosmic-reload

# View logs
cosmic-logs

# Check status
cosmic-status

# Run quick test
cosmic-test

# Watch for changes
cosmic-watch
```

## Working with Components

### AI Engine

The AI engine is the core of Cosmic OS. It runs as a systemd user service.

**Starting manually:**
```bash
python3 core/ai_engine/main.py
```

**Service control:**
```bash
systemctl --user start cosmic-ai
systemctl --user stop cosmic-ai
systemctl --user restart cosmic-ai
```

**Testing the generator:**
```python
from core.ai_engine.command_generator import CommandGenerator

gen = CommandGenerator(None)  # No model = fallback mode
result = gen.generate("open firefox")
print(result)
```

### Automation Layer

The automation layer wraps xdotool for GUI control.

**Testing screen controller:**
```python
from core.automation.screen_controller import ScreenController

screen = ScreenController(dry_run=True)  # Dry run for testing
screen.mouse_move(100, 100)
screen.type_text("hello")
```

**Testing action primitives:**
```python
from core.automation.screen_controller import ScreenController
from core.automation.action_primitives import ActionPrimitives

screen = ScreenController(dry_run=True)
actions = ActionPrimitives(screen)

actions.click(100, 100)
actions.type_text("hello world")
actions.press_key("Return")
```

### GUI Components

The GUI is built with PyQt6. For testing:

```bash
# Test sidebar standalone
python3 core/gui/sidebar.py

# Test settings panel
python3 core/gui/settings_panel.py

# Test setup wizard
python3 core/gui/setup_wizard.py
```

### IPC Communication

Test IPC communication with the AI daemon:

```python
import socket
import json

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/cosmic-ai.sock")
sock.sendall(b"open firefox")
response = sock.recv(4096)
print(json.loads(response))
sock.close()
```

## Adding New Features

### Adding a New Action Type

1. **Update CommandGenerator prompt** (`command_generator.py`):
```python
self.system_prompt = """...
- {"action": "new_action", "param": "value"}
..."""
```

2. **Add execution logic** (`executor.py`):
```python
def _execute_step(self, step):
    action = step.get("action")
    # ...
    elif action == "new_action":
        param = step.get("param")
        self._execute_new_action(param)
```

3. **Add safety checks** (`command_validator.py`):
```python
def _validate_safety(self, actions):
    for step in actions:
        if step["action"] == "new_action":
            if self._is_dangerous_new_action(step):
                return False
```

4. **Add tests** (`tests/test_executor.py`):
```python
def test_new_action(self):
    plan = {"plan": [{"action": "new_action", "param": "value"}]}
    result = self.executor.execute(plan)
    assert result["success"] is True
```

### Adding a New Validator

1. **Create validator logic** (`command_validator.py`):
```python
def _validate_custom(self, actions):
    # Your validation logic
    return True
```

2. **Add to validation chain:**
```python
def approve_all(self, plan):
    # ...
    if not self._validate_custom(actions):
        logger.warning("Custom validation failed.")
        return False
```

### Adding GUI Features

1. **Create widget** in appropriate file
2. **Connect to IPC** for AI communication
3. **Add keyboard shortcuts** if needed
4. **Update settings panel** for configuration

## Debugging

### Enable Debug Logging

In `config/cosmic-os.conf`:
```ini
[Development]
debug_mode = true
log_level = DEBUG
```

### View Logs

```bash
# Systemd journal
journalctl --user -u cosmic-ai -f

# Log file
tail -f cosmic-ai.log
```

### Common Issues

**xdotool not working:**
- Ensure X11, not Wayland
- Check `$DISPLAY` is set
- Try: `xdotool getmouselocation`

**IPC connection refused:**
- Check if daemon is running: `systemctl --user status cosmic-ai`
- Check socket exists: `ls -la /tmp/cosmic-ai.sock`

**Model not loading:**
- Verify model file exists
- Check RAM available
- Try loading smaller tier

**Hot-reload not working:**
- Verify shared folder mounted
- Check inotifywait installed
- Verify file watcher running

## Code Style

- Python 3.11+ type hints
- Docstrings for all public functions
- Black formatting (line length 100)
- Sort imports with isort
- Meaningful variable names

## Git Workflow

1. Create feature branch: `git checkout -b feature/name`
2. Make changes
3. Test thoroughly
4. Commit with clear message
5. Push and create PR

## Resources

- [llama-cpp-python docs](https://llama-cpp-python.readthedocs.io/)
- [xdotool man page](https://man.archlinux.org/man/xdotool.1)
- [PyQt6 documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [KDE Plasma development](https://develop.kde.org/)
