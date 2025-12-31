"""
Unified API Client for Groq and OpenRouter with automatic key rotation and fallback.

Features:
- Primary: Groq API (faster, 30 RPM, 14,400 RPD)
- Fallback: OpenRouter API (20 RPM, 50 RPD)
- Automatic key rotation on rate limits (429) or errors
- Model fallback within each provider
- Full conversation context support
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import requests

# Try to import dotenv, but make it optional with fallback
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    # Fallback: simple .env file parser
    def load_dotenv(dotenv_path, override=False):
        """Simple .env file parser (fallback when python-dotenv not available)."""
        if not isinstance(dotenv_path, Path):
            dotenv_path = Path(dotenv_path)
        if not dotenv_path.exists():
            return False
        try:
            with open(dotenv_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if override or key not in os.environ:
                            os.environ[key] = value
            return True
        except Exception:
            return False

logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Try multiple paths to find .env file
env_paths = [
    Path(__file__).resolve().parent.parent.parent / ".env",  # Project root
    Path.cwd() / ".env",  # Current working directory
    Path.home() / "Downloads" / "agentOS" / ".env",  # Common location
    Path("/media/sf_agentOS/.env"),  # Shared folder location
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        try:
            if HAS_DOTENV:
                load_dotenv(env_path)
            else:
                load_dotenv(env_path, override=False)
            env_loaded = True
            logger.debug(f"Loaded .env from: {env_path}")
            break
        except Exception as e:
            logger.debug(f"Failed to load .env from {env_path}: {e}")
            continue

if not env_loaded:
    logger.warning(f"Could not find .env file. Tried: {[str(p) for p in env_paths]}")


class UnifiedAPIClient:
    """
    Unified API client that tries Groq first, then falls back to OpenRouter.
    Automatically rotates through API keys on rate limits or errors.
    """
    
    # API Endpoints
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Default models (updated December 2024)
    # Groq production models: llama-3.3-70b-versatile (best), llama-3.1-8b-instant (fastest)
    DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"
    # OpenRouter free models
    DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
    DEFAULT_OPENROUTER_FALLBACK_MODEL = "qwen/qwen-2.5-72b-instruct:free"
    
    def __init__(
        self,
        groq_model: str = None,
        groq_fallback_model: str = None,
        openrouter_model: str = None,
        openrouter_fallback_model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        timeout: int = 30
    ):
        """
        Initialize the unified API client.
        
        Args:
            groq_model: Primary Groq model (default: llama-3.1-70b-versatile)
            groq_fallback_model: Fallback Groq model (default: mixtral-8x7b-32768)
            openrouter_model: Primary OpenRouter model (default: deepseek/deepseek-chat)
            openrouter_fallback_model: Fallback OpenRouter model (default: google/gemini-flash-1.5)
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 512)
            timeout: Request timeout in seconds (default: 30)
        """
        # Load API keys from environment
        self.groq_keys = self._load_keys("GROQ_KEY", 3)
        self.openrouter_keys = self._load_keys("OPENROUTER_KEY", 3)
        
        # Model configuration
        self.groq_model = groq_model or self.DEFAULT_GROQ_MODEL
        self.groq_fallback_model = groq_fallback_model or self.DEFAULT_GROQ_FALLBACK_MODEL
        self.openrouter_model = openrouter_model or self.DEFAULT_OPENROUTER_MODEL
        self.openrouter_fallback_model = openrouter_fallback_model or self.DEFAULT_OPENROUTER_FALLBACK_MODEL
        
        # Generation parameters
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Track current key indices for rotation
        self._groq_key_index = 0
        self._openrouter_key_index = 0
        
        # Track last used provider/model for logging
        self._last_provider = None
        self._last_model = None
        self._last_key_index = None
        
        # Log initialization (only if keys are missing)
        if len(self.groq_keys) == 0:
            logger.warning("No Groq API keys found in .env file")
        if len(self.openrouter_keys) == 0:
            logger.warning("No OpenRouter API keys found in .env file")
        logger.debug(f"UnifiedAPIClient: {len(self.groq_keys)} Groq keys, {len(self.openrouter_keys)} OpenRouter keys")
    
    def _load_keys(self, prefix: str, count: int) -> List[str]:
        """Load API keys from environment variables."""
        keys = []
        for i in range(1, count + 1):
            key = os.getenv(f"{prefix}_{i}")
            if key:
                keys.append(key)
        return keys
    
    def _make_groq_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        key_index: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make a request to Groq API.
        
        Returns:
            Tuple of (response_dict, error_message)
        """
        if key_index >= len(self.groq_keys):
            return None, "No more Groq keys available"
        
        key = self.groq_keys[key_index]
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        
        try:
            logger.debug(f"Groq request: model={model}, key_index={key_index}")
            response = requests.post(
                self.GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self._last_provider = "groq"
                self._last_model = model
                self._last_key_index = key_index
                return result, None
            elif response.status_code == 429:
                logger.debug(f"Groq rate limit hit (key {key_index + 1})")
                return None, "rate_limit"
            else:
                error_msg = f"Groq error {response.status_code}: {response.text[:200]}"
                logger.debug(error_msg)
                return None, error_msg
                
        except requests.exceptions.Timeout:
            logger.debug(f"Groq request timeout (key {key_index + 1})")
            return None, "timeout"
        except requests.exceptions.RequestException as e:
            logger.debug(f"Groq request failed: {e}")
            return None, str(e)
    
    def _make_openrouter_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        key_index: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make a request to OpenRouter API.
        
        Returns:
            Tuple of (response_dict, error_message)
        """
        if key_index >= len(self.openrouter_keys):
            return None, "No more OpenRouter keys available"
        
        key = self.openrouter_keys[key_index]
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cosmic-os.local",
            "X-Title": "Cosmic OS AI Assistant"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            logger.debug(f"OpenRouter request: model={model}, key_index={key_index}")
            response = requests.post(
                self.OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self._last_provider = "openrouter"
                self._last_model = model
                self._last_key_index = key_index
                return result, None
            elif response.status_code == 429:
                logger.debug(f"OpenRouter rate limit hit (key {key_index + 1})")
                return None, "rate_limit"
            else:
                error_msg = f"OpenRouter error {response.status_code}: {response.text[:200]}"
                logger.debug(error_msg)
                return None, error_msg
                
        except requests.exceptions.Timeout:
            logger.debug(f"OpenRouter request timeout (key {key_index + 1})")
            return None, "timeout"
        except requests.exceptions.RequestException as e:
            logger.debug(f"OpenRouter request failed: {e}")
            return None, str(e)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        use_fallback_model: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request with automatic key rotation and fallback.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            use_fallback_model: If True, use fallback models instead of primary
        
        Returns:
            Dict with 'content' (response text), 'provider', 'model', or 'error'
        """
        if not messages:
            return {"error": "No messages provided"}
        
        # Determine which models to use
        groq_model = self.groq_fallback_model if use_fallback_model else self.groq_model
        openrouter_model = self.openrouter_fallback_model if use_fallback_model else self.openrouter_model
        
        errors = []
        
        # Try all Groq keys with primary model
        for i in range(len(self.groq_keys)):
            key_index = (self._groq_key_index + i) % len(self.groq_keys)
            result, error = self._make_groq_request(messages, groq_model, key_index)
            
            if result:
                # Update key index for next request (round-robin)
                self._groq_key_index = (key_index + 1) % len(self.groq_keys)
                return self._extract_response(result)
            
            if error:
                errors.append(f"Groq key {key_index + 1}: {error}")
                if error not in ["rate_limit", "timeout"]:
                    # Non-recoverable error, try next key
                    continue
        
        # Try Groq with fallback model if primary failed
        if not use_fallback_model and groq_model != self.groq_fallback_model:
            logger.debug(f"Trying Groq fallback model: {self.groq_fallback_model}")
            for i in range(len(self.groq_keys)):
                key_index = (self._groq_key_index + i) % len(self.groq_keys)
                result, error = self._make_groq_request(messages, self.groq_fallback_model, key_index)
                
                if result:
                    self._groq_key_index = (key_index + 1) % len(self.groq_keys)
                    return self._extract_response(result)
                
                if error:
                    errors.append(f"Groq fallback key {key_index + 1}: {error}")
        
        # Groq failed, try OpenRouter
        logger.debug("Groq exhausted, falling back to OpenRouter...")
        
        # Try all OpenRouter keys with primary model
        for i in range(len(self.openrouter_keys)):
            key_index = (self._openrouter_key_index + i) % len(self.openrouter_keys)
            result, error = self._make_openrouter_request(messages, openrouter_model, key_index)
            
            if result:
                self._openrouter_key_index = (key_index + 1) % len(self.openrouter_keys)
                return self._extract_response(result)
            
            if error:
                errors.append(f"OpenRouter key {key_index + 1}: {error}")
        
        # Try OpenRouter with fallback model
        if not use_fallback_model and openrouter_model != self.openrouter_fallback_model:
            logger.debug(f"Trying OpenRouter fallback model: {self.openrouter_fallback_model}")
            for i in range(len(self.openrouter_keys)):
                key_index = (self._openrouter_key_index + i) % len(self.openrouter_keys)
                result, error = self._make_openrouter_request(messages, self.openrouter_fallback_model, key_index)
                
                if result:
                    self._openrouter_key_index = (key_index + 1) % len(self.openrouter_keys)
                    return self._extract_response(result)
                
                if error:
                    errors.append(f"OpenRouter fallback key {key_index + 1}: {error}")
        
        # All providers and keys exhausted
        logger.warning(f"All API keys exhausted. Errors: {len(errors)}")
        return {
            "error": "All API keys exhausted",
            "details": errors
        }
    
    def _extract_response(self, api_response: Dict) -> Dict[str, Any]:
        """Extract the response content from API response."""
        try:
            content = api_response["choices"][0]["message"]["content"]
            return {
                "content": content,
                "provider": self._last_provider,
                "model": self._last_model,
                "key_index": self._last_key_index + 1  # 1-indexed for logging
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract response: {e}")
            return {"error": f"Invalid API response format: {e}"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the API client."""
        return {
            "groq_keys_available": len(self.groq_keys),
            "openrouter_keys_available": len(self.openrouter_keys),
            "groq_model": self.groq_model,
            "groq_fallback_model": self.groq_fallback_model,
            "openrouter_model": self.openrouter_model,
            "openrouter_fallback_model": self.openrouter_fallback_model,
            "last_provider": self._last_provider,
            "last_model": self._last_model
        }


# Singleton instance for easy access
_client_instance: Optional[UnifiedAPIClient] = None


def get_api_client(**kwargs) -> UnifiedAPIClient:
    """Get or create the singleton API client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = UnifiedAPIClient(**kwargs)
    return _client_instance


def reset_api_client():
    """Reset the singleton instance (useful for testing)."""
    global _client_instance
    _client_instance = None

