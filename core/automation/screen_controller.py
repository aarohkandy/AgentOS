"""
Screen Controller for Cosmic OS
Wrapper around xdotool with error handling and screen utilities.
"""

import subprocess
import shutil
import logging
import os
from typing import Optional, Tuple, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ScreenController:
    """
    Low-level wrapper around xdotool for X11 GUI automation.
    Provides mouse, keyboard, and window control primitives.
    """

    def __init__(self, dry_run: bool = False):
        """
        Initialize screen controller.
        
        Args:
            dry_run: If True, log commands instead of executing
        """
        self.dry_run = dry_run
        self.xdotool_path = shutil.which("xdotool")
        self.scrot_path = shutil.which("scrot")
        self.xrandr_path = shutil.which("xrandr")
        
        if not self.xdotool_path:
            logger.warning("xdotool not found. Install with: sudo apt install xdotool")
        
        self._screen_resolution: Optional[Tuple[int, int]] = None

    def _run_xdotool(self, *args: str) -> str:
        """
        Execute an xdotool command.
        
        Args:
            *args: Command arguments
            
        Returns:
            Command output as string
            
        Raises:
            RuntimeError: If command fails
        """
        if not self.xdotool_path:
            raise RuntimeError("xdotool not available")
        
        cmd = [self.xdotool_path] + list(args)
        
        if self.dry_run:
            logger.info(f"[DRY RUN] {' '.join(cmd)}")
            return ""
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool failed: {e.stderr}")
            raise RuntimeError(f"xdotool command failed: {e.stderr}")

    def _run_shell(self, cmd: str) -> str:
        """Run a shell command and return output."""
        if self.dry_run:
            logger.info(f"[DRY RUN] {cmd}")
            return ""
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Shell command failed: {e.stderr}")
            raise RuntimeError(f"Shell command failed: {e.stderr}")

    # ===== Mouse Controls =====

    def mouse_move(self, x: int, y: int) -> None:
        """Move mouse to absolute coordinates."""
        self._run_xdotool("mousemove", str(x), str(y))

    def mouse_move_relative(self, dx: int, dy: int) -> None:
        """Move mouse relative to current position."""
        self._run_xdotool("mousemove_relative", str(dx), str(dy))

    def mouse_click(self, button: int = 1) -> None:
        """
        Click mouse button.
        
        Args:
            button: 1=left, 2=middle, 3=right, 4=scroll up, 5=scroll down
        """
        self._run_xdotool("click", str(button))

    def mouse_down(self, button: int = 1) -> None:
        """Press mouse button down."""
        self._run_xdotool("mousedown", str(button))

    def mouse_up(self, button: int = 1) -> None:
        """Release mouse button."""
        self._run_xdotool("mouseup", str(button))

    def get_mouse_location(self) -> Tuple[int, int]:
        """Get current mouse position."""
        output = self._run_xdotool("getmouselocation")
        # Output format: x:123 y:456 screen:0 window:12345678
        parts = output.split()
        x = int(parts[0].split(":")[1])
        y = int(parts[1].split(":")[1])
        return x, y

    # ===== Keyboard Controls =====

    def type_text(self, text: str, delay_ms: int = 50) -> None:
        """
        Type text with keyboard.
        
        Args:
            text: Text to type
            delay_ms: Delay between keystrokes in milliseconds
        """
        # Escape special characters for xdotool
        # xdotool handles most chars, but we need to be careful with shell
        self._run_xdotool("type", "--delay", str(delay_ms), "--", text)

    def key_press(self, key: str) -> None:
        """
        Press and release a key or key combination.
        
        Args:
            key: Key name like 'Return', 'Escape', 'ctrl+c', 'alt+F4'
        """
        self._run_xdotool("key", key)

    def key_down(self, key: str) -> None:
        """Press and hold a key."""
        self._run_xdotool("keydown", key)

    def key_up(self, key: str) -> None:
        """Release a held key."""
        self._run_xdotool("keyup", key)

    # ===== Screen Information =====

    def get_screen_resolution(self, force_refresh: bool = False) -> Tuple[int, int]:
        """
        Get current screen resolution.
        
        Args:
            force_refresh: Force re-detection instead of using cached value
            
        Returns:
            Tuple of (width, height)
        """
        if self._screen_resolution and not force_refresh:
            return self._screen_resolution
        
        if not self.xrandr_path:
            logger.warning("xrandr not found, using fallback resolution")
            return (1920, 1080)
        
        try:
            output = self._run_shell("xrandr | grep '\\*' | head -1")
            # Output like: "   1920x1080     60.00*+"
            resolution = output.strip().split()[0]
            width, height = resolution.split("x")
            self._screen_resolution = (int(width), int(height))
            return self._screen_resolution
        except Exception as e:
            logger.warning(f"Failed to detect resolution: {e}")
            return (1920, 1080)

    def get_display_info(self) -> dict:
        """Get detailed display information."""
        width, height = self.get_screen_resolution()
        return {
            "width": width,
            "height": height,
            "center_x": width // 2,
            "center_y": height // 2,
        }

    # ===== Screenshot =====

    def take_screenshot(
        self,
        filepath: Optional[str] = None,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> str:
        """
        Take a screenshot.
        
        Args:
            filepath: Path to save screenshot (default: timestamped in /tmp)
            region: Optional (x, y, width, height) to capture specific region
            
        Returns:
            Path to saved screenshot
        """
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path.home() / ".local/share/cosmic-os/screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            filepath = str(screenshot_dir / f"cosmic_{timestamp}.png")
        
        if self.scrot_path:
            if region:
                x, y, w, h = region
                # Use import from imagemagick for region capture
                cmd = f"import -window root -crop {w}x{h}+{x}+{y} {filepath}"
            else:
                cmd = f"{self.scrot_path} {filepath}"
            self._run_shell(cmd)
        else:
            # Fallback using xdotool + import
            try:
                self._run_shell(f"import -window root {filepath}")
            except Exception:
                logger.error("No screenshot tool available. Install scrot or imagemagick.")
                raise RuntimeError("No screenshot tool available")
        
        return filepath

    # ===== Utility Methods =====

    def wait_for_idle(self, timeout: int = 5) -> bool:
        """
        Wait for the system to become idle (no pending events).
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if system became idle, False if timeout
        """
        try:
            self._run_xdotool("sleep", str(timeout))
            return True
        except Exception:
            return False

    def get_active_window(self) -> Optional[int]:
        """Get the window ID of the currently active window."""
        try:
            output = self._run_xdotool("getactivewindow")
            return int(output)
        except Exception:
            return None

    def get_active_window_name(self) -> Optional[str]:
        """Get the name/title of the currently active window."""
        try:
            window_id = self.get_active_window()
            if window_id:
                return self._run_xdotool("getwindowname", str(window_id))
            return None
        except Exception:
            return None

    def sync(self) -> None:
        """Synchronize with X server (wait for pending commands to complete)."""
        self._run_xdotool("sync")
