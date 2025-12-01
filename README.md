# AgentOS

**An AI-first Operating System where the agent is the kernel.**

AgentOS is a research project to build a Linux-based OS designed from the ground up for AI agents. Unlike traditional OSs where AI is an app, in AgentOS, the AI has deep system integration, capable of seeing the screen, controlling inputs, and managing the system.

## 🚀 Quick Start for AI Agents (and Humans)

If you are an AI agent or a human developer wanting to get started immediately, follow these steps.

### 1. Python Agent (Local Development)
**Best for:** Developing the agent logic, testing LLM integration.
**Prerequisites:** Python 3.10+

```bash
# 1. Clone the repository (if you haven't already)
# git clone <repo_url>
# cd AgentOS

# 2. Install dependencies
make install

# 3. Run tests
make test
```

### 2. Full OS Simulation (VirtualBox)
**Best for:** Testing the OS integration, screen capture, and boot process.
**Prerequisites:** VirtualBox, Make.

```bash
# 1. Automated Setup (Creates VM, installs Debian + Agent)
make setup-os
```

### 3. Custom OS Build (Buildroot)
**Best for:** Creating the final minimal ISO for distribution.
**Prerequisites:** Linux host, Buildroot dependencies (gcc, make, etc.)

```bash
# 1. Build the custom ISO
make build-custom-os

# 2. Test the ISO in a VM
make test-custom-os
```

## 📂 Project Structure

- `src/agent/`: The core Python agent code.
- `scripts/`: Helper scripts for setup, building, and testing.
- `tests/`: Pytest suite.
- `buildroot/`: Buildroot source and configuration for the custom OS.
- `iso-build/`: Live-build configuration for Debian-based ISO.
- `docs/`: Detailed documentation.

## 📚 Documentation

- [Project Status & Roadmap](PROJECT_STATUS.md) - **Start Here for Context**
- [Custom OS Build Guide](CUSTOM_OS_BUILD.md)
- [Automated Setup Guide](AUTOMATED_SETUP.md)
- [Contributing](CONTRIBUTING.md)

## 🛠️ Development

- **Testing**: `make test` runs the fast local tests.
- **Linting**: Ensure code is clean and readable.
- **Virtual Environment**: `make install` creates a `.venv` for you.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
