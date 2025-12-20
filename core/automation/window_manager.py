"""
Window Manager for Cosmic OS
Window detection, focus management, and window operations.
"""

import subprocess
import logging
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Information about a window."""
    window_id: int
    name: str
    x: int
    y: int
    width: int
    height: int
    desktop: int
    pid: Optional[int] = None
    wm_class: Optional[str] = None


class WindowManager:
    """
    Window detection and management for GUI automation.
    Uses xdotool and wmctrl for window operations.
    """

    def __init__(self, screen_controller):
        """
        Initialize window manager.
        
        Args:
            screen_controller: ScreenController instance
        """
        self.screen = screen_controller

    def _run_xdotool(self, *args: str) -> str:
        """Execute xdotool command through screen controller."""
        return self.screen._run_xdotool(*args)

    def _run_shell(self, cmd: str) -> str:
        """Execute shell command through screen controller."""
        return self.screen._run_shell(cmd)

    # ===== Window Search =====

    def find_window_by_name(
        self,
        name: str,
        exact: bool = False,
        visible_only: bool = True
    ) -> List[int]:
        """
        Find windows by name/title.
        
        Args:
            name: Window name or partial name to search for
            exact: If True, match exact name only
            visible_only: If True, only return visible windows
            
        Returns:
            List of matching window IDs
        """
        try:
            args = ["search"]
            if exact:
                args.append("--name")
            else:
                args.append("--name")
            
            if visible_only:
                args.append("--onlyvisible")
            
            args.append(name)
            output = self._run_xdotool(*args)
            
            if not output:
                return []
            
            return [int(wid) for wid in output.strip().split("\n") if wid]
        except Exception as e:
            logger.debug(f"No windows found matching '{name}': {e}")
            return []

    def find_window_by_class(
        self,
        wm_class: str,
        visible_only: bool = True
    ) -> List[int]:
        """
        Find windows by WM_CLASS (application identifier).
        
        Args:
            wm_class: Window class name (e.g., 'firefox', 'konsole')
            visible_only: If True, only return visible windows
            
        Returns:
            List of matching window IDs
        """
        try:
            args = ["search", "--class"]
            if visible_only:
                args.append("--onlyvisible")
            args.append(wm_class)
            output = self._run_xdotool(*args)
            
            if not output:
                return []
            
            return [int(wid) for wid in output.strip().split("\n") if wid]
        except Exception:
            return []

    def find_window_by_pid(self, pid: int) -> List[int]:
        """Find windows by process ID."""
        try:
            output = self._run_xdotool("search", "--pid", str(pid))
            if not output:
                return []
            return [int(wid) for wid in output.strip().split("\n") if wid]
        except Exception:
            return []

    # ===== Window Information =====

    def get_window_info(self, window_id: int) -> Optional[WindowInfo]:
        """
        Get detailed information about a window.
        
        Args:
            window_id: Window ID to query
            
        Returns:
            WindowInfo object or None if window doesn't exist
        """
        try:
            # Get window name
            name = self._run_xdotool("getwindowname", str(window_id))
            
            # Get window geometry
            geo = self._run_xdotool("getwindowgeometry", str(window_id))
            # Parse geometry output like:
            # Window 12345
            #   Position: 100,200 (screen: 0)
            #   Geometry: 800x600
            
            x, y, width, height = 0, 0, 0, 0
            for line in geo.split("\n"):
                if "Position:" in line:
                    match = re.search(r"Position:\s*(\d+),(\d+)", line)
                    if match:
                        x, y = int(match.group(1)), int(match.group(2))
                elif "Geometry:" in line:
                    match = re.search(r"Geometry:\s*(\d+)x(\d+)", line)
                    if match:
                        width, height = int(match.group(1)), int(match.group(2))
            
            # Get desktop (workspace) number
            desktop = 0
            try:
                desktop_output = self._run_shell(
                    f"xdotool get_desktop_for_window {window_id}"
                )
                desktop = int(desktop_output)
            except Exception:
                pass
            
            # Get PID
            pid = None
            try:
                pid_output = self._run_xdotool("getwindowpid", str(window_id))
                pid = int(pid_output)
            except Exception:
                pass
            
            return WindowInfo(
                window_id=window_id,
                name=name,
                x=x,
                y=y,
                width=width,
                height=height,
                desktop=desktop,
                pid=pid
            )
        except Exception as e:
            logger.error(f"Failed to get window info for {window_id}: {e}")
            return None

    def get_active_window(self) -> Optional[int]:
        """Get the currently focused window ID."""
        return self.screen.get_active_window()

    def get_active_window_info(self) -> Optional[WindowInfo]:
        """Get info about the currently focused window."""
        window_id = self.get_active_window()
        if window_id:
            return self.get_window_info(window_id)
        return None

    def list_windows(self, desktop: Optional[int] = None) -> List[WindowInfo]:
        """
        List all visible windows.
        
        Args:
            desktop: Optional desktop/workspace number to filter
            
        Returns:
            List of WindowInfo objects
        """
        try:
            output = self._run_xdotool("search", "--onlyvisible", "--name", "")
            if not output:
                return []
            
            windows = []
            for wid_str in output.strip().split("\n"):
                if not wid_str:
                    continue
                try:
                    wid = int(wid_str)
                    info = self.get_window_info(wid)
                    if info:
                        if desktop is None or info.desktop == desktop:
                            windows.append(info)
                except ValueError:
                    continue
            
            return windows
        except Exception as e:
            logger.error(f"Failed to list windows: {e}")
            return []

    # ===== Window Operations =====

    def focus_window(self, window_id: int) -> bool:
        """
        Focus (activate) a window.
        
        Args:
            window_id: Window ID to focus
            
        Returns:
            True if successful
        """
        try:
            self._run_xdotool("windowactivate", "--sync", str(window_id))
            return True
        except Exception as e:
            logger.error(f"Failed to focus window {window_id}: {e}")
            return False

    def focus_window_by_name(self, name: str) -> bool:
        """Focus a window by name."""
        windows = self.find_window_by_name(name)
        if windows:
            return self.focus_window(windows[0])
        return False

    def minimize_window(self, window_id: int) -> bool:
        """Minimize a window."""
        try:
            self._run_xdotool("windowminimize", str(window_id))
            return True
        except Exception:
            return False

    def maximize_window(self, window_id: int) -> bool:
        """Maximize a window (toggle)."""
        try:
            # Use wmctrl if available, otherwise try key combo
            try:
                self._run_shell(f"wmctrl -i -r {window_id} -b toggle,maximized_vert,maximized_horz")
            except Exception:
                self.focus_window(window_id)
                self.screen.key_press("super+Up")
            return True
        except Exception:
            return False

    def close_window(self, window_id: int) -> bool:
        """Close a window gracefully."""
        try:
            self._run_shell(f"wmctrl -i -c {window_id}")
            return True
        except Exception:
            try:
                # Fallback: send Alt+F4
                self.focus_window(window_id)
                self.screen.key_press("alt+F4")
                return True
            except Exception:
                return False

    def move_window(self, window_id: int, x: int, y: int) -> bool:
        """Move a window to specified position."""
        try:
            self._run_xdotool("windowmove", str(window_id), str(x), str(y))
            return True
        except Exception:
            return False

    def resize_window(self, window_id: int, width: int, height: int) -> bool:
        """Resize a window."""
        try:
            self._run_xdotool("windowsize", str(window_id), str(width), str(height))
            return True
        except Exception:
            return False

    def raise_window(self, window_id: int) -> bool:
        """Raise window to front."""
        try:
            self._run_xdotool("windowraise", str(window_id))
            return True
        except Exception:
            return False

    # ===== Desktop/Workspace Operations =====

    def get_current_desktop(self) -> int:
        """Get current desktop/workspace number."""
        try:
            output = self._run_shell("xdotool get_desktop")
            return int(output)
        except Exception:
            return 0

    def get_num_desktops(self) -> int:
        """Get total number of desktops/workspaces."""
        try:
            output = self._run_shell("xdotool get_num_desktops")
            return int(output)
        except Exception:
            return 1

    def switch_desktop(self, desktop: int) -> bool:
        """Switch to specified desktop/workspace."""
        try:
            self._run_shell(f"xdotool set_desktop {desktop}")
            return True
        except Exception:
            return False

    def move_window_to_desktop(self, window_id: int, desktop: int) -> bool:
        """Move a window to specified desktop."""
        try:
            self._run_shell(f"xdotool set_desktop_for_window {window_id} {desktop}")
            return True
        except Exception:
            return False

    # ===== Application Launch =====

    def launch_application(self, command: str, wait_for_window: bool = True) -> Optional[int]:
        """
        Launch an application.
        
        Args:
            command: Command to execute
            wait_for_window: If True, wait for a new window and return its ID
            
        Returns:
            Window ID if wait_for_window is True and window appears, else None
        """
        import time
        
        # Get list of windows before launch
        windows_before = set()
        try:
            output = self._run_xdotool("search", "--onlyvisible", "--name", "")
            if output:
                windows_before = set(int(w) for w in output.strip().split("\n") if w)
        except Exception:
            pass
        
        # Launch application
        try:
            subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.error(f"Failed to launch '{command}': {e}")
            return None
        
        if not wait_for_window:
            return None
        
        # Wait for new window
        for _ in range(50):  # 5 second timeout
            time.sleep(0.1)
            try:
                output = self._run_xdotool("search", "--onlyvisible", "--name", "")
                if output:
                    windows_after = set(int(w) for w in output.strip().split("\n") if w)
                    new_windows = windows_after - windows_before
                    if new_windows:
                        return new_windows.pop()
            except Exception:
                continue
        
        return None
