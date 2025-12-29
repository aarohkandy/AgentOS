"""
System and Internet Access Module
Provides capabilities for:
- Getting system time, date
- Fetching news from internet
- Other system information queries
"""

import logging
import subprocess
import datetime
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SystemAccess:
    """Provides system and internet access capabilities."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout for web requests
    
    def get_time(self) -> str:
        """Get current system time."""
        try:
            now = datetime.datetime.now()
            return now.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Failed to get time: {e}")
            return "Unable to get time"
    
    def get_date(self) -> str:
        """Get current system date."""
        try:
            now = datetime.datetime.now()
            return now.strftime("%A, %B %d, %Y")
        except Exception as e:
            logger.error(f"Failed to get date: {e}")
            return "Unable to get date"
    
    def get_news(self, query: Optional[str] = None, limit: int = 5) -> str:
        """Get recent news. If query is provided, searches for news about that topic."""
        try:
            # Use a simple news API (example: NewsAPI or similar)
            # For now, we'll use a simple web search approach
            if query:
                # Try to get news about specific topic
                # This is a placeholder - in production, use a real news API
                return f"News about '{query}': [News API integration needed - placeholder response]"
            else:
                # General news
                return "Recent news: [News API integration needed - placeholder response]"
        except Exception as e:
            logger.error(f"Failed to get news: {e}")
            return f"Unable to fetch news: {str(e)}"
    
    def check_internet(self) -> bool:
        """Check if internet connection is available."""
        try:
            response = self.session.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def web_search(self, query: str) -> str:
        """Perform a web search (simplified - returns search URL for now)."""
        try:
            # In a real implementation, this would use a search API
            # For now, return a search URL
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            return f"Search URL: {search_url}"
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Unable to perform web search: {str(e)}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        try:
            import platform
            import psutil
            
            info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "uptime_seconds": int(psutil.boot_time()),
            }
            return info
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}
    
    def handle_query(self, query: str) -> Dict[str, Any]:
        """
        Handle a system/internet query and return appropriate response.
        
        Args:
            query: User query (e.g., "what time is it", "recent news", etc.)
            
        Returns:
            Dict with response information
        """
        query_lower = query.lower().strip()
        
        # Time queries
        if any(word in query_lower for word in ["time", "what time", "current time"]):
            time_str = self.get_time()
            return {
                "description": f"The current time is {time_str}",
                "system_query": True
            }
        
        # Date queries
        if any(word in query_lower for word in ["date", "what date", "today", "what day"]):
            date_str = self.get_date()
            return {
                "description": f"Today's date is {date_str}",
                "system_query": True
            }
        
        # News queries
        if "news" in query_lower or "recent news" in query_lower:
            # Extract topic if mentioned
            topic = None
            if "about" in query_lower:
                parts = query_lower.split("about")
                if len(parts) > 1:
                    topic = parts[1].strip()
            
            news = self.get_news(topic)
            return {
                "description": news,
                "system_query": True
            }
        
        # Internet check
        if "internet" in query_lower and ("check" in query_lower or "connected" in query_lower):
            connected = self.check_internet()
            status = "connected" if connected else "not connected"
            return {
                "description": f"Internet is {status}",
                "system_query": True
            }
        
        # System info
        if any(word in query_lower for word in ["system info", "system information", "computer info"]):
            info = self.get_system_info()
            if "error" in info:
                return {
                    "description": f"Unable to get system info: {info['error']}",
                    "system_query": True
                }
            
            info_str = "\n".join([f"{k}: {v}" for k, v in info.items()])
            return {
                "description": f"System Information:\n{info_str}",
                "system_query": True
            }
        
        # Default: not a system query
        return None

