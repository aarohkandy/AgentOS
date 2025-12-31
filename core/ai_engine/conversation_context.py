"""
Conversation Context Manager for Cosmic OS AI.

Manages full conversation history in OpenAI messages format for maintaining
context across multiple requests. Supports session management, context
summarization, and memory limits.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # "system", "user", or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to OpenAI message format."""
        return {"role": self.role, "content": self.content}


class ConversationContext:
    """
    Manages conversation history for maintaining context across requests.
    
    Features:
    - Full conversation history in OpenAI messages format
    - Configurable maximum context length (messages or tokens)
    - Session management (clear, save, restore)
    - Smart context summarization when limits are reached
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are Cosmic AI, an intelligent assistant that helps users control their computer through natural language.

You can:
1. Answer questions directly with {"description": "your answer"}
2. Control the computer with action plans:
   {"plan": [{"action": "click", "location": [x,y]}, {"action": "type", "text": "text"}, {"action": "key", "key": "Return"}], "description": "what this does", "estimated_time": N}

Available actions:
- click: {"action": "click", "location": [x, y]} - Click at screen coordinates
- type: {"action": "type", "text": "text"} - Type text
- key: {"action": "key", "key": "KeyName"} - Press a key (Return, Tab, Escape, Super_L, Alt+F4, etc.)
- wait: {"action": "wait", "seconds": N} - Wait N seconds
- drag: {"action": "drag", "start": [x1, y1], "end": [x2, y2]} - Drag from start to end

Guidelines:
- For simple questions (math, greetings, info), respond with just {"description": "answer"}
- For computer control tasks, provide a detailed plan with steps
- Be concise and efficient
- Always respond with valid JSON"""

    WEB_SEARCH_PROMPT_ADDITION = """

You have access to current information. When asked about:
- Current events, news, or recent information
- Real-time data (weather, stocks, sports scores)
- Information that may have changed since your training

Provide the most accurate and up-to-date information you can. If you're unsure about current information, say so."""
    
    def __init__(
        self,
        max_messages: int = 50,
        max_tokens_estimate: int = 8000,
        system_prompt: str = None,
        enable_web_search: bool = True
    ):
        """
        Initialize the conversation context manager.
        
        Args:
            max_messages: Maximum number of messages to keep in context
            max_tokens_estimate: Rough token limit for context (4 chars ≈ 1 token)
            system_prompt: Custom system prompt (uses default if None)
            enable_web_search: Whether to add web search instructions to system prompt
        """
        self.max_messages = max_messages
        self.max_tokens_estimate = max_tokens_estimate
        self.enable_web_search = enable_web_search
        
        # Build system prompt
        base_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        if enable_web_search:
            base_prompt += self.WEB_SEARCH_PROMPT_ADDITION
        
        self._system_message = Message(role="system", content=base_prompt)
        
        # Conversation history (excluding system message)
        self._messages: deque[Message] = deque(maxlen=max_messages)
        
        # Session metadata
        self._session_start = time.time()
        self._message_count = 0
        
        logger.info(f"ConversationContext initialized: max_messages={max_messages}, web_search={enable_web_search}")
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add a user message to the conversation."""
        if not content:
            return
        
        message = Message(
            role="user",
            content=content,
            metadata=metadata or {}
        )
        self._messages.append(message)
        self._message_count += 1
        
        # Trim if we exceed token estimate
        self._trim_to_token_limit()
        
        logger.debug(f"Added user message: {content[:50]}...")
    
    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add an assistant message to the conversation."""
        if not content:
            return
        
        message = Message(
            role="assistant",
            content=content,
            metadata=metadata or {}
        )
        self._messages.append(message)
        self._message_count += 1
        
        # Trim if we exceed token estimate
        self._trim_to_token_limit()
        
        logger.debug(f"Added assistant message: {content[:50]}...")
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        Get conversation history in OpenAI messages format.
        
        Args:
            include_system: Whether to include the system message
        
        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        messages = []
        
        if include_system:
            messages.append(self._system_message.to_dict())
        
        for msg in self._messages:
            messages.append(msg.to_dict())
        
        return messages
    
    def get_context_for_request(self, user_message: str) -> List[Dict[str, str]]:
        """
        Get the full context for an API request, including the new user message.
        
        This method:
        1. Gets existing conversation history
        2. Adds the new user message
        3. Returns the complete context
        
        Note: This does NOT add the message to history - call add_user_message after
        getting the response if you want to persist it.
        
        Args:
            user_message: The new user message to include
        
        Returns:
            List of message dicts ready for API request
        """
        messages = self.get_messages(include_system=True)
        messages.append({"role": "user", "content": user_message})
        return messages
    
    def _trim_to_token_limit(self) -> None:
        """Trim old messages if we exceed the token estimate."""
        # Rough token estimate: 4 characters ≈ 1 token
        while len(self._messages) > 2:  # Keep at least last exchange
            total_chars = sum(len(msg.content) for msg in self._messages)
            total_chars += len(self._system_message.content)
            estimated_tokens = total_chars / 4
            
            if estimated_tokens <= self.max_tokens_estimate:
                break
            
            # Remove oldest message
            removed = self._messages.popleft()
            logger.debug(f"Trimmed old message to stay within token limit")
    
    def clear(self) -> None:
        """Clear conversation history (keeps system message)."""
        self._messages.clear()
        self._session_start = time.time()
        logger.info("Conversation context cleared")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation state."""
        total_chars = sum(len(msg.content) for msg in self._messages)
        total_chars += len(self._system_message.content)
        
        return {
            "message_count": len(self._messages),
            "total_messages_processed": self._message_count,
            "estimated_tokens": total_chars // 4,
            "session_duration_seconds": time.time() - self._session_start,
            "max_messages": self.max_messages,
            "max_tokens_estimate": self.max_tokens_estimate
        }
    
    def update_system_prompt(self, new_prompt: str, append_web_search: bool = None) -> None:
        """
        Update the system prompt.
        
        Args:
            new_prompt: The new system prompt
            append_web_search: Whether to append web search instructions (uses current setting if None)
        """
        if append_web_search is None:
            append_web_search = self.enable_web_search
        
        if append_web_search:
            new_prompt += self.WEB_SEARCH_PROMPT_ADDITION
        
        self._system_message = Message(role="system", content=new_prompt)
        logger.info("System prompt updated")
    
    def get_last_exchange(self) -> Optional[tuple]:
        """
        Get the last user-assistant exchange.
        
        Returns:
            Tuple of (user_message, assistant_message) or None if no exchange exists
        """
        messages = list(self._messages)
        if len(messages) < 2:
            return None
        
        # Find last user-assistant pair
        for i in range(len(messages) - 1, 0, -1):
            if messages[i].role == "assistant" and messages[i-1].role == "user":
                return (messages[i-1].content, messages[i].content)
        
        return None
    
    def export_history(self) -> List[Dict[str, Any]]:
        """Export full conversation history with metadata."""
        history = [{
            "role": self._system_message.role,
            "content": self._system_message.content,
            "timestamp": self._system_message.timestamp,
            "metadata": {"type": "system"}
        }]
        
        for msg in self._messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata
            })
        
        return history
    
    def import_history(self, history: List[Dict[str, Any]]) -> None:
        """
        Import conversation history.
        
        Args:
            history: List of message dicts with role, content, and optional timestamp/metadata
        """
        self._messages.clear()
        
        for item in history:
            if item.get("role") == "system":
                self._system_message = Message(
                    role="system",
                    content=item["content"],
                    timestamp=item.get("timestamp", time.time()),
                    metadata=item.get("metadata", {})
                )
            else:
                msg = Message(
                    role=item["role"],
                    content=item["content"],
                    timestamp=item.get("timestamp", time.time()),
                    metadata=item.get("metadata", {})
                )
                self._messages.append(msg)
        
        logger.info(f"Imported {len(self._messages)} messages")


# Singleton instance for easy access
_context_instance: Optional[ConversationContext] = None


def get_conversation_context(**kwargs) -> ConversationContext:
    """Get or create the singleton conversation context instance."""
    global _context_instance
    if _context_instance is None:
        _context_instance = ConversationContext(**kwargs)
    return _context_instance


def reset_conversation_context():
    """Reset the singleton instance (useful for testing)."""
    global _context_instance
    _context_instance = None

