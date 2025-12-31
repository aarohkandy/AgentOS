import shutil
import logging
import subprocess
import time

logger = logging.getLogger(__name__)

class ScreenController:
    """
    Robust wrapper around xdotool for GUI interaction.
    Handles error checking, delays, and common actions.
    Excludes sidebar area from screen calculations.
    """
    def __init__(self, config=None):
        self.config = config
        self.xdotool = shutil.which("xdotool")
        if not self.xdotool:
            logger.critical("xdotool not found! GUI automation will fail.")
        
        # Default delays
        self.click_delay = 0.1
        self.type_delay = 0.05
        
        # Sidebar configuration - sidebar is on the right side
        # Always assume sidebar area is reserved to prevent overlap
        self.sidebar_width = 420  # Sidebar width in pixels
        self.sidebar_visible = True  # Always assume sidebar area is reserved
        
        if config:
            self.click_delay = config.get_float("Automation", "click_delay", 0.1)
            self.type_delay = config.get_float("Automation", "type_delay", 0.05)
            # Allow config to override sidebar width
            sidebar_width_config = config.get_int("GUI", "sidebar_width", fallback=420)
            if sidebar_width_config:
                self.sidebar_width = sidebar_width_config
        
        # Get screen dimensions
        self.screen_width, self.screen_height = self._get_screen_size()
        # Always exclude sidebar area from available screen space
        self.available_width = self.screen_width - self.sidebar_width

    def _run(self, args):
        if not self.xdotool:
            logger.warning(f"[Dry Run] xdotool {args}")
            return True

        cmd = f"{self.xdotool} {args}"
        try:
            subprocess.run(cmd, shell=True, check=True, timeout=10)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool error: {e}", exc_info=True)
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"xdotool command timed out: {args}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in _run: {e}", exc_info=True)
            return False

    def _get_screen_size(self):
        """Get screen resolution."""
        try:
            if self.xdotool:
                output = subprocess.check_output(f"{self.xdotool} getdisplaygeometry", shell=True).decode().strip()
                width, height = map(int, output.split())
                return width, height
        except:
            pass
        # Fallback to common resolution
        return 1920, 1080
    
    def _constrain_to_available_area(self, x, y):
        """Constrain coordinates to available screen area (excluding sidebar).
        This ensures no actions happen in or behind the sidebar area.
        """
        # Ensure coordinates are within available area (never in sidebar area)
        # Sidebar is on the right, so x must be < available_width
        x = max(0, min(x, self.available_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        
        # Double-check: if x is in sidebar area, clamp it
        if x >= self.available_width:
            x = self.available_width - 1
            logger.warning(f"Coordinate {x} was in sidebar area, clamped to {x}")
        
        return x, y
    
    def set_sidebar_visible(self, visible):
        """Update sidebar visibility state."""
        self.sidebar_visible = visible
    
    def click(self, x, y, button=1):
        """Click at specific coordinates, constrained to available area (excluding sidebar)."""
        x, y = self._constrain_to_available_area(x, y)
        logger.debug(f"Clicking at {x}, {y} (constrained from original {x}, {y})")
        return self._run(f"mousemove {x} {y} click {button}")

    def type_text(self, text, delay=None):
        """Type text string."""
        d = delay if delay else self.type_delay
        # Calculate milliseconds for xdotool
        delay_ms = int(d * 1000)
        # Escape double quotes
        safe_text = text.replace('"', '\\"')
        return self._run(f"type --delay {delay_ms} \"{safe_text}\"")

    def press_key(self, key):
        """Press a keyboard key (e.g., Return, Ctrl+c)."""
        return self._run(f"key {key}")

    def drag(self, start_x, start_y, end_x, end_y):
        """Drag from start to end, constrained to available area (excluding sidebar)."""
        start_x, start_y = self._constrain_to_available_area(start_x, start_y)
        end_x, end_y = self._constrain_to_available_area(end_x, end_y)
        return self._run(f"mousemove {start_x} {start_y} mousedown 1 mousemove {end_x} {end_y} mouseup 1")

    def get_mouse_location(self):
        """Returns (x, y) tuple, constrained to available area."""
        if not self.xdotool:
            return (0, 0)
        
        try:
            output = subprocess.check_output(f"{self.xdotool} getmouselocation --shell", shell=True).decode()
            vals = {}
            for line in output.splitlines():
                k, v = line.split("=")
                vals[k] = int(v)
            x, y = vals.get("X", 0), vals.get("Y", 0)
            # Constrain to available area
            x, y = self._constrain_to_available_area(x, y)
            return (x, y)
        except Exception:
            return (0, 0)
    
    def get_available_screen_size(self):
        """Get available screen size (excluding sidebar)."""
        return (self.available_width, self.screen_height)

    def find_window(self, name):
        """Find window ID by name."""
        if not self.xdotool:
            return None
        try:
            wid = subprocess.check_output(f"{self.xdotool} search --onlyvisible --name \"{name}\" | head -1", shell=True).decode().strip()
            return wid
        except:
            return None

    def focus_window(self, wid):
        if wid:
            self._run(f"windowactivate {wid}")

