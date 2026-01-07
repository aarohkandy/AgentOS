"""
Unified API Client for Google Gemini, Groq, and OpenRouter with automatic key rotation and fallback.

Features:
- Primary: Google Gemini API (gemini-3-flash-preview)
- Fallback: Groq API (faster, 30 RPM, 14,400 RPD)
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
    Unified API client that tries Google Gemini first, then falls back to Groq, then OpenRouter.
    Automatically rotates through API keys on rate limits or errors.
    """
    
    # API Endpoints
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Default models (updated January 2025)
    # Google Gemini models
    DEFAULT_GOOGLE_MODEL = "gemini-3-flash-preview"
    DEFAULT_GOOGLE_FALLBACK_MODEL = "gemini-3-flash-preview"
    # Groq production models: llama-3.3-70b-versatile (best), llama-3.1-8b-instant (fastest)
    DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"
    # OpenRouter free models
    DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
    DEFAULT_OPENROUTER_FALLBACK_MODEL = "qwen/qwen-2.5-72b-instruct:free"
    
    def __init__(
        self,
        google_model: str = None,
        google_fallback_model: str = None,
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
            google_model: Primary Google Gemini model (default: gemini-3-flash-preview)
            google_fallback_model: Fallback Google model (default: gemini-3-flash-preview)
            groq_model: Primary Groq model (default: llama-3.3-70b-versatile)
            groq_fallback_model: Fallback Groq model (default: llama-3.1-8b-instant)
            openrouter_model: Primary OpenRouter model (default: meta-llama/llama-3.2-3b-instruct:free)
            openrouter_fallback_model: Fallback OpenRouter model (default: qwen/qwen-2.5-72b-instruct:free)
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 512)
            timeout: Request timeout in seconds (default: 30)
        """
        # Load API keys from environment
        raw_google_keys = self._load_keys("GOOGLE_KEY", 3)
        raw_groq_keys = self._load_keys("GROQ_KEY", 3)
        raw_openrouter_keys = self._load_keys("OPENROUTER_KEY", 3)
        
        # Validate and filter API keys
        self.google_keys = self._validate_and_filter_keys(raw_google_keys, "Google", "AIza")
        self.groq_keys = self._validate_and_filter_keys(raw_groq_keys, "GROQ", "gsk_")
        self.openrouter_keys = self._validate_and_filter_keys(raw_openrouter_keys, "OpenRouter", "sk-or-v1-")
        
        # Raise exception if no valid keys found
        if len(self.google_keys) == 0 and len(self.groq_keys) == 0 and len(self.openrouter_keys) == 0:
            raise ValueError(
                "No valid API keys found. Please check your .env file.\n"
                "1. Ensure you have a .env file in the project root.\n"
                "2. Add GOOGLE_KEY_1=AIza... or GROQ_KEY_1=gsk_... or OPENROUTER_KEY_1=sk-or-v1-...\n"
                "3. Keys must start with 'AIza' (Google), 'gsk_' (Groq), or 'sk-or-v1-' (OpenRouter)."
            )
        
        # Model configuration
        self.google_model = google_model or self.DEFAULT_GOOGLE_MODEL
        self.google_fallback_model = google_fallback_model or self.DEFAULT_GOOGLE_FALLBACK_MODEL
        self.groq_model = groq_model or self.DEFAULT_GROQ_MODEL
        self.groq_fallback_model = groq_fallback_model or self.DEFAULT_GROQ_FALLBACK_MODEL
        self.openrouter_model = openrouter_model or self.DEFAULT_OPENROUTER_MODEL
        self.openrouter_fallback_model = openrouter_fallback_model or self.DEFAULT_OPENROUTER_FALLBACK_MODEL
        
        # Generation parameters
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Track current key indices for rotation
        self._google_key_index = 0
        self._groq_key_index = 0
        self._openrouter_key_index = 0
        
        # Track last used provider/model for logging
        self._last_provider = None
        self._last_model = None
        self._last_key_index = None
        
        # Log validation status
        google_valid_count, groq_valid_count, openrouter_valid_count = self.validate_keys()
        if google_valid_count == 0:
            logger.warning("No valid Google API keys found. Check .env file and ensure keys start with 'AIza'")
        if groq_valid_count == 0:
            logger.warning("No valid Groq API keys found. Check .env file and ensure keys start with 'gsk_'")
        if openrouter_valid_count == 0:
            logger.warning("No valid OpenRouter API keys found. Check .env file and ensure keys start with 'sk-or-v1-'")
        logger.debug(f"UnifiedAPIClient: {google_valid_count} valid Google keys, {groq_valid_count} valid Groq keys, {openrouter_valid_count} valid OpenRouter keys")
    
    def _load_keys(self, prefix: str, count: int) -> List[str]:
        """Load API keys from environment variables."""
        keys = []
        for i in range(1, count + 1):
            key = os.getenv(f"{prefix}_{i}")
            if key:
                keys.append(key)
        return keys
    
    def _validate_key_format(self, key: str, key_type: str) -> bool:
        """
        Validate API key format.
        
        Args:
            key: The API key to validate
            key_type: Either 'groq' or 'openrouter'
        
        Returns:
            True if key format is valid, False otherwise
        """
        if not key or not key.strip():
            return False
        
        key = key.strip()
        
        if key_type == "groq":
            # Groq keys typically start with 'gsk_'
            return key.startswith("gsk_")
        elif key_type == "openrouter":
            # OpenRouter keys typically start with 'sk-or-v1-'
            return key.startswith("sk-or-v1-")
        
        return False
    
    def _validate_and_filter_keys(self, keys: List[str], provider_name: str, expected_prefix: str) -> List[str]:
        """
        Validate and filter API keys, keeping only valid ones.
        
        Args:
            keys: List of raw keys to validate
            provider_name: Name of the provider (for logging)
            expected_prefix: Expected prefix for valid keys
        
        Returns:
            List of valid keys
        """
        valid_keys = []
        for i, key in enumerate(keys, 1):
            if not key or not key.strip():
                logger.warning(f"{provider_name} key {i} is empty")
                continue
            if not key.startswith(expected_prefix):
                logger.warning(f"{provider_name} key {i} has invalid format (should start with '{expected_prefix}')")
                continue
            valid_keys.append(key)
            logger.debug(f"{provider_name} key {i} is valid")
        
        return valid_keys
    
    def validate_keys(self) -> Tuple[int, int, int]:
        """
        Validate API keys format and return counts of valid keys.
        
        Returns:
            Tuple of (google_valid_count, groq_valid_count, openrouter_valid_count)
        """
        google_valid_count = len(self.google_keys)
        groq_valid_count = len(self.groq_keys)
        openrouter_valid_count = len(self.openrouter_keys)
        
        # Log summary
        if google_valid_count == 0:
            logger.warning("No valid Google API keys found. Check your .env file.")
        if groq_valid_count == 0:
            logger.warning("No valid Groq API keys found. Check your .env file.")
        if openrouter_valid_count == 0:
            logger.warning("No valid OpenRouter API keys found. Check your .env file.")
        
        return google_valid_count, groq_valid_count, openrouter_valid_count
    
    def _convert_messages_to_google_format(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to Google's contents format.
        
        Args:
            messages: List of dicts with 'role' and 'content' keys
        
        Returns:
            Formatted string for Google API
        """
        formatted_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if not content:
                continue
                
            if role == "system":
                # System message as instruction (prepend to conversation)
                formatted_parts.insert(0, f"System: {content}")
            elif role == "user":
                formatted_parts.append(f"User: {content}")
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(formatted_parts)
    
    def _make_google_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        key_index: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make a request to Google Gemini API.
        
        Returns:
            Tuple of (response_dict, error_message)
        """
        if key_index >= len(self.google_keys):
            return None, "No more Google keys available"
        
        key = self.google_keys[key_index]
        
        try:
            from google import genai
        except ImportError:
            logger.warning("⚠️  google-genai package not installed - Google API unavailable")
            return None, "google-genai package not installed"
        
        try:
            start_time = time.time()
            logger.info(f"→ Google API: {model} (key {key_index + 1})")
            
            # Create client with API key
            client = genai.Client(api_key=key)
            
            # Convert messages to Google format
            contents = self._convert_messages_to_google_format(messages)
            
            # Make API call
            response = client.models.generate_content(
                model=model,
                contents=contents,
            )
            
            elapsed = time.time() - start_time
            
            # Extract response text
            if hasattr(response, 'text') and response.text:
                result = {
                    "content": response.text,
                    "provider": "google",
                    "model": model
                }
                self._last_provider = "google"
                self._last_model = model
                self._last_key_index = key_index
                logger.info(f"✓ Google response: {elapsed:.2f}s")
                return result, None
            else:
                error_msg = "Google API returned empty response"
                logger.error(f"✗ {error_msg}")
                return None, error_msg
                
        except Exception as e:
            error_str = str(e).lower()
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            
            # Check for rate limiting
            if "rate limit" in error_str or "429" in error_str or "quota" in error_str:
                logger.warning(f"⚠️  Google rate limit (key {key_index + 1}) - will fallback to Groq")
                return None, "rate_limit"
            elif "invalid" in error_str and "key" in error_str:
                logger.error(f"✗ Google invalid API key (key {key_index + 1}) - will fallback to Groq")
                return None, "invalid_key"
            elif "model" in error_str and ("not found" in error_str or "invalid" in error_str):
                logger.error(f"✗ Google model not found: {model} - will fallback to Groq")
                return None, "model_not_found"
            else:
                error_msg = f"Google error: {str(e)[:200]}"
                logger.warning(f"⚠️  {error_msg} - will fallback to Groq")
                return None, error_msg
    
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
            start_time = time.time()
            logger.info(f"→ Groq API: {model} (key {key_index + 1})")
            response = requests.post(
                self.GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self._last_provider = "groq"
                self._last_model = model
                self._last_key_index = key_index
                logger.info(f"✓ Groq response: {elapsed:.2f}s")
                return result, None
            elif response.status_code == 429:
                logger.warning(f"⚠ Groq rate limit (key {key_index + 1})")
                return None, "rate_limit"
            else:
                error_msg = f"Groq error {response.status_code}: {response.text[:200]}"
                logger.error(f"✗ {error_msg}")
                return None, error_msg
                
        except requests.exceptions.Timeout:
            logger.error(f"✗ Groq timeout (key {key_index + 1})")
            return None, "timeout"
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Groq request failed: {e}")
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
            start_time = time.time()
            logger.info(f"→ OpenRouter API: {model} (key {key_index + 1})")
            response = requests.post(
                self.OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self._last_provider = "openrouter"
                self._last_model = model
                self._last_key_index = key_index
                logger.info(f"✓ OpenRouter response: {elapsed:.2f}s")
                return result, None
            elif response.status_code == 429:
                logger.warning(f"⚠ OpenRouter rate limit (key {key_index + 1})")
                return None, "rate_limit"
            else:
                error_msg = f"OpenRouter error {response.status_code}: {response.text[:200]}"
                logger.error(f"✗ {error_msg}")
                return None, error_msg
                
        except requests.exceptions.Timeout:
            logger.error(f"✗ OpenRouter timeout (key {key_index + 1})")
            return None, "timeout"
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ OpenRouter request failed: {e}")
            return None, str(e)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        use_fallback_model: bool = False,
        prefer_google: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request with automatic key rotation and fallback.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            use_fallback_model: If True, use fallback models instead of primary
            prefer_google: If True, try Google first (for web search queries). If False, skip Google and use Groq.
        
        Returns:
            Dict with 'content' (response text), 'provider', 'model', or 'error'
        """
        if not messages:
            return {"error": "No messages provided"}
        
        # Determine which models to use
        google_model = self.google_fallback_model if use_fallback_model else self.google_model
        groq_model = self.groq_fallback_model if use_fallback_model else self.groq_model
        openrouter_model = self.openrouter_fallback_model if use_fallback_model else self.openrouter_model
        
        errors = []
        
        # Try Google only if prefer_google=True (e.g., for web search queries)
        if prefer_google and len(self.google_keys) > 0:
            logger.info("🔍 Using Google Gemini for search query (Groq fallback available)")
            # Try all Google keys with primary model
            for i in range(len(self.google_keys)):
                key_index = (self._google_key_index + i) % len(self.google_keys)
                result, error = self._make_google_request(messages, google_model, key_index)
                
                if result:
                    # Update key index for next request (round-robin)
                    self._google_key_index = (key_index + 1) % len(self.google_keys)
                    # Google response is already in the correct format
                    return result
                
                if error:
                    errors.append(f"Google key {key_index + 1}: {error}")
                    if error not in ["rate_limit", "timeout"]:
                        # Non-recoverable error, try next key
                        continue
            
            # Try Google with fallback model if primary failed
            if not use_fallback_model and google_model != self.google_fallback_model:
                logger.debug(f"Trying Google fallback model: {self.google_fallback_model}")
                for i in range(len(self.google_keys)):
                    key_index = (self._google_key_index + i) % len(self.google_keys)
                    result, error = self._make_google_request(messages, self.google_fallback_model, key_index)
                    
                    if result:
                        self._google_key_index = (key_index + 1) % len(self.google_keys)
                        return result
                    
                    if error:
                        errors.append(f"Google fallback key {key_index + 1}: {error}")
            
            # Google failed for search query, fallback to Groq
            logger.info("⚠️  Google failed for search query, falling back to Groq...")
        elif not prefer_google:
            # General query - use Groq directly (better rate limits)
            logger.debug("💬 General query - using Groq (better rate limits)")
        
        # Use Groq (either directly for general queries, or as fallback for search queries)
        
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
        # Google responses are already in the correct format (returned directly from _make_google_request)
        if "content" in api_response and "provider" in api_response:
            return api_response
        
        # OpenAI-compatible format (Groq/OpenRouter)
        try:
            content = api_response["choices"][0]["message"]["content"]
            return {
                "content": content,
                "provider": self._last_provider,
                "model": self._last_model,
                "key_index": self._last_key_index + 1 if self._last_key_index is not None else None
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract response: {e}")
            return {"error": f"Invalid API response format: {e}"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the API client."""
        return {
            "google_keys_available": len(self.google_keys),
            "groq_keys_available": len(self.groq_keys),
            "openrouter_keys_available": len(self.openrouter_keys),
            "google_model": self.google_model,
            "google_fallback_model": self.google_fallback_model,
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

