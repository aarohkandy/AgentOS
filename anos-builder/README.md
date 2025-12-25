# ANOS Operating System Builder

Custom Linux distribution based on Ubuntu 24.04 with Cosmic OS pre-installed.

## Quick Start

```bash
cd anos-builder
./build-anos-iso.sh
```

## What It Does

1. Downloads Ubuntu 24.04 Server ISO (minimal base)
2. Extracts and modifies the filesystem
3. Installs minimal packages (KDE Plasma core, Calamares)
4. Pre-installs Cosmic OS
5. Applies ANOS branding
6. Creates bootable ISO with Calamares installer

## Features

- **Minimal Base**: Only essential packages
- **Custom Branding**: ANOS branding throughout (replace assets/ when ready)
- **Calamares Installer**: Streamlined installation
- **Automated Setup**: Only prompts for username, password, and language
- **Cosmic OS Pre-installed**: Ready to use after installation

## Directory Structure

- `build-anos-iso.sh` - Main builder script
- `packages/` - Package lists (base.list, remove.list)
- `cosmic-integration/` - Cosmic OS installation scripts
- `installer/calamares/` - Calamares configuration
- `branding/` - ANOS branding files
- `assets/` - Visual assets (logos, wallpapers - placeholders for now)

## Customization

Replace files in `assets/` with your ANOS symbol and branding:
- `assets/logo.png` - ANOS logo
- `assets/splash.png` - Boot splash
- `assets/wallpaper.png` - Desktop wallpaper

## Requirements

- 20GB+ free disk space
- sudo access
- Linux system (Arch/Ubuntu)
- Internet connection

## Build Time

- 30-60 minutes (depending on internet speed)




