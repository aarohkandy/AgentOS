"""
Global Hotkey Handler for Cosmic OS Sidebar
Uses DBus to register system-wide hotkeys that work even when app doesn't have focus.
"""

import logging
import subprocess
import shutil
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class GlobalHotkeyHandler:
    """Handles global hotkey registration using system services."""
    
    def __init__(self, callback: Callable[[], None], hotkey: str = "Super+Shift"):
        """
        Initialize global hotkey handler.
        
        Args:
            callback: Function to call when hotkey is pressed
            hotkey: Hotkey combination (e.g., "Super+Shift")
        """
        self.callback = callback
        self.hotkey = hotkey
        self.registered = False
        self.qdbus = shutil.which("qdbus")
        self.kwriteconfig5 = shutil.which("kwriteconfig5")
        
    def register(self) -> bool:
        """Register the global hotkey with the system."""
        if self.registered:
            return True
            
        # Try KDE method first (most reliable)
        if self._register_kde():
            self.registered = True
            logger.info(f"Global hotkey registered via KDE: {self.hotkey}")
            return True
        
        # Fallback: Try using xdotool to monitor keys (less reliable)
        if self._register_xdotool():
            self.registered = True
            logger.info(f"Global hotkey registered via xdotool: {self.hotkey}")
            return True
        
        logger.warning("Could not register global hotkey. Sidebar will need to be triggered manually.")
        return False
    
    def _register_kde(self) -> bool:
        """Register hotkey using KDE's global shortcuts system."""
        if not self.kwriteconfig5:
            return False
        
        try:
            # Register with KDE global shortcuts
            result = subprocess.run(
                [
                    self.kwriteconfig5,
                    "--file", "kglobalshortcutsrc",
                    "--group", "cosmic-ai",
                    "--key", "toggle-sidebar",
                    f"Meta+Shift,Meta+Shift,Toggle Cosmic AI Sidebar"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Reload KDE shortcuts
                try:
                    subprocess.run(["qdbus", "org.kde.kglobalaccel", "/kglobalaccel", "org.kde.KGlobalAccel.reloadConfig"], 
                                 timeout=2, capture_output=True)
                except:
                    pass
                return True
        except Exception as e:
            logger.debug(f"KDE hotkey registration failed: {e}")
        
        return False
    
    def _register_xdotool(self) -> bool:
        """Fallback: Monitor keys using xdotool (less reliable)."""
        # This is a fallback - xdotool can't truly do global hotkeys
        # but we can at least try
        return False
    
    def unregister(self):
        """Unregister the global hotkey."""
        if not self.registered:
            return
        
        try:
            if self.kwriteconfig5:
                subprocess.run(
                    [
                        self.kwriteconfig5,
                        "--file", "kglobalshortcutsrc",
                        "--group", "cosmic-ai",
                        "--delete", "toggle-sidebar"
                    ],
                    timeout=5,
                    capture_output=True
                )
        except Exception as e:
            logger.debug(f"Failed to unregister hotkey: {e}")
        
        self.registered = False

