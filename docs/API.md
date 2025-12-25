# Cosmic OS API Reference

## IPC Interface

Cosmic OS AI daemon exposes two IPC interfaces:

### D-Bus Interface

**Service:** `com.cosmicos.ai`  
**Path:** `/com/cosmicos/ai`

#### Methods

##### ProcessRequest
Process a natural language request.

```
ProcessRequest(message: String) -> String
```

**Parameters:**
- `message`: Natural language user request

**Returns:**
- JSON string containing command plan or error

**Example (Python):**
```python
import dbus

bus = dbus.SessionBus()
proxy = bus.get_object('com.cosmicos.ai', '/com/cosmicos/ai')
iface = dbus.Interface(proxy, 'com.cosmicos.ai')

result = iface.ProcessRequest("open firefox")
print(result)
```

### Unix Socket Interface

**Path:** `/tmp/cosmic-ai.sock`

Send UTF-8 encoded messages, receive JSON responses.

**Example (Python):**
```python
import socket
import json

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/cosmic-ai.sock")
sock.sendall(b"open firefox")
response = sock.recv(4096)
data = json.loads(response.decode())
sock.close()
```

---

## Request/Response Format

### Request

Plain text natural language message:
```
open firefox and go to google.com
```

### Response

#### Success (Command Plan)
```json
{
    "plan": [
        {"action": "click", "target": "firefox", "location": [100, 50]},
        {"action": "wait", "seconds": 2},
        {"action": "type", "text": "google.com"},
        {"action": "key", "key": "Return"}
    ],
    "description": "Open Firefox and navigate to Google",
    "estimated_time": 5
}
```

#### Error
```json
{
    "success": false,
    "error": "Plan rejected by validators",
    "plan": { ... }
}
```

---

## Action Types

### click
Click at screen coordinates.

```json
{
    "action": "click",
    "target": "button_name",  // Optional description
    "location": [x, y],       // Required coordinates
    "button": "left"          // Optional: left, right, middle
}
```

### type
Type text using keyboard.

```json
{
    "action": "type",
    "text": "hello world"
}
```

### key
Press a key or key combination.

```json
{
    "action": "key",
    "key": "Return"  // Key name or combo like "ctrl+c"
}
```

**Common key names:**
- `Return`, `Escape`, `Tab`, `BackSpace`, `Delete`
- `Up`, `Down`, `Left`, `Right`
- `Home`, `End`, `Page_Up`, `Page_Down`
- `F1` through `F12`
- `space`, `plus`, `minus`
- Modifiers: `ctrl`, `alt`, `shift`, `super`
- Combos: `ctrl+c`, `alt+F4`, `ctrl+shift+s`

### wait
Pause execution.

```json
{
    "action": "wait",
    "seconds": 2.5
}
```

### drag
Drag from one point to another.

```json
{
    "action": "drag",
    "start": [100, 100],
    "end": [200, 200]
}
```

---

## Python API

### Config

```python
from core.ai_engine.config import Config

config = Config("config/cosmic-os.conf")

# Get string value
tier = config.get("AI", "tier", fallback="auto")

# Get boolean
debug = config.get_boolean("Development", "debug_mode", fallback=False)

# Get integer
width = config.get_int("GUI", "sidebar_width", fallback=400)

# Get list
validators = config.get_list("AI", "validator_models")
```

### ModelManager

```python
from core.ai_engine.config import Config
from core.ai_engine.model_manager import ModelManager

config = Config()
manager = ModelManager(config)

# Detected tier (1, 2, or 3)
print(manager.tier)

# Load models
manager.load_models()
manager.load_validators()

# Access loaded model
model = manager.main_model
validators = manager.validator_models
```

### CommandGenerator

```python
from core.ai_engine.command_generator import CommandGenerator

generator = CommandGenerator(model)  # or None for fallback

# Generate plan
plan = generator.generate("open firefox")
# Returns dict with 'plan', 'description', 'estimated_time'

# With screen context
plan = generator.generate("click the search button", screen_context={
    "resolution": (1920, 1080),
    "active_window": "Firefox"
})
```

### CommandValidator

```python
from core.ai_engine.command_validator import CommandValidator

validator = CommandValidator(validator_models)

# Validate plan
if validator.approve_all(plan):
    print("Plan approved")
else:
    print("Plan rejected")
```

### Executor

```python
from core.ai_engine.executor import Executor

executor = Executor()

# Execute plan
result = executor.execute(plan)
# Returns {"success": True/False, "error": "...", "failed_step": {...}}
```

### ScreenController

```python
from core.automation.screen_controller import ScreenController

screen = ScreenController(dry_run=False)

# Mouse
screen.mouse_move(100, 200)
screen.mouse_click(1)  # Left click
screen.mouse_down(1)
screen.mouse_up(1)
x, y = screen.get_mouse_location()

# Keyboard
screen.type_text("hello", delay_ms=50)
screen.key_press("Return")
screen.key_press("ctrl+c")

# Screen info
width, height = screen.get_screen_resolution()

# Screenshot
path = screen.take_screenshot("/tmp/screenshot.png")

# Window info
window_id = screen.get_active_window()
name = screen.get_active_window_name()
```

### ActionPrimitives

```python
from core.automation.screen_controller import ScreenController
from core.automation.action_primitives import ActionPrimitives, MouseButton

screen = ScreenController()
actions = ActionPrimitives(screen)

# Click
result = actions.click(100, 100)
result = actions.double_click(100, 100)
result = actions.right_click(100, 100)

# Type
result = actions.type_text("hello", delay=0.05, clear_first=False)

# Keys
result = actions.press_key("Return")
result = actions.key_combo(["ctrl", "c"])

# Wait
result = actions.wait(1.5)

# Drag
result = actions.drag(100, 100, 200, 200)

# Scroll
result = actions.scroll("down", amount=3)

# Screenshot
result = actions.take_screenshot("/tmp/shot.png")

# Check result
if result.success:
    print(result.message)
else:
    print(f"Error: {result.message}")
```

### WindowManager

```python
from core.automation.screen_controller import ScreenController
from core.automation.window_manager import WindowManager

screen = ScreenController()
wm = WindowManager(screen)

# Find windows
windows = wm.find_window_by_name("Firefox")
windows = wm.find_window_by_class("firefox")

# Get window info
info = wm.get_window_info(window_id)
print(info.name, info.x, info.y, info.width, info.height)

# Active window
window_id = wm.get_active_window()
info = wm.get_active_window_info()

# List all windows
all_windows = wm.list_windows()

# Window operations
wm.focus_window(window_id)
wm.minimize_window(window_id)
wm.maximize_window(window_id)
wm.close_window(window_id)
wm.move_window(window_id, 100, 100)
wm.resize_window(window_id, 800, 600)

# Desktop operations
current = wm.get_current_desktop()
wm.switch_desktop(1)
wm.move_window_to_desktop(window_id, 2)

# Launch app
window_id = wm.launch_application("firefox", wait_for_window=True)
```

### CosmicAI (Main Entry Point)

```python
from core.ai_engine.main import CosmicAI

ai = CosmicAI()

# Process request (generate plan)
plan = ai.process_request("open firefox")

# Execute approved plan
result = ai.execute_plan_request(plan)

# Start daemon
ai.start()  # Blocks, runs IPC server

# Stop daemon
ai.stop()
```

---

## Configuration Reference

### cosmic-os.conf

```ini
[General]
version = 0.1.0
first_run = true

[AI]
tier = auto                    # auto, 1, 2, or 3
main_model_path = core/ai_engine/models/tier2/model.gguf
validator_models = ["safety", "logic", "efficiency"]
max_tokens = 512
temperature = 0.7

[GUI]
hotkey = Ctrl+Space
sidebar_width = 400
sidebar_animation_speed = 200
theme = cosmic-dark

[Automation]
click_delay = 0.1              # Seconds between actions
type_delay = 0.05              # Seconds between keystrokes
screenshot_on_error = true
max_retries = 3

[Permissions]
allow_file_operations = true
allow_network_access = true
allow_system_settings = false
require_confirmation = true

[Development]
hot_reload = false
debug_mode = false
log_level = INFO               # DEBUG, INFO, WARNING, ERROR
```

---

## Error Codes

| Error | Description |
|-------|-------------|
| `model_not_found` | AI model file not found |
| `validation_failed` | Plan rejected by validators |
| `execution_failed` | Action execution error |
| `ipc_error` | Communication error |
| `permission_denied` | Action not allowed by permissions |
| `xdotool_unavailable` | xdotool not installed |

---

## Events

The GUI sidebar emits these signals:

| Signal | Parameters | Description |
|--------|------------|-------------|
| `messageSubmitted` | `text: str` | User submitted message |
| `planApproved` | `plan: dict` | User approved plan |
| `planDenied` | | User denied plan |
| `sidebarOpened` | | Sidebar became visible |
| `sidebarClosed` | | Sidebar was hidden |
