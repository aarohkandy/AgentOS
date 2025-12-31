import json
import logging
import sys
import re
from typing import Dict, Any, Optional

try:
    from core.ai_engine.system_access import SystemAccess
except ImportError:
    # Fallback if module not found
    SystemAccess = None

try:
    from core.ai_engine.api_client import UnifiedAPIClient, get_api_client
except ImportError:
    UnifiedAPIClient = None
    get_api_client = None

try:
    from core.ai_engine.conversation_context import ConversationContext, get_conversation_context
except ImportError:
    ConversationContext = None
    get_conversation_context = None

logger = logging.getLogger(__name__)

class CommandGenerator:
    def __init__(self, model=None, api_client: UnifiedAPIClient = None, context: ConversationContext = None, use_online_api: bool = True):
        """
        Initialize the command generator (online API only - no local models).
        
        Args:
            model: Ignored (kept for compatibility, but not used)
            api_client: UnifiedAPIClient for online API calls (required)
            context: ConversationContext for maintaining conversation history (optional)
            use_online_api: Always True - we only use online API
        """
        # No local models - online API only
        self.model = None
        self.use_online_api = True  # Always use online API
        self.system_access = SystemAccess() if SystemAccess else None  # System and internet access
        
        # API client for online inference (Groq/OpenRouter) - REQUIRED
        self.api_client = api_client
        if self.api_client is None and get_api_client is not None:
            try:
                self.api_client = get_api_client()
                logger.info("Initialized UnifiedAPIClient for online inference")
            except Exception as e:
                logger.error(f"Failed to initialize API client: {e}", exc_info=True)
                self.api_client = None
                raise RuntimeError("API client is required but failed to initialize") from e
        
        if self.api_client is None:
            raise RuntimeError("API client is required - cannot initialize CommandGenerator without API client")
        
        # Conversation context for maintaining history
        self.context = context
        if self.context is None and get_conversation_context is not None:
            try:
                self.context = get_conversation_context()
                logger.info("Initialized ConversationContext for conversation history")
            except Exception as e:
                logger.warning(f"Failed to initialize conversation context: {e}")
                self.context = None
        
        # iOS-quality response cache for instant answers
        try:
            from core.ai_engine.response_cache import ResponseCache
            self.cache = ResponseCache(max_size=200, ttl_seconds=7200)
        except ImportError:
            logger.warning("ResponseCache not available, caching disabled")
            self.cache = None
        
        self.system_prompt = """Fast assistant. JSON only.

Simple: {"description": "answer"}
GUI: {"plan": [{"action": "click", "location": [x,y]}, {"action": "type", "text": "text"}, {"action": "key", "key": "Return"}, {"action": "wait", "seconds": 0.5}], "description": "brief", "estimated_time": N}

Be instant. No explanations."""

    def _extract_json(self, text):
        """
        Robustly extract JSON from text that may contain extra content.
        Handles:
        - Markdown code blocks (```json ... ```)
        - Extra text before/after JSON
        - Multiple JSON objects (returns first valid one)
        - Nested braces
        """
        if not text:
            return None
        
        # First, try to strip markdown code blocks
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        # Try direct JSON parse first (fastest path)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Find first opening brace
        start_idx = text.find('{')
        if start_idx == -1:
            # No JSON found, treat as conversational response
            return {"description": text, "fallback_mode": True}
        
        # Find matching closing brace by counting braces
        brace_count = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if brace_count != 0:
            # Unmatched braces, treat as conversational
            return {"description": text, "fallback_mode": True}
        
        # Extract JSON substring
        json_str = text[start_idx:end_idx + 1]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Still invalid JSON, treat as conversational
            return {"description": text, "fallback_mode": True}

    def generate(self, user_message, screen_context=None):
        """Generate a command plan from user message - iOS-quality instant responses."""
        # Handle None or invalid input gracefully
        if user_message is None:
            user_message = ""
        if not isinstance(user_message, str):
            user_message = str(user_message)
        
        # Normalize for cache lookup (strip whitespace, lowercase)
        cache_key = user_message.strip().lower()
        
        # INSTANT: Check cache first for instant responses
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT: {cache_key[:50]}")
                return cached
        
        logger.debug(f"CommandGenerator.generate called (API: {self.api_client is not None})")
        
        # First, check if this is a system/internet query (time, news, etc.)
        try:
            if self.system_access:
                system_response = self.system_access.handle_query(user_message)
                # Check if query was handled by system access (returns dict with "description" if handled, None otherwise)
                if system_response and system_response.get("description"):
                    logger.debug("Handled as system/internet query")
                    result = {
                        "description": system_response.get("description"),
                        "system_query": True
                    }
                    # Cache system queries for instant future responses
                    if self.cache:
                        self.cache.set(cache_key, result)
                    return result
        except Exception as e:
            logger.debug(f"System access check failed: {e}")
            # Fall through to model generation
        
        # Check if this is a simple math/question that doesn't need GUI actions
        try:
            if self._is_simple_query(user_message):
                logger.debug("Handled as simple query (no GUI actions needed)")
                result = self._handle_simple_query(user_message)
                # Cache simple queries for instant future responses
                if result and self.cache:
                    self.cache.set(cache_key, result)
                return result
        except Exception as e:
            logger.debug(f"Simple query check failed: {e}")
        
        # For complex tasks, check if step-by-step planning is needed
        try:
            needs_steps = self._needs_step_by_step(user_message)
        except Exception as e:
            logger.debug(f"Step-by-step check failed: {e}")
            needs_steps = False
        
        # Always use online API (no local models)
        if self.api_client:
            logger.debug("Using online API (Groq/OpenRouter) for generation")
            result = self._generate_with_api(user_message, needs_steps=needs_steps)
            # Cache successful results for instant future responses (iOS-quality)
            if result and not result.get("error") and self.cache:
                try:
                    self.cache.set(cache_key, result)
                except Exception as e:
                    logger.debug(f"Cache set failed: {e}")
            return result
        else:
            # API client is required - this should never happen if initialized correctly
            logger.error("API client not available - cannot generate response")
            # Use rule-based fallback as last resort
            fallback_plan = self._generate_fallback_plan(user_message)
            if fallback_plan and self.cache:
                try:
                    self.cache.set(cache_key, fallback_plan)
                except Exception as e:
                    logger.debug(f"Cache set failed: {e}")
            return fallback_plan or {
                "description": "API client not available. Please check your .env file and API keys.",
                "error": True
            }
    
    def _generate_with_api(self, user_message: str, needs_steps: bool = False) -> Dict[str, Any]:
        """
        Generate response using online API (Groq/OpenRouter) with conversation context.
        
        Args:
            user_message: The user's message
            needs_steps: Whether the task needs step-by-step planning
        
        Returns:
            Dict with the command plan or description
        """
        if not self.api_client:
            return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
        
        try:
            # Build the messages with conversation context
            if self.context:
                # Get full conversation history
                messages = self.context.get_context_for_request(user_message)
                
                # Enhance system prompt for step-by-step if needed
                if needs_steps and messages and messages[0]["role"] == "system":
                    messages[0]["content"] += "\n\nIMPORTANT: This is a COMPLEX task requiring multiple steps. Break it into detailed step-by-step actions."
            else:
                # No context, build simple messages
                enhanced_prompt = self.system_prompt
                if needs_steps:
                    enhanced_prompt += "\n\nIMPORTANT: This is a COMPLEX task requiring multiple steps. Break it into detailed step-by-step actions."
                
                messages = [
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": user_message}
                ]
            
            logger.debug(f"Sending request to API with {len(messages)} messages")
            
            # Make the API request
            response = self.api_client.chat(messages)
            
            if "error" in response:
                logger.error(f"API error: {response['error']}")
                # Fall back to rule-based (no local models)
                return self._generate_fallback_plan(user_message) or {
                    "description": f"API error: {response['error']}. Please try again.",
                    "error": True
                }
            
            # Extract the response content
            content = response.get("content", "")
            provider = response.get("provider", "unknown")
            model = response.get("model", "unknown")
            
            logger.debug(f"Got response from {provider}/{model}")
            
            # Parse the JSON response
            result = self._extract_json(content)
            
            # Add metadata about the provider
            if result:
                result["_provider"] = provider
                result["_model"] = model
            
            # Update conversation context with the exchange
            if self.context and result:
                self.context.add_user_message(user_message)
                # Store the raw content for context, not the parsed JSON
                self.context.add_assistant_message(content)
            
            return result or {"description": content, "fallback_mode": True}
            
        except Exception as e:
            logger.error(f"Error generating with API: {e}", exc_info=True)
            # Fall back to rule-based (no local models)
            return self._generate_fallback_plan(user_message) or {
                "description": f"Error: {str(e)}. Please try again.",
                "error": True
            }
    
    def _format_system_response(self, result: dict, query: str) -> str:
        """Format system/internet response for display."""
        if "time" in result:
            return f"Current time: {result['time']} ({result['date']})"
        elif "os" in result:
            return f"System: {result['os']} {result['os_version']}\nCPU: {result['cpu_count']} cores\nRAM: {result['ram_available_gb']:.1f}GB / {result['ram_total_gb']:.1f}GB available"
        elif "message" in result:
            return result['message']
        elif "results" in result:
            return result['results']
        else:
            return str(result)

    def _generate_with_api_fallback(self, user_message, needs_steps=False):
        """Fallback when API is not available - returns error message."""
        logger.error("API client not available - cannot generate response")
        return {
            "description": "API client not available. Please check your .env file and ensure API keys are configured.",
            "fallback_mode": True,
            "needs_setup": True,
            "error": True
        }
    
    def _is_simple_query(self, user_message: str) -> bool:
        """Check if query is simple and doesn't need GUI actions."""
        message_lower = user_message.lower().strip()
        
        # Simple greetings
        if message_lower in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]:
            return True
        
        # Simple math expressions (e.g., "5*5", "10+20", "100/4")
        # Must contain at least one operator and numbers
        math_pattern = re.match(r'^\s*\d+\s*[\+\-\*/×÷]\s*\d+(\s*[\+\-\*/×÷]\s*\d+)*\s*$', user_message.strip())
        if math_pattern:
            return True
        
        # Simple questions that don't need actions
        simple_patterns = [
            "how are you", "what's up", "who are you", "what can you do",
            "thanks", "thank you", "thx", "bye", "goodbye"
        ]
        if any(pattern in message_lower for pattern in simple_patterns):
            return True
        
        return False
    
    def _handle_simple_query(self, user_message: str) -> Dict[str, Any]:
        """Handle simple queries that don't need GUI actions."""
        message_lower = user_message.lower().strip()
        
        # Handle math expressions
        math_pattern = re.match(r'^[\d+\-*/().\s]+$', user_message.strip())
        if math_pattern:
            try:
                # Safe evaluation of math expression
                result = eval(user_message.replace(" ", "").replace("×", "*").replace("÷", "/"))
                return {
                    "description": f"{user_message} = {result}",
                    "system_query": True
                }
            except:
                pass  # If eval fails, treat as regular query
        
        if message_lower in ["hi", "hello", "hey", "greetings"]:
            return {
                "description": "Hello! 👋 I'm Cosmic AI. How can I help you today?",
                "system_query": True
            }
        
        if message_lower in ["how are you", "what's up"]:
            return {
                "description": "I'm doing great! Ready to help you control your computer. What would you like to do?",
                "system_query": True
            }
        
        if message_lower in ["thanks", "thank you", "thx"]:
            return {
                "description": "You're welcome! 😊",
                "system_query": True
            }
        
        if message_lower in ["bye", "goodbye", "see you"]:
            return {
                "description": "Goodbye! 👋",
                "system_query": True
            }
        
        # Default simple response
        return {
            "description": "I'm here to help! What would you like me to do?",
            "system_query": True
        }
    
    def _needs_step_by_step(self, user_message: str) -> bool:
        """Determine if a task needs step-by-step planning (complex multi-command operations).
        Simple queries like math (5*5) should NOT trigger step-by-step.
        """
        message_lower = user_message.lower().strip()
        
        # First check if it's a simple query (math, greetings, etc.) - these don't need step-by-step
        if self._is_simple_query(user_message):
            return False
        
        # Complex operations that need multiple steps
        complex_keywords = [
            "download and", "install and", "download then", "install then",
            "download and run", "download and install", "install and run",
            "setup", "configure", "create and", "build and", "compile and",
            "multiple", "several", "steps", "step by step"
        ]
        
        if any(keyword in message_lower for keyword in complex_keywords):
            return True
        
        # Tasks that typically require multiple commands
        multi_step_patterns = [
            "download.*program", "install.*software", "setup.*environment",
            "create.*file.*and", "write.*script.*and", "build.*project"
        ]
        
        for pattern in multi_step_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _generate_fallback_plan(self, user_message):
        """
        Rule-based command plan generator for when AI models aren't available.
        Handles common patterns like "open X", "search for Y", etc.
        For conversational messages, returns text-only responses (no plan key).
        """
        message_lower = user_message.lower().strip()
        plan = []
        description = ""
        
        # Pattern: "open [application]"
        if message_lower.startswith("open "):
            app = user_message[5:].strip()
            description = f"Opening {app}"
            plan = [
                {"action": "key", "key": "Super_L"},  # Open application launcher
                {"action": "wait", "seconds": 0.5},
                {"action": "type", "text": app},
                {"action": "wait", "seconds": 0.5},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 2}
            ]
        
        # Pattern: "search for [query]" or "search [query]"
        elif message_lower.startswith("search for ") or message_lower.startswith("search "):
            query = user_message.split("search", 1)[1].replace("for", "").strip()
            description = f"Searching for: {query}"
            plan = [
                {"action": "key", "key": "Super_L"},
                {"action": "wait", "seconds": 0.5},
                {"action": "type", "text": query},
                {"action": "wait", "seconds": 0.5},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 1}
            ]
        
        # Pattern: "go to [url]" or "navigate to [url]"
        elif "go to " in message_lower or "navigate to " in message_lower or "visit " in message_lower:
            url = user_message
            for prefix in ["go to ", "navigate to ", "visit "]:
                if prefix in message_lower:
                    url = user_message.split(prefix, 1)[1].strip()
                    break
            description = f"Navigating to {url}"
            plan = [
                {"action": "key", "key": "Super_L"},
                {"action": "wait", "seconds": 0.5},
                {"action": "type", "text": "firefox"},
                {"action": "wait", "seconds": 0.5},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 2},
                {"action": "type", "text": url},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 2}
            ]
        
        # Pattern: "close [window]" or "close window"
        elif message_lower.startswith("close"):
            description = "Closing window"
            plan = [
                {"action": "key", "key": "Alt+F4"},
                {"action": "wait", "seconds": 0.5}
            ]
        
        # Pattern: "take screenshot" or "screenshot"
        elif "screenshot" in message_lower:
            description = "Taking screenshot"
            plan = [
                {"action": "key", "key": "Print"},
                {"action": "wait", "seconds": 1}
            ]
        
        # Pattern: "download and install [app]" or "download and run [app]"
        elif "download and" in message_lower or "install and" in message_lower:
            # Extract app name
            app = user_message
            for prefix in ["download and install", "download and run", "install and run"]:
                if prefix in message_lower:
                    app = user_message.split(prefix, 1)[1].strip()
                    break
            
            description = f"Downloading and installing {app} (multi-step process)"
            plan = [
                {"action": "key", "key": "Super_L"},
                {"action": "wait", "seconds": 0.5},
                {"action": "type", "text": "terminal"},
                {"action": "wait", "seconds": 0.5},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 2},
                {"action": "type", "text": f"# Download and install {app}"},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 0.5},
                {"action": "type", "text": f"# Step 1: Download {app}"},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 0.5},
                {"action": "type", "text": f"# Step 2: Install {app}"},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 0.5},
            ]
        
        # Pattern: "type [text]"
        elif message_lower.startswith("type "):
            text = user_message[5:].strip()
            description = f"Typing: {text}"
            plan = [
                {"action": "type", "text": text},
                {"action": "wait", "seconds": 0.5}
            ]
        
        # Conversational messages - return text-only response (no plan key)
        elif message_lower in ["hi", "hello", "hey", "greetings"]:
            return {
                "description": "Hello! 👋 I'm Cosmic AI. I can help you control your computer with natural language.\n\nTry commands like:\n• \"open firefox\"\n• \"search for cats\"\n• \"take screenshot\"\n\nNote: I'm currently using rule-based fallback mode. Install AI models for full capabilities: ./scripts/install-models.sh",
                "fallback_mode": True
            }
        
        elif message_lower in ["help", "what can you do", "what do you do"]:
            return {
                "description": "I can help you control your computer! Here are some things you can ask me:\n\n📱 **Applications:**\n• \"open firefox\" - Open an application\n• \"open calculator\" - Launch any app\n\n🔍 **Search:**\n• \"search for cats\" - Search your system\n\n🌐 **Web:**\n• \"go to github.com\" - Navigate to a website\n\n📸 **Actions:**\n• \"take screenshot\" - Capture your screen\n• \"close window\" - Close current window\n\n💡 **Tip:** Install AI models for more advanced capabilities: ./scripts/install-models.sh",
                "fallback_mode": True
            }
        
        elif message_lower in ["thanks", "thank you", "thx"]:
            return {
                "description": "You're welcome! 😊 Is there anything else I can help you with?",
                "fallback_mode": True
            }
        
        elif message_lower in ["bye", "goodbye", "see you"]:
            return {
                "description": "Goodbye! 👋 Feel free to come back anytime.",
                "fallback_mode": True
            }
        
        # Questions about capabilities
        elif any(word in message_lower for word in ["what", "how", "can you", "do you", "?"]):
            return {
                "description": "I can help you control your computer through natural language commands. Try asking me to:\n• Open applications\n• Search for files or content\n• Navigate to websites\n• Take screenshots\n• And more!\n\nFor complex requests, install AI models: ./scripts/install-models.sh",
                "fallback_mode": True
            }
        
        # Default: Show message that AI model is needed (but don't return empty plan)
        else:
            # For unrecognized messages, return a helpful text response instead of empty plan
            return {
                "description": f"I'm not sure how to handle '{user_message}' in fallback mode.\n\nI can help with commands like:\n• \"open [app]\" - Open an application\n• \"search for [query]\" - Search your system\n• \"go to [url]\" - Navigate to a website\n• \"take screenshot\" - Capture screen\n\nFor more advanced capabilities, install AI models:\n./scripts/install-models.sh",
                "fallback_mode": True
            }
        
        # Only return command plan if we have actual actions
        if plan:
            estimated_time = sum(step.get("seconds", 0.1) for step in plan if step.get("action") == "wait") + len(plan) * 0.1
            
            return {
                "plan": plan,
                "description": description,
                "estimated_time": round(estimated_time, 1),
                "fallback_mode": True
            }
        else:
            # No plan generated, return text-only response
            return {
                "description": description,
                "fallback_mode": True
            }
    
    def clear_context(self):
        """Clear the conversation context."""
        if self.context:
            self.context.clear()
            logger.info("Conversation context cleared")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation context."""
        if self.context:
            return self.context.get_summary()
        return {"message": "No conversation context available"}
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get the status of the API client."""
        if self.api_client:
            return self.api_client.get_status()
        return {"message": "No API client available", "use_online_api": self.use_online_api}
