# Building ANOS ISO

## Prerequisites

Install required tools:

**On Arch Linux:**
```bash
sudo pacman -S wget curl 7zip xorriso cdrtools rsync squashfs-tools grub syslinux
```

**On Ubuntu/Debian:**
```bash
sudo apt install wget curl p7zip-full xorriso genisoimage rsync squashfs-tools grub-pc-bin grub-efi-amd64-bin isolinux syslinux-utils
```

## Build Process

1. **Run the builder:**
   ```bash
   ./build-anos-iso.sh
   ```

2. **The script will:**
   - Check prerequisites
   - Download Ubuntu 24.04 Server ISO (~1-2GB)
   - Extract filesystem
   - Install minimal packages
   - Install Cosmic OS
   - Apply ANOS branding
   - Configure Calamares
   - Build final ISO

3. **Output:**
   - ISO file: `anos-YYYYMMDD-HHMMSS.iso`
   - Build log: `anos-build/build.log`

## Using the ISO

1. Boot from the ISO in VirtualBox or physical machine
2. Calamares installer will launch automatically
3. Follow the installer (only prompts for username, password, language)
4. After installation, reboot and log in
5. Cosmic OS will be ready to use (press Ctrl+Space)

## Troubleshooting

- **Build fails**: Check `anos-build/build.log`
- **Missing tools**: Install prerequisites listed above
- **Disk space**: Need 20GB+ free space
- **Download fails**: Check internet connection

## Customization

Before building, you can:
- Edit `packages/base.list` to add/remove packages
- Replace `assets/` files with your ANOS branding
- Modify `installer/calamares/` configuration
- Adjust `cosmic-integration/` scripts




