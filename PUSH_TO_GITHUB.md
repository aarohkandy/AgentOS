# Push ANOS to GitHub

## Quick Steps

1. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Name it: `anos` (or whatever you prefer)
   - Don't initialize with README/license
   - Click "Create repository"

2. **Push your code:**
   ```bash
   cd /home/a_a_k/Downloads/agentOS
   
   # Add your GitHub repo as remote
   git remote add origin https://github.com/YOUR_USERNAME/anos.git
   
   # Rename branch to main
   git branch -M main
   
   # Push to GitHub
   git push -u origin main
   ```

3. **If you need to authenticate:**
   - Use a Personal Access Token (not password)
   - Or use SSH: `git remote set-url origin git@github.com:YOUR_USERNAME/anos.git`

## What's Included

- `anos-builder/` - Complete ANOS builder system
  - `build-anos-iso.sh` - Main builder script
  - `installer/` - Calamares configuration
  - `branding/` - ANOS branding files
  - `packages/` - Package lists
  - `cosmic-integration/` - Cosmic OS installation scripts
  - `assets/` - Visual assets (placeholders)

- `core/` - Cosmic OS core files
- `config/` - Configuration files
- `scripts/` - Utility scripts
- `docs/` - Documentation

## Build Status

The build process was interrupted during squashfs compression. The builder has been updated to use faster gzip compression instead of xz.

To complete the build:
```bash
cd anos-builder
./resume-build.sh
```

Or start fresh:
```bash
cd anos-builder
./build-anos-iso.sh
```

