"""
System and Internet Access Module
Provides time, system info, news, and web access capabilities.
"""

import logging
import subprocess
import datetime
import platform
import psutil
import requests
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SystemAccess:
    """Provides system and internet access capabilities."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CosmicOS/1.0 (Linux)'
        })
    
    def get_time(self) -> Dict[str, Any]:
        """Get current system time."""
        try:
            now = datetime.datetime.now()
            return {
                "success": True,
                "time": now.strftime("%H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": str(datetime.datetime.now().astimezone().tzinfo)
            }
        except Exception as e:
            logger.error(f"Error getting time: {e}")
            return {"success": False, "error": str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            return {
                "success": True,
                "os": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "cpu_percent": psutil.cpu_percent(interval=0.1),  # Faster - 0.1s instead of 1s
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"success": False, "error": str(e)}
    
    def get_news(self, query: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Get news using web search for real results."""
        try:
            from core.ai_engine.web_search import get_web_search_helper
            
            helper = get_web_search_helper()
            
            # Build search query - use more specific queries for better results
            if query:
                search_query = f"latest news {query} 2024"
            else:
                search_query = "breaking news today 2024"
            
            logger.debug(f"Searching for news with query: {search_query}")
            
            # Use fast augment_query_with_search with short timeout (don't block for long)
            search_results = helper.augment_query_with_search(search_query, timeout=2.0)  # Fast - 2 seconds max
            if search_results:
                return {
                    "success": True,
                    "message": f"**Recent News{' - ' + query if query else ''}:**\n\n{search_results}",
                    "query": query or "general",
                    "results": search_results
                }
            
            # No results found - let the AI handle it with context instead (don't block)
            return None
            
        except ImportError:
            # Fallback if WebSearchHelper not available
            logger.warning("WebSearchHelper not available for news")
                return {
                    "success": True,
                    "message": "General news - use web search for current news",
                    "suggestion": "Try: 'search for latest technology news'"
                }
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return {"success": False, "error": str(e)}
    
    def web_search(self, query: str) -> Dict[str, Any]:
        """Perform web search using WebSearchHelper for real results."""
        try:
            # Use the WebSearchHelper for actual search results
            from core.ai_engine.web_search import get_web_search_helper
            
            helper = get_web_search_helper()
            
            # Use fast augment_query_with_search with short timeout
            search_results = helper.augment_query_with_search(query, timeout=2.0)  # Fast - 2 seconds max
            if search_results:
                return {
                    "success": True,
                    "query": query,
                    "results": search_results,
                    "url": f"https://html.duckduckgo.com/html/?q={query}"
                }
            
            # No results found
            return {
                "success": False,
                "error": "No search results found",
                "query": query
            }
            
        except ImportError:
            # Fallback if WebSearchHelper not available
            logger.warning("WebSearchHelper not available, using fallback")
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
                return {
                    "success": True,
                    "query": query,
                    "results": f"Search completed for: {query}. Use browser for detailed results.",
                    "url": search_url
                }
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_system_command(self, command: str) -> Dict[str, Any]:
        """Execute system command (with safety checks)."""
        try:
            # Safety: Only allow safe commands
            dangerous_commands = ["rm -rf", "mkfs", "dd if=", "format", "fdisk"]
            if any(dangerous in command.lower() for dangerous in dangerous_commands):
                return {"success": False, "error": "Command blocked for safety"}
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {"success": False, "error": str(e)}
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query and determine if it needs system/internet access."""
        query_lower = query.lower()
        
        # Time queries
        if any(word in query_lower for word in ["time", "what time", "current time", "now"]):
            time_info = self.get_time()
            if time_info.get("success"):
                return {
                    "success": True,
                    "handled": True,
                    "description": f"Current time: {time_info.get('time')}, Date: {time_info.get('date')}"
                }
            return {
                "success": False,
                "handled": True,
                "error": "Unable to get current time",
                "description": "Unable to get current time"
            }
        
        # System info queries
        if any(word in query_lower for word in ["system info", "system information", "cpu", "ram", "memory"]):
            sys_info = self.get_system_info()
            if sys_info.get("success"):
                return {
                    "success": True,
                    "handled": True,
                    "description": f"System: {sys_info.get('os')}, CPU cores: {sys_info.get('cpu_count')}, RAM: {sys_info.get('ram_total_gb')}GB total, {sys_info.get('ram_available_gb')}GB available"
                }
            return {
                "success": False,
                "handled": True,
                "error": "Unable to get system information",
                "description": "Unable to get system information"
            }
        
        # News queries
        if "news" in query_lower:
            # Extract query if present
            if "about" in query_lower or "for" in query_lower:
                parts = query_lower.split("about" if "about" in query_lower else "for", 1)
                news_query = parts[1].strip() if len(parts) > 1 else None
            else:
                news_query = None
            news_result = self.get_news(news_query)
            if news_result.get("success"):
                # Return the actual news results
                description = news_result.get("message") or news_result.get("results", "News information retrieved")
                return {
                    "success": True,
                    "handled": True,
                    "description": description
                }
            return {
                "success": False,
                "handled": True,
                "error": "Unable to get news",
                "description": "Unable to get news"
            }
        
        # Web search queries
        if any(word in query_lower for word in ["search", "find", "look up", "google"]):
            # Extract search query
            for word in ["search for", "find", "look up", "google"]:
                if word in query_lower:
                    parts = query_lower.split(word, 1)
                    search_query = parts[1].strip() if len(parts) > 1 else query
                    search_result = self.web_search(search_query)
                    if search_result.get("success"):
                        # Return the actual search results, not just "Search completed"
                        results = search_result.get('results', '')
                        return {"description": results}
                    return {"description": f"Search failed: {search_result.get('error', 'Unknown error')}"}
            
            # Direct search query
            search_result = self.web_search(query)
            if search_result.get("success"):
                # Return the actual search results
                results = search_result.get('results', '')
                return {"description": results}
            return {"description": f"Search failed: {search_result.get('error', 'Unknown error')}"}
        
        # Default: not a system/internet query
        return None
    
    def handle_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle a query and return response if it's a system/internet query, None otherwise.
        All queries now go through AI - no pre-coded responses."""
        # All queries go through AI - return None to let AI handle everything
        # This allows the AI to use conversation context and web search augmentation
        # The AI will be able to search and provide news in a more natural way
        if any(phrase in query_lower for phrase in ["news", "recent news", "latest news", "what's happening", "current events"]):
            # Try to get news, but if it fails, let AI handle it
            news_query = None
            for phrase in ["about", "on", "for"]:
                if phrase in query_lower:
                    parts = query_lower.split(phrase, 1)
                    if len(parts) > 1:
                        news_query = parts[1].strip()
                        break
            
            news_result = self.get_news(news_query)
            if news_result and news_result.get("success"):
                # Return the actual news results
                description = news_result.get("message") or news_result.get("results", "News information retrieved")
                return {
                    "description": description,
                    "system_query": True,
                    "internet_access": True
                }
            # If get_news returns None or fails, let the AI handle it (return None)
            # The AI will use web search augmentation through conversation context
            return None
        
        # Web search queries
        search_prefixes = ["search for", "look up", "find information about", "what is", "who is", "tell me about"]
        for prefix in search_prefixes:
            if prefix in query_lower:
                search_query = query
                for p in search_prefixes:
                    if p in query_lower:
                        search_query = query.split(p, 1)[1].strip()
                        break
                
                search_result = self.web_search(search_query)
                if search_result.get("success"):
                    return {
                        "description": f"**Search Results:**\n{search_result.get('results', 'Search completed')}",
                        "system_query": True,
                        "internet_access": True
                    }
                else:
                    # Don't return error - let it fall through to AI which can handle it better
                    # or use conversation context
                    return None
        
        # Fall back to process_query for other cases
        result = self.process_query(query)
        if result and result.get("description"):
            return result
        return None
