"""
Tool Registry.
Manages available tools and their permissions.
"""

from typing import Dict, Callable, Any

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        
    def register(self, name: str, func: Callable, description: str):
        self._tools[name] = func
        
    def get_tool(self, name: str) -> Callable:
        return self._tools.get(name)
        
    def list_tools(self) -> Dict[str, str]:
        return {name: "desc" for name in self._tools}
