"""
Memory Manager for AgentOS.
Handles short-term (working) memory and long-term (vector/database) memory.
"""

from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class MemoryItem:
    content: str
    timestamp: float
    tags: List[str]
    embedding: Optional[List[float]] = None

class MemoryManager:
    def __init__(self):
        self.short_term: List[MemoryItem] = []
        
    def add(self, content: str, tags: List[str] = None):
        pass
        
    def search(self, query: str) -> List[MemoryItem]:
        return []
