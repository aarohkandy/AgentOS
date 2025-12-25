# Cosmic OS ISO Builder

This script creates a bootable ISO file with Cosmic OS pre-installed, ready to use in Oracle VirtualBox.

## Quick Start

```bash
./build-iso.sh
```

## Requirements

- **Disk Space**: ~15GB free space
- **Time**: 30-60 minutes (depending on internet speed)
- **Permissions**: sudo access required
- **OS**: Linux (Arch, Ubuntu, or similar)

## What It Does

1. **Downloads** Kubuntu 24.04 LTS ISO (~4.5GB)
2. **Extracts** the ISO filesystem
3. **Installs** Cosmic OS and all dependencies in a chroot environment
4. **Configures** first-boot setup scripts
5. **Repackages** everything into a bootable ISO

## Output

The script creates a single ISO file:
- `cosmic-os-YYYYMMDD-HHMMSS.iso`
- Ready to boot in VirtualBox
- Cosmic OS pre-installed and configured
- First-boot wizard will run automatically

## Using the ISO in VirtualBox

1. Open VirtualBox
2. Create new VM:
   - Type: Linux
   - Version: Ubuntu (64-bit)
   - RAM: 4GB minimum (8GB+ recommended)
   - Storage: 20GB+ (dynamically allocated)
3. Settings → Storage → Controller IDE → Add Optical Drive
4. Select the generated ISO file
5. Boot the VM
6. Install normally (or try live mode)
7. After installation, Cosmic OS is ready!
8. Press **Ctrl+Space** to open the AI sidebar

## Build Process

The script shows live progress for:
- Download progress (percentage)
- File copying operations
- Package installation
- Filesystem compression
- ISO creation

All output is also logged to `iso-build/build.log`

## Troubleshooting

### Out of disk space
- Free up at least 15GB
- The script checks available space before starting

### Missing tools
- The script will try to install missing dependencies automatically
- On Arch: `sudo pacman -S wget curl p7zip xorriso cdrtools rsync debootstrap squashfs-tools grub isolinux syslinux`
- On Ubuntu: `sudo apt install wget curl p7zip-full xorriso genisoimage rsync debootstrap squashfs-tools grub-pc-bin grub-efi-amd64-bin isolinux syslinux-utils`

### Build fails
- Check `iso-build/build.log` for detailed error messages
- Ensure you have sudo permissions
- Try cleaning: `sudo rm -rf iso-build/` and run again

## Customization

To modify what gets installed, edit the `chroot-install.sh` section in `build-iso.sh` (around line 232).

## Notes

- The first boot will automatically configure KDE Plasma
- Cosmic AI service starts automatically after login
- Models are not included (download on first use or pre-download)
- The ISO is ~4-5GB in size






