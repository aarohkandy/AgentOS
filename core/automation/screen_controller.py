import shutil
import logging
import subprocess
import time

logger = logging.getLogger(__name__)

class ScreenController:
    """
    Robust wrapper around xdotool for GUI interaction.
    Handles error checking, delays, and common actions.
    """
    def __init__(self, config=None):
        self.config = config
        self.xdotool = shutil.which("xdotool")
        if not self.xdotool:
            logger.critical("xdotool not found! GUI automation will fail.")
        
        # Default delays
        self.click_delay = 0.1
        self.type_delay = 0.05
        
        if config:
            self.click_delay = config.get_float("Automation", "click_delay", 0.1)
            self.type_delay = config.get_float("Automation", "type_delay", 0.05)

    def _run(self, args):
        if not self.xdotool:
            logger.warning(f"[Dry Run] xdotool {args}")
            return True

        cmd = f"{self.xdotool} {args}"
        try:
            subprocess.run(cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool error: {e}")
            return False

    def click(self, x, y, button=1):
        """Click at specific coordinates."""
        logger.debug(f"Clicking at {x}, {y}")
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
        """Drag from start to end."""
        return self._run(f"mousemove {start_x} {start_y} mousedown 1 mousemove {end_x} {end_y} mouseup 1")

    def get_mouse_location(self):
        """Returns (x, y) tuple."""
        if not self.xdotool:
            return (0, 0)
        
        try:
            output = subprocess.check_output(f"{self.xdotool} getmouselocation --shell", shell=True).decode()
            vals = {}
            for line in output.splitlines():
                k, v = line.split("=")
                vals[k] = int(v)
            return (vals.get("X", 0), vals.get("Y", 0))
        except Exception:
            return (0, 0)

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

