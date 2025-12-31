"""
Global Hotkey Handler for Cosmic OS
Handles system-level keyboard shortcuts that work even when app doesn't have focus.
Uses multiple methods for cross-platform compatibility.
"""

import logging
import subprocess
import shutil
import sys
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class GlobalHotkey:
    """System-level global hotkey handler."""
    
    def __init__(self, callback: Callable):
        """
        Initialize global hotkey handler.
        
        Args:
            callback: Function to call when hotkey is pressed
        """
        self.callback = callback
        self.active = False
        self.method = None
        
    def register(self, key_combination: str = "Meta+Shift") -> bool:
        """
        Register global hotkey.
        
        Args:
            key_combination: Key combination (e.g., "Meta+Shift", "Ctrl+Space")
            
        Returns:
            True if registration successful
        """
        # Try different methods based on platform and available tools
        methods = [
            self._try_kde_shortcut,
            self._try_xdotool_daemon,
            self._try_python_pynput,
        ]
        
        for method in methods:
            try:
                if method(key_combination):
                    self.active = True
                    logger.info(f"Global hotkey registered using {method.__name__}")
                    return True
            except Exception as e:
                logger.debug(f"Hotkey method {method.__name__} failed: {e}")
                continue
        
        logger.warning("Could not register global hotkey. Using fallback (app must have focus)")
        return False
    
    def _try_kde_shortcut(self, key_combination: str) -> bool:
        """Try using KDE's global shortcuts (kwriteconfig5)."""
        if not shutil.which("kwriteconfig5"):
            return False
        
        try:
            # Register with KDE
            subprocess.run(
                ["kwriteconfig5", "--file", "kglobalshortcutsrc",
                 "--group", "cosmic-ai",
                 "--key", "toggle-sidebar",
                 f"{key_combination},{key_combination},Toggle Cosmic AI Sidebar"],
                check=True,
                capture_output=True,
                timeout=5
            )
            
            # Reload KDE shortcuts
            subprocess.run(
                ["qdbus", "org.kde.kglobalaccel", "/kglobalaccel", "reloadConfig"],
                check=False,
                timeout=5
            )
            
            logger.info("KDE global shortcut registered")
            return True
        except Exception:
            return False
    
    def _try_xdotool_daemon(self, key_combination: str) -> bool:
        """Try using xdotool in daemon mode (Linux X11)."""
        if not shutil.which("xdotool"):
            return False
        
        # xdotool doesn't have a great daemon mode, so this is limited
        # We'd need a separate process watching for key combinations
        return False
    
    def _try_python_pynput(self, key_combination: str) -> bool:
        """Try using pynput library for global hotkeys."""
        try:
            from pynput import keyboard
            
            # Parse key combination
            keys = self._parse_key_combination(key_combination)
            if not keys:
                return False
            
            # Create listener
            def on_hotkey():
                try:
                    self.callback()
                except Exception as e:
                    logger.error(f"Error in hotkey callback: {e}")
            
            # Register hotkey
            hotkey = keyboard.HotKey(keys, on_hotkey)
            listener = keyboard.Listener(on_press=hotkey.press, on_release=hotkey.release)
            listener.start()
            
            self.listener = listener
            logger.info("pynput global hotkey registered")
            return True
        except ImportError:
            logger.debug("pynput not available")
            return False
        except Exception as e:
            logger.debug(f"pynput hotkey registration failed: {e}")
            return False
    
    def _parse_key_combination(self, combo: str) -> Optional[list]:
        """Parse key combination string into pynput key list."""
        try:
            from pynput.keyboard import Key
            
            parts = combo.replace("+", " ").split()
            keys = []
            
            for part in parts:
                part_lower = part.lower()
                if part_lower == "meta" or part_lower == "super" or part_lower == "win":
                    keys.append(Key.cmd)
                elif part_lower == "ctrl":
                    keys.append(Key.ctrl)
                elif part_lower == "alt":
                    keys.append(Key.alt)
                elif part_lower == "shift":
                    keys.append(Key.shift)
                else:
                    keys.append(part_lower)
            
            return keys if len(keys) > 1 else None
        except Exception:
            return None
    
    def unregister(self):
        """Unregister global hotkey."""
        if hasattr(self, 'listener'):
            try:
                self.listener.stop()
            except:
                pass
        self.active = False




