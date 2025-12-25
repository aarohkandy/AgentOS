# Cosmic OS Architecture

## Overview

Cosmic OS is an AI-integrated desktop overlay for Ubuntu/Kubuntu that provides natural language control of the desktop through GUI automation. The system features a three-tier AI model system with safety validation and a hot-reload development environment.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    AI Sidebar (Qt/QML)                   │    │
│  │  - Triggered by Ctrl+Space                               │    │
│  │  - Chat interface with message history                   │    │
│  │  - Command plan preview with approve/deny                │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ IPC (D-Bus / Unix Socket)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AI ENGINE                                 │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │ Model Manager │──│  Command     │──│   Command         │    │
│  │ (3-tier)      │  │  Generator   │  │   Validator (3x)  │    │
│  └───────────────┘  └──────────────┘  └───────────────────┘    │
│                                               │                  │
│                                               ▼                  │
│                                       ┌───────────────┐         │
│                                       │   Executor    │         │
│                                       └───────────────┘         │
└───────────────────────────────────────────────┬─────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AUTOMATION LAYER                             │
│  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │ Screen Controller│  │ Window Manager  │  │ Accessibility │  │
│  │ (xdotool)        │  │ (xdotool/wmctrl)│  │ (AT-SPI2)     │  │
│  └──────────────────┘  └─────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DESKTOP ENVIRONMENT                          │
│                      KDE Plasma (X11)                            │
│                      + Latte Dock                                │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. AI Engine (`core/ai_engine/`)

The brain of Cosmic OS, responsible for understanding user requests and generating executable plans.

#### Model Manager (`model_manager.py`)
- Detects hardware capabilities (RAM, GPU)
- Selects appropriate AI tier:
  - **Tier 1**: <8GB RAM → SmolLM 1.7B / Phi-3 Mini
  - **Tier 2**: 8-16GB RAM → Qwen2.5 3B / Llama 3.2 3B
  - **Tier 3**: >16GB RAM or GPU → Qwen2.5 7B / Llama 3.1 8B
- Loads GGUF models via llama-cpp-python
- Manages GPU offloading for tier 3

#### Command Generator (`command_generator.py`)
- Converts natural language to GUI action sequences
- Uses structured JSON output format
- Prompt-engineered to output only GUI actions
- Context includes screen resolution and available apps

**Output Format:**
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

#### Command Validator (`command_validator.py`)
Three validation layers, each using a tiny model (<1B params):

1. **Safety Validator**
   - Blocks destructive commands (rm -rf, mkfs, dd, etc.)
   - Prevents closing critical system apps
   - Uses heuristic blacklist + AI validation

2. **Logic Validator**
   - Verifies command sequence makes sense
   - Checks prerequisites (app installed, window exists)
   - Validates timing (no negative waits)

3. **Efficiency Validator**
   - Suggests faster alternatives
   - Removes redundant steps
   - Optimizes wait times (soft pass)

#### Executor (`executor.py`)
- Executes validated command plans
- Interfaces with automation layer
- Supports pause/resume/cancel
- Takes screenshots on error

#### IPC Server (`ipc_server.py`)
- Primary: D-Bus service (`com.cosmicos.ai`)
- Fallback: Unix socket (`/tmp/cosmic-ai.sock`)
- Async communication to prevent UI blocking
- JSON message format

### 2. Automation Layer (`core/automation/`)

Provides low-level GUI control primitives.

#### Screen Controller (`screen_controller.py`)
Wrapper around xdotool for X11 automation:
- Mouse movement and clicks
- Keyboard input simulation
- Screen resolution detection
- Screenshot capture

#### Window Manager (`window_manager.py`)
Window detection and manipulation:
- Find windows by name/class/PID
- Focus, minimize, maximize, close
- Move and resize windows
- Desktop/workspace management

#### Accessibility (`accessibility.py`)
Future AT-SPI2 integration for semantic GUI interaction:
- Find elements by name/role
- Interact with UI semantically
- More robust than coordinate-based

### 3. GUI Layer (`core/gui/`)

User-facing interface components.

#### Sidebar (`sidebar.py`)
Main interaction interface:
- Slides in from right side
- Chat-style message interface
- Command plan preview
- Approve/deny buttons
- Settings access

#### Setup Wizard (`setup_wizard.py`)
First-boot experience:
- Hardware detection
- Tier selection
- Permission configuration
- Model download

#### Settings Panel (`settings_panel.py`)
Configuration interface:
- AI model settings
- Permission management
- Automation timing
- Development options

### 4. System Configuration (`core/system-config/`)

KDE Plasma and system setup scripts.

- **kde-plasma-setup.sh**: Full Plasma customization
- **latte-dock-config.sh**: iOS-like dock setup
- **theme-setup.sh**: Dark theme installation
- **systemd/**: Service files for daemon
- **plasma-configs/**: KDE configuration files

## Data Flow

### Request Processing

```
1. User Input (Ctrl+Space → "open firefox")
         │
         ▼
2. Sidebar sends to AI Engine via IPC
         │
         ▼
3. Command Generator creates plan
         │
         ▼
4. Validators check plan (safety, logic, efficiency)
         │
         ▼
5. Plan returned to Sidebar for preview
         │
         ▼
6. User approves → Executor runs plan
         │
         ▼
7. Automation layer performs GUI actions
```

### Safety Pipeline

```
Plan → Safety Validator → Logic Validator → Efficiency Validator → Approved/Rejected
         │                    │                    │
         │ Blocks             │ Blocks             │ Suggests
         │ dangerous          │ illogical          │ improvements
         │ commands           │ sequences          │ (soft pass)
```

## Key Design Decisions

### Why Three Tiers?
- Ensures Cosmic OS works on any hardware
- Better user experience on capable systems
- Automatic detection removes setup friction

### Why Three Validators?
- Defense in depth against dangerous commands
- Separation of concerns (safety ≠ logic)
- Small models for fast validation (<500ms total)

### Why xdotool over Terminal Commands?
- Users see familiar GUI actions
- More intuitive behavior
- Future migration to AT-SPI2
- Aligns with "zero terminal" philosophy

### Why Hot-Reload Development?
- 10-30 second iteration time
- Test on real KDE environment in VM
- Host code changes auto-sync to VM
- Rapid experimentation

## Security Model

1. **Validator Chain**: All commands pass through 3 validators
2. **Heuristic Blacklist**: Known dangerous patterns blocked
3. **User Confirmation**: Plans shown before execution
4. **Permission System**: Configurable capabilities
5. **Safe Mode**: Preview-only option
6. **Blocked Paths**: System directories protected

## Future Enhancements

- AT-SPI2 accessibility backend
- Multi-monitor support
- Wayland compatibility
- Voice activation
- Screen understanding (vision model)
- Plugin system for custom actions
