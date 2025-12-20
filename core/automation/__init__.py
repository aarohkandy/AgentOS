# Cosmic OS Automation Module
# Provides GUI automation primitives using xdotool (X11) with future AT-SPI support

from core.automation.action_primitives import ActionPrimitives
from core.automation.screen_controller import ScreenController
from core.automation.window_manager import WindowManager

__all__ = ['ActionPrimitives', 'ScreenController', 'WindowManager']
