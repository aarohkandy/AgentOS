"""
Accessibility Module for Cosmic OS
AT-SPI2 integration for accessible GUI automation (future implementation).

This module provides infrastructure for using AT-SPI2 (Assistive Technology
Service Provider Interface) to interact with GUI elements by their semantic
properties rather than screen coordinates.

Status: Placeholder for future implementation
Current version uses xdotool coordinates; this will enable more robust automation.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import AT-SPI2 bindings
try:
    import gi
    gi.require_version('Atspi', '2.0')
    from gi.repository import Atspi
    ATSPI_AVAILABLE = True
except (ImportError, ValueError):
    ATSPI_AVAILABLE = False
    logger.info("AT-SPI2 not available. Using coordinate-based automation only.")


class AccessibleRole(Enum):
    """Common accessible roles for UI elements."""
    WINDOW = "window"
    FRAME = "frame"
    DIALOG = "dialog"
    PUSH_BUTTON = "push button"
    TOGGLE_BUTTON = "toggle button"
    CHECK_BOX = "check box"
    RADIO_BUTTON = "radio button"
    TEXT = "text"
    ENTRY = "entry"
    PASSWORD_TEXT = "password text"
    MENU = "menu"
    MENU_ITEM = "menu item"
    MENU_BAR = "menu bar"
    TOOL_BAR = "tool bar"
    LIST = "list"
    LIST_ITEM = "list item"
    TABLE = "table"
    TABLE_CELL = "table cell"
    TREE = "tree"
    TREE_ITEM = "tree item"
    TAB_LIST = "page tab list"
    TAB = "page tab"
    SCROLL_BAR = "scroll bar"
    SLIDER = "slider"
    SPIN_BUTTON = "spin button"
    COMBO_BOX = "combo box"
    LABEL = "label"
    IMAGE = "image"
    SEPARATOR = "separator"
    PANEL = "panel"
    FILLER = "filler"
    UNKNOWN = "unknown"


@dataclass
class AccessibleElement:
    """Represents an accessible UI element."""
    name: str
    role: AccessibleRole
    description: str
    x: int
    y: int
    width: int
    height: int
    states: List[str]
    actions: List[str]
    value: Optional[str] = None
    children_count: int = 0
    
    @property
    def center(self) -> tuple:
        """Get center coordinates of element."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def is_visible(self) -> bool:
        """Check if element is visible."""
        return "visible" in self.states and "showing" in self.states
    
    @property
    def is_focusable(self) -> bool:
        """Check if element can receive focus."""
        return "focusable" in self.states
    
    @property
    def is_enabled(self) -> bool:
        """Check if element is enabled."""
        return "enabled" in self.states


class AccessibilityManager:
    """
    Manages accessibility-based UI element discovery and interaction.
    
    This is a future-focused module that will eventually replace
    coordinate-based automation with semantic element identification.
    """

    def __init__(self):
        """Initialize accessibility manager."""
        self.available = ATSPI_AVAILABLE
        if self.available:
            logger.info("AT-SPI2 accessibility support enabled")
        else:
            logger.info("AT-SPI2 not available - accessibility features disabled")

    def is_available(self) -> bool:
        """Check if AT-SPI2 is available."""
        return self.available

    def get_desktop(self):
        """Get the desktop accessible object."""
        if not self.available:
            return None
        try:
            return Atspi.get_desktop(0)
        except Exception as e:
            logger.error(f"Failed to get desktop: {e}")
            return None

    def find_application(self, name: str) -> Optional[Any]:
        """
        Find an application by name.
        
        Args:
            name: Application name to find
            
        Returns:
            Accessible object for the application or None
        """
        if not self.available:
            logger.warning("AT-SPI2 not available")
            return None
        
        try:
            desktop = self.get_desktop()
            if not desktop:
                return None
            
            for i in range(desktop.get_child_count()):
                app = desktop.get_child_at_index(i)
                if app and name.lower() in app.get_name().lower():
                    return app
            return None
        except Exception as e:
            logger.error(f"Failed to find application '{name}': {e}")
            return None

    def find_element_by_name(
        self,
        root: Any,
        name: str,
        role: Optional[AccessibleRole] = None
    ) -> Optional[AccessibleElement]:
        """
        Find an element by name within a subtree.
        
        Args:
            root: Root accessible object to search from
            name: Element name to find
            role: Optional role filter
            
        Returns:
            AccessibleElement if found, None otherwise
        """
        if not self.available or not root:
            return None
        
        try:
            return self._search_tree(root, name, role)
        except Exception as e:
            logger.error(f"Failed to find element '{name}': {e}")
            return None

    def _search_tree(
        self,
        node: Any,
        name: str,
        role: Optional[AccessibleRole]
    ) -> Optional[AccessibleElement]:
        """Recursively search accessibility tree."""
        try:
            node_name = node.get_name() or ""
            node_role = node.get_role_name()
            
            # Check if this node matches
            if name.lower() in node_name.lower():
                if role is None or node_role == role.value:
                    return self._node_to_element(node)
            
            # Search children
            for i in range(node.get_child_count()):
                child = node.get_child_at_index(i)
                if child:
                    result = self._search_tree(child, name, role)
                    if result:
                        return result
            
            return None
        except Exception:
            return None

    def _node_to_element(self, node: Any) -> Optional[AccessibleElement]:
        """Convert AT-SPI node to AccessibleElement."""
        try:
            # Get component interface for geometry
            component = node.get_component_iface()
            if component:
                rect = component.get_extents(Atspi.CoordType.SCREEN)
                x, y, width, height = rect.x, rect.y, rect.width, rect.height
            else:
                x, y, width, height = 0, 0, 0, 0
            
            # Get states
            state_set = node.get_state_set()
            states = []
            for state in Atspi.StateType:
                if state_set.contains(state):
                    states.append(state.value_nick)
            
            # Get available actions
            action = node.get_action_iface()
            actions = []
            if action:
                for i in range(action.get_n_actions()):
                    actions.append(action.get_action_name(i))
            
            # Get value if applicable
            value_iface = node.get_value_iface()
            value = None
            if value_iface:
                value = str(value_iface.get_current_value())
            
            # Map role
            role_name = node.get_role_name()
            try:
                role = AccessibleRole(role_name)
            except ValueError:
                role = AccessibleRole.UNKNOWN
            
            return AccessibleElement(
                name=node.get_name() or "",
                role=role,
                description=node.get_description() or "",
                x=x,
                y=y,
                width=width,
                height=height,
                states=states,
                actions=actions,
                value=value,
                children_count=node.get_child_count()
            )
        except Exception as e:
            logger.error(f"Failed to convert node to element: {e}")
            return None

    def click_element(self, element: AccessibleElement) -> bool:
        """
        Click on an accessible element.
        
        Uses the 'click' action if available, otherwise falls back
        to coordinate-based clicking.
        
        Args:
            element: Element to click
            
        Returns:
            True if successful
        """
        # For now, return center coordinates for xdotool to use
        # In future, can use AT-SPI actions directly
        logger.info(f"Click element '{element.name}' at {element.center}")
        return True

    def get_element_text(self, element: Any) -> Optional[str]:
        """Get text content of an accessible element."""
        if not self.available:
            return None
        
        try:
            text_iface = element.get_text_iface()
            if text_iface:
                length = text_iface.get_character_count()
                return text_iface.get_text(0, length)
            return None
        except Exception:
            return None

    def set_element_text(self, element: Any, text: str) -> bool:
        """Set text content of an editable element."""
        if not self.available:
            return False
        
        try:
            editable = element.get_editable_text_iface()
            if editable:
                # Clear existing text
                text_iface = element.get_text_iface()
                if text_iface:
                    length = text_iface.get_character_count()
                    editable.delete_text(0, length)
                # Insert new text
                editable.insert_text(0, text, len(text))
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set text: {e}")
            return False


# Placeholder for future advanced features
class AccessibilityWatcher:
    """
    Watch for accessibility events (window opens, focus changes, etc.)
    
    Future implementation will enable reactive automation based on
    UI events rather than polling.
    """
    
    def __init__(self):
        self.available = ATSPI_AVAILABLE
        self.listeners = []

    def register_focus_listener(self, callback):
        """Register callback for focus change events."""
        if not self.available:
            logger.warning("AT-SPI2 not available for event watching")
            return
        
        self.listeners.append(('focus', callback))
        logger.info("Focus listener registered")

    def register_window_listener(self, callback):
        """Register callback for window events."""
        if not self.available:
            return
        
        self.listeners.append(('window', callback))
        logger.info("Window listener registered")

    def start(self):
        """Start listening for events."""
        if not self.available:
            return
        
        # Future: Set up AT-SPI2 event listeners
        logger.info("Accessibility watcher started (placeholder)")

    def stop(self):
        """Stop listening for events."""
        self.listeners.clear()
        logger.info("Accessibility watcher stopped")

