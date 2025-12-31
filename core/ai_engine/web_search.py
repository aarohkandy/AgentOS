"""
Web Search Helper for Cosmic OS AI.

Provides web search capabilities using DuckDuckGo (no API key required).
Can be used to augment AI responses with current information.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)


class WebSearchHelper:
    """
    Helper class for performing web searches to augment AI responses.
    Uses DuckDuckGo's instant answer API (no API key required).
    """
    
    # DuckDuckGo Instant Answer API
    DDG_API_URL = "https://api.duckduckgo.com/"
    
    # Patterns that suggest a query needs web search
    WEB_SEARCH_PATTERNS = [
        r'\b(current|latest|recent|today|now|live)\b',
        r'\b(news|weather|stock|price|score)\b',
        r'\b(who is|what is|where is)\b.*\b(now|currently|today)\b',
        r'\b(2024|2025)\b',  # Recent years
        r'\b(happening|trending)\b',
    ]
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the web search helper.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.WEB_SEARCH_PATTERNS]
    
    def needs_web_search(self, query: str) -> bool:
        """
        Determine if a query likely needs web search for current information.
        
        Args:
            query: The user's query
        
        Returns:
            True if the query likely needs current information
        """
        for pattern in self._compiled_patterns:
            if pattern.search(query):
                return True
        return False
    
    def search_instant_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get an instant answer from DuckDuckGo.
        
        Args:
            query: The search query
        
        Returns:
            Dict with answer information or None if no instant answer
        """
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(
                self.DDG_API_URL,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "CosmicOS/1.0"}
            )
            
            if response.status_code != 200:
                logger.warning(f"DuckDuckGo API returned {response.status_code}")
                return None
            
            data = response.json()
            
            # Check for abstract (main answer)
            if data.get("Abstract"):
                return {
                    "type": "abstract",
                    "answer": data["Abstract"],
                    "source": data.get("AbstractSource", ""),
                    "url": data.get("AbstractURL", ""),
                    "image": data.get("Image", "")
                }
            
            # Check for answer (direct answer like calculations)
            if data.get("Answer"):
                return {
                    "type": "answer",
                    "answer": data["Answer"],
                    "source": "DuckDuckGo",
                    "url": ""
                }
            
            # Check for definition
            if data.get("Definition"):
                return {
                    "type": "definition",
                    "answer": data["Definition"],
                    "source": data.get("DefinitionSource", ""),
                    "url": data.get("DefinitionURL", "")
                }
            
            # Check for related topics
            if data.get("RelatedTopics"):
                topics = data["RelatedTopics"][:3]  # Get top 3
                summaries = []
                for topic in topics:
                    if isinstance(topic, dict) and topic.get("Text"):
                        summaries.append(topic["Text"])
                
                if summaries:
                    return {
                        "type": "related",
                        "answer": "\n".join(summaries),
                        "source": "DuckDuckGo",
                        "url": ""
                    }
            
            return None
            
        except requests.exceptions.Timeout:
            logger.warning("DuckDuckGo search timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in web search: {e}")
            return None
    
    def search_html(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a web search and return results (scrapes DuckDuckGo HTML).
        
        Note: This is a fallback method. The instant answer API is preferred.
        
        Args:
            query: The search query
            num_results: Maximum number of results to return
        
        Returns:
            List of result dicts with 'title', 'url', 'snippet'
        """
        try:
            # Use DuckDuckGo HTML search
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                }
            )
            
            if response.status_code != 200:
                return []
            
            # Simple HTML parsing (avoid BeautifulSoup dependency)
            results = []
            html = response.text
            
            # DuckDuckGo HTML structure - try multiple patterns
            # Pattern 1: Modern DuckDuckGo structure
            patterns = [
                # Pattern for result links with snippets
                re.compile(
                    r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?'
                    r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([^<]*)</a>',
                    re.DOTALL | re.IGNORECASE
                ),
                # Pattern for web results
                re.compile(
                    r'<a[^>]*class="[^"]*web-result[^"]*"[^>]*href="([^"]*)"[^>]*>.*?'
                    r'<span[^>]*class="[^"]*result__title[^"]*"[^>]*>([^<]*)</span>.*?'
                    r'<span[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([^<]*)</span>',
                    re.DOTALL | re.IGNORECASE
                ),
                # Generic pattern for any links with text
                re.compile(
                    r'<a[^>]*href="(https?://[^"]+)"[^>]*>.*?'
                    r'<span[^>]*>([^<]+)</span>.*?'
                    r'<span[^>]*>([^<]+)</span>',
                    re.DOTALL | re.IGNORECASE
                ),
            ]
            
            for pattern in patterns:
                matches = pattern.findall(html)
                if matches:
                    for match in matches[:num_results]:
                        if len(match) >= 3:
                            url, title, snippet = match[0], match[1], match[2]
                            # Filter out non-news URLs and validate
                            if url.startswith('http') and len(title.strip()) > 5:
                                results.append({
                                    "title": title.strip(),
                                    "url": url,
                                    "snippet": snippet.strip() if snippet else ""
                                })
                    if results:
                        break
            
            # If still no results, try a simpler approach - just extract any links with text
            if not results:
                # Look for any links that might be news
                link_pattern = re.compile(
                    r'<a[^>]*href="(https?://[^"]+)"[^>]*>([^<]{10,})</a>',
                    re.IGNORECASE
                )
                matches = link_pattern.findall(html)
                seen_urls = set()
                for url, title in matches[:num_results * 2]:  # Get more to filter
                    if url.startswith('http') and url not in seen_urls:
                        # Skip DuckDuckGo internal links
                        if 'duckduckgo.com' not in url and len(title.strip()) > 10:
                            seen_urls.add(url)
                            results.append({
                                "title": title.strip(),
                                "url": url,
                                "snippet": ""
                            })
                            if len(results) >= num_results:
                                break
            
            return results[:num_results]
            
        except Exception as e:
            logger.warning(f"HTML search failed: {e}")
            return []
    
    def format_search_results(self, results: List[Dict[str, str]]) -> str:
        """
        Format search results into a readable string.
        
        Args:
            results: List of search result dicts
        
        Returns:
            Formatted string with search results
        """
        if not results:
            return "No search results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result['title']}")
            if result.get('snippet'):
                formatted.append(f"   {result['snippet']}")
            if result.get('url'):
                formatted.append(f"   URL: {result['url']}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def augment_query_with_search(self, query: str) -> Optional[str]:
        """
        Augment a query with web search results if needed.
        
        Args:
            query: The user's query
        
        Returns:
            Additional context from web search, or None if not needed/available
        """
        if not self.needs_web_search(query):
            return None
        
        # Try instant answer first
        instant = self.search_instant_answer(query)
        if instant:
            answer = instant["answer"]
            source = instant.get("source", "")
            if source:
                return f"[Web Search Result from {source}]: {answer}"
            return f"[Web Search Result]: {answer}"
        
        # Fall back to HTML search
        results = self.search_html(query, num_results=3)
        if results:
            formatted = self.format_search_results(results)
            return f"[Web Search Results]:\n{formatted}"
        
        return None


# Singleton instance
_search_instance: Optional[WebSearchHelper] = None


def get_web_search_helper(**kwargs) -> WebSearchHelper:
    """Get or create the singleton web search helper instance."""
    global _search_instance
    if _search_instance is None:
        _search_instance = WebSearchHelper(**kwargs)
    return _search_instance


def search_web(query: str) -> Optional[str]:
    """
    Convenience function to search the web.
    
    Args:
        query: The search query
    
    Returns:
        Search results as a string, or None if no results
    """
    helper = get_web_search_helper()
    return helper.augment_query_with_search(query)

