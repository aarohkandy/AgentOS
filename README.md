# 🌌 Cosmic OS

**AI-Integrated Desktop Experience for Linux**

Cosmic OS is an AI-powered desktop overlay that brings natural language control to your Linux desktop. Talk to your computer and watch it perform actions through actual GUI interactions.

![Cosmic OS](docs/images/cosmic-os-banner.png)

## ✨ Features

- **🎯 Natural Language Control**: Tell your computer what to do in plain English
- **👁️ Visual AI Sidebar**: Beautiful slide-in interface triggered by Ctrl+Space
- **🛡️ Triple Safety Validation**: 3 AI validators check every command before execution
- **⚡ Ultra-Fast Development**: Hot-reload system with 10-30 second iteration time
- **🎨 iOS-Inspired Design**: Clean, minimal KDE Plasma experience with Latte Dock
- **🔒 Privacy First**: All processing happens locally, nothing leaves your machine

## 🖥️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 24.04 LTS | Kubuntu 24.04 LTS |
| RAM | 4GB (Tier 1) | 16GB+ (Tier 3) |
| Storage | 5GB | 15GB |
| Display | X11 | X11 |

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/cosmic-os/cosmic-os.git
cd cosmic-os

# Run installer
sudo ./install.sh

# Reboot and enjoy!
```

After installation, press **Ctrl+Space** to open the AI sidebar.

## 💬 Usage

Simply type what you want to do:

```
"Open Firefox and go to github.com"
"Search for cats in the file manager"
"Take a screenshot and save it to Desktop"
"Close all windows"
```

The AI will show you a command plan before executing. Review it and click Approve to proceed.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          AI Sidebar (Qt/QML)            │
└─────────────────┬───────────────────────┘
                  │ IPC
┌─────────────────▼───────────────────────┐
│              AI Engine                   │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐  │
│  │Generator│→│Validators│→│ Executor │  │
│  └─────────┘ └──────────┘ └──────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Automation Layer                 │
│      (xdotool / AT-SPI2)                │
└─────────────────────────────────────────┘
```

## 🤖 AI Tiers

Cosmic OS automatically selects the best model for your hardware:

| Tier | Hardware | Models | RAM Usage |
|------|----------|--------|-----------|
| 1 | <8GB RAM | SmolLM 1.7B, Phi-3 Mini | ~2GB |
| 2 | 8-16GB RAM | Qwen2.5 3B, Llama 3.2 3B | ~4GB |
| 3 | >16GB / GPU | Qwen2.5 7B, Llama 3.1 8B | ~8GB |

## 🛡️ Safety

Every command goes through three safety validators:

1. **Safety Validator**: Blocks dangerous commands (rm -rf, mkfs, etc.)
2. **Logic Validator**: Verifies command sequences make sense
3. **Efficiency Validator**: Suggests optimizations

You always see the plan before execution and must approve it.

## 📁 Project Structure

```
cosmic-os/
├── core/
│   ├── ai_engine/      # AI processing
│   ├── automation/     # GUI control
│   ├── gui/           # User interface
│   └── system-config/ # KDE setup
├── scripts/           # Utilities
├── config/           # Configuration
├── tests/            # Test suite
└── docs/             # Documentation
```

## 🔧 Development

For contributors and developers:

```bash
# Setup development environment
./dev-setup.sh

# Quick test (starts AI daemon + sidebar without full install)
./scripts/start-cosmic-test.sh

# Or ultra-simple version
./scripts/quick-test.sh

# Run tests
python3 scripts/test-ai.py

# Start hot-reload
./scripts/dev-sync.sh
```

See [Development Guide](docs/DEVELOPMENT.md) for complete instructions.

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Development](docs/DEVELOPMENT.md) - Contributing and development setup
- [API Reference](docs/API.md) - Complete API documentation
- [User Guide](docs/USER_GUIDE.md) - End-user documentation

## 🗺️ Roadmap

- [ ] Wayland support
- [ ] Multi-monitor support
- [ ] Voice activation
- [ ] Screen understanding (vision)
- [ ] Plugin system
- [ ] More desktop environments

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit PRs.

1. Fork the repository
2. Create your feature branch
3. Make changes and test
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Efficient LLM inference
- [xdotool](https://github.com/jordansissel/xdotool) - X11 automation
- [KDE Plasma](https://kde.org/plasma-desktop/) - Desktop environment
- [Latte Dock](https://github.com/KDE/latte-dock) - Beautiful dock

---

**Made with ❤️ for the Linux desktop**
