"""
Performance Optimizations - iOS-quality instant responses
"""

import logging
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

# Global performance optimizations
_response_times = []

def measure_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        _response_times.append(elapsed)
        if elapsed > 0.1:  # Log slow operations
            logger.debug(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

@lru_cache(maxsize=1000)
def normalize_query(query: str) -> str:
    """Normalize query for caching/comparison."""
    return ' '.join(query.lower().strip().split())

def get_performance_stats() -> dict:
    """Get performance statistics."""
    if not _response_times:
        return {"avg_time": 0, "total_requests": 0}
    
    return {
        "avg_time": sum(_response_times) / len(_response_times),
        "min_time": min(_response_times),
        "max_time": max(_response_times),
        "total_requests": len(_response_times)
    }




