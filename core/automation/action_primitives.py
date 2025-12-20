"""
Action Primitives for Cosmic OS
Basic, atomic GUI actions that can be composed into complex operations.
"""

import time
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MouseButton(Enum):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3


class ModifierKey(Enum):
    SHIFT = "shift"
    CTRL = "ctrl"
    ALT = "alt"
    SUPER = "super"


@dataclass
class Point:
    x: int
    y: int

    def __iter__(self):
        yield self.x
        yield self.y


@dataclass
class ActionResult:
    success: bool
    message: str = ""
    data: Optional[dict] = None


class ActionPrimitives:
    """
    Low-level action primitives for GUI automation.
    These are the building blocks for all AI-driven GUI interactions.
    """

    def __init__(self, screen_controller):
        """
        Initialize action primitives with a screen controller.
        
        Args:
            screen_controller: ScreenController instance for executing xdotool commands
        """
        self.screen = screen_controller
        self.default_click_delay = 0.1
        self.default_type_delay = 0.05

    def click(
        self,
        x: int,
        y: int,
        button: MouseButton = MouseButton.LEFT,
        clicks: int = 1,
        delay_between: float = 0.1
    ) -> ActionResult:
        """
        Click at specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button to click
            clicks: Number of clicks (1 for single, 2 for double)
            delay_between: Delay between multiple clicks
            
        Returns:
            ActionResult with success status
        """
        try:
            for i in range(clicks):
                self.screen.mouse_move(x, y)
                time.sleep(self.default_click_delay)
                self.screen.mouse_click(button.value)
                if i < clicks - 1:
                    time.sleep(delay_between)
            return ActionResult(success=True, message=f"Clicked at ({x}, {y})")
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return ActionResult(success=False, message=str(e))

    def double_click(self, x: int, y: int) -> ActionResult:
        """Double-click at specified coordinates."""
        return self.click(x, y, clicks=2, delay_between=0.05)

    def right_click(self, x: int, y: int) -> ActionResult:
        """Right-click at specified coordinates."""
        return self.click(x, y, button=MouseButton.RIGHT)

    def type_text(
        self,
        text: str,
        delay: Optional[float] = None,
        clear_first: bool = False
    ) -> ActionResult:
        """
        Type text using keyboard simulation.
        
        Args:
            text: Text to type
            delay: Delay between keystrokes (ms)
            clear_first: If True, select all and delete before typing
            
        Returns:
            ActionResult with success status
        """
        try:
            if clear_first:
                self.key_combo(["ctrl", "a"])
                time.sleep(0.05)
                self.press_key("Delete")
                time.sleep(0.05)
            
            type_delay = delay if delay is not None else self.default_type_delay
            self.screen.type_text(text, int(type_delay * 1000))
            return ActionResult(success=True, message=f"Typed {len(text)} characters")
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return ActionResult(success=False, message=str(e))

    def press_key(self, key: str) -> ActionResult:
        """
        Press a single key.
        
        Args:
            key: Key name (e.g., 'Return', 'Escape', 'Tab', 'Delete')
            
        Returns:
            ActionResult with success status
        """
        try:
            self.screen.key_press(key)
            return ActionResult(success=True, message=f"Pressed key: {key}")
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return ActionResult(success=False, message=str(e))

    def key_combo(self, keys: List[str]) -> ActionResult:
        """
        Press a key combination.
        
        Args:
            keys: List of keys to press together (e.g., ['ctrl', 'c'])
            
        Returns:
            ActionResult with success status
        """
        try:
            combo = "+".join(keys)
            self.screen.key_press(combo)
            return ActionResult(success=True, message=f"Pressed combo: {combo}")
        except Exception as e:
            logger.error(f"Key combo failed: {e}")
            return ActionResult(success=False, message=str(e))

    def wait(self, seconds: float) -> ActionResult:
        """
        Wait for specified duration.
        
        Args:
            seconds: Time to wait in seconds
            
        Returns:
            ActionResult (always succeeds)
        """
        time.sleep(seconds)
        return ActionResult(success=True, message=f"Waited {seconds}s")

    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: MouseButton = MouseButton.LEFT,
        duration: float = 0.5
    ) -> ActionResult:
        """
        Drag from one point to another.
        
        Args:
            start_x, start_y: Starting coordinates
            end_x, end_y: Ending coordinates
            button: Mouse button to hold
            duration: Duration of drag operation
            
        Returns:
            ActionResult with success status
        """
        try:
            self.screen.mouse_move(start_x, start_y)
            time.sleep(0.1)
            self.screen.mouse_down(button.value)
            
            # Smooth drag
            steps = max(int(duration * 20), 5)
            for i in range(1, steps + 1):
                t = i / steps
                curr_x = int(start_x + (end_x - start_x) * t)
                curr_y = int(start_y + (end_y - start_y) * t)
                self.screen.mouse_move(curr_x, curr_y)
                time.sleep(duration / steps)
            
            self.screen.mouse_up(button.value)
            return ActionResult(
                success=True,
                message=f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"
            )
        except Exception as e:
            logger.error(f"Drag failed: {e}")
            return ActionResult(success=False, message=str(e))

    def scroll(
        self,
        direction: str,
        amount: int = 3,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> ActionResult:
        """
        Scroll the mouse wheel.
        
        Args:
            direction: 'up' or 'down'
            amount: Number of scroll clicks
            x, y: Optional position to scroll at (moves mouse first)
            
        Returns:
            ActionResult with success status
        """
        try:
            if x is not None and y is not None:
                self.screen.mouse_move(x, y)
                time.sleep(0.1)
            
            button = 4 if direction == "up" else 5
            for _ in range(amount):
                self.screen.mouse_click(button)
                time.sleep(0.05)
            
            return ActionResult(success=True, message=f"Scrolled {direction} {amount} times")
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return ActionResult(success=False, message=str(e))

    def hover(self, x: int, y: int, duration: float = 0.5) -> ActionResult:
        """
        Move mouse to position and hover.
        
        Args:
            x, y: Target coordinates
            duration: How long to hover
            
        Returns:
            ActionResult with success status
        """
        try:
            self.screen.mouse_move(x, y)
            time.sleep(duration)
            return ActionResult(success=True, message=f"Hovered at ({x}, {y}) for {duration}s")
        except Exception as e:
            logger.error(f"Hover failed: {e}")
            return ActionResult(success=False, message=str(e))

    def move_mouse(self, x: int, y: int) -> ActionResult:
        """Move mouse to specified coordinates without clicking."""
        try:
            self.screen.mouse_move(x, y)
            return ActionResult(success=True, message=f"Moved to ({x}, {y})")
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return ActionResult(success=False, message=str(e))

    def take_screenshot(self, filepath: Optional[str] = None) -> ActionResult:
        """
        Capture a screenshot.
        
        Args:
            filepath: Optional path to save screenshot
            
        Returns:
            ActionResult with filepath in data
        """
        try:
            path = self.screen.take_screenshot(filepath)
            return ActionResult(
                success=True,
                message="Screenshot captured",
                data={"filepath": path}
            )
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ActionResult(success=False, message=str(e))
