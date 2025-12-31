"""
Response Cache for iOS-quality instant responses
Caches AI responses for instant repeated queries
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    LRU cache with TTL for instant iOS-quality responses.
    Automatically evicts old entries to stay within memory limits.
    """
    
    def __init__(self, max_size: int = 200, ttl_seconds: int = 7200):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of cached responses
            ttl_seconds: Time-to-live in seconds (default 2 hours)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = None
        try:
            import threading
            self._lock = threading.Lock()
        except ImportError:
            pass
    
    def _acquire_lock(self):
        """Acquire lock if available."""
        if self._lock:
            self._lock.acquire()
    
    def _release_lock(self):
        """Release lock if available."""
        if self._lock:
            self._lock.release()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired.
        
        Args:
            key: Cache key (typically normalized query)
            
        Returns:
            Cached response dict or None if not found/expired
        """
        self._acquire_lock()
        try:
            # Normalize key
            key = key.strip().lower()
            
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            cached_time = entry.get("_cached_at", 0)
            current_time = time.time()
            
            # Check if expired
            if current_time - cached_time > self.ttl_seconds:
                # Expired - remove it
                del self.cache[key]
                logger.debug(f"Cache expired for: {key[:50]}")
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            
            # Return response (without internal metadata)
            response = entry.copy()
            response.pop("_cached_at", None)
            logger.debug(f"Cache HIT for: {key[:50]}")
            return response
        finally:
            self._release_lock()
    
    def set(self, key: str, value: Dict[str, Any]):
        """
        Cache a response.
        
        Args:
            key: Cache key (typically normalized query)
            value: Response dict to cache
        """
        self._acquire_lock()
        try:
            # Normalize key
            key = key.strip().lower()
            
            # Add metadata
            cache_entry = value.copy()
            cache_entry["_cached_at"] = time.time()
            
            # Remove old entry if exists
            if key in self.cache:
                del self.cache[key]
            
            # Add new entry
            self.cache[key] = cache_entry
            
            # Evict oldest if over limit
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                logger.debug(f"Cache evicted: {oldest_key[:50]}")
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            logger.debug(f"Cache SET for: {key[:50]}")
        finally:
            self._release_lock()
    
    def clear(self):
        """Clear all cached entries."""
        self._acquire_lock()
        try:
            self.cache.clear()
            logger.debug("Cache cleared")
        finally:
            self._release_lock()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }
