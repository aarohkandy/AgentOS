import json
import logging
import requests
import subprocess
import sys
import re
import threading
from typing import Dict, Any, Optional

try:
    from core.ai_engine.system_access import SystemAccess
except ImportError:
    # Fallback if module not found
    SystemAccess = None

logger = logging.getLogger(__name__)

class CommandGenerator:
    def __init__(self, model):
        self.model = model
        self._model_lock = threading.Lock()  # Thread safety for model access
        self.system_access = SystemAccess() if SystemAccess else None  # System and internet access
        
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
        
        logger.info(f"CommandGenerator.generate called (model available: {self.model is not None})")
        
        # First, check if this is a system/internet query (time, news, etc.)
        try:
            if self.system_access:
                system_response = self.system_access.handle_query(user_message)
                # Check if query was handled by system access (returns dict with "description" if handled, None otherwise)
                if system_response and system_response.get("description"):
                    logger.info("Handled as system/internet query")
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
                logger.info("Handled as simple query (no GUI actions needed)")
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
        
        if self.model:
            logger.info("Using local model for generation")
            result = self._generate_with_model(user_message, needs_steps=needs_steps)
            # Cache successful results for instant future responses (iOS-quality)
            if result and not result.get("error") and self.cache:
                try:
                    self.cache.set(cache_key, result)
                except Exception as e:
                    logger.debug(f"Cache set failed: {e}")
            return result
        else:
            logger.info("No local model available, using fallback")
            # Try API fallback first
            api_result = self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
            # If API fallback also fails, use rule-based fallback
            if api_result.get("needs_setup") or (api_result.get("fallback_mode") and not api_result.get("description")):
                # Check if this is a GUI command that can be handled by rules
                fallback_plan = self._generate_fallback_plan(user_message)
                if fallback_plan:
                    # Rule-based plan found, use it (it may have plan or just description)
                    # Cache for instant future responses
                    if self.cache:
                        try:
                            self.cache.set(cache_key, fallback_plan)
                        except Exception as e:
                            logger.debug(f"Cache set failed: {e}")
                    return fallback_plan
            # Cache API results too
            if api_result and not api_result.get("error") and self.cache:
                try:
                    self.cache.set(cache_key, api_result)
                except Exception as e:
                    logger.debug(f"Cache set failed: {e}")
            return api_result
    
    
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

    def _generate_with_model(self, user_message, needs_steps=False):
        """Generate response using local AI model with error handling and thread safety."""
        if not self.model:
            return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
        
        # Enhance prompt for step-by-step if needed
        enhanced_prompt = self.system_prompt
        if needs_steps:
            enhanced_prompt += "\n\nIMPORTANT: This is a COMPLEX task requiring multiple steps. Break it into detailed step-by-step actions. For example, 'download and run a program' needs: 1) Open browser, 2) Navigate to download URL, 3) Click download, 4) Wait for download, 5) Open terminal, 6) Run command. Each step should be a separate action in the plan."
        else:
            enhanced_prompt += "\n\nNOTE: This is a SIMPLE task. Provide a direct answer or single action. No need for multiple steps."
        
        prompt = f"{enhanced_prompt}\n\nUser Request: {user_message}\nJSON Plan:"
        
        # Thread-safe model access to prevent concurrent calls
        with self._model_lock:
            try:
                # Log memory usage before generation
                import psutil
                import time
                process = psutil.Process()
                mem_before = process.memory_info().rss / (1024 ** 3)  # GB
                logger.info(f"Starting generation for: '{user_message[:50]}...' (Memory before: {mem_before:.2f} GB)")
                
                # Validate prompt length (some models have limits)
                if len(prompt) > 100000:  # 100K characters
                    logger.warning(f"Prompt too long ({len(prompt)} chars), truncating")
                    prompt = prompt[:100000]
                
                # Use fewer tokens for simple queries (faster responses)
                # Simple queries don't need complex planning
                is_simple = self._is_simple_query(user_message) or not needs_steps
                # iOS-quality: Fast responses with optimal token count
                max_tokens = 128 if is_simple else 512  # More tokens for complex queries, fewer for simple
                
                logger.debug(f"Calling model with prompt length: {len(prompt)} chars, max_tokens: {max_tokens} (simple={is_simple})")
                
                # Log available memory to help diagnose memory issues
                available_mem_gb = psutil.virtual_memory().available / (1024 ** 3)
                total_mem_gb = psutil.virtual_memory().total / (1024 ** 3)
                logger.info(f"System memory: {total_mem_gb:.2f} GB total, {available_mem_gb:.2f} GB available")
                
                # Call model with streaming disabled (we want the full response)
                start_time = time.time()
                logger.info("Model inference starting...")
                
                output = self.model(
                    prompt,
                    max_tokens=max_tokens,
                    stop=["User Request:", "JSON Plan:"],
                    echo=False
                )
                
                elapsed = time.time() - start_time
                logger.info(f"Model inference completed in {elapsed:.2f}s")
                
                # Log memory usage after generation
                mem_after = process.memory_info().rss / (1024 ** 3)  # GB
                mem_delta = mem_after - mem_before
                logger.info(f"Generation complete in {elapsed:.2f}s (Memory after: {mem_after:.2f} GB, delta: {mem_delta:+.2f} GB)")
                
                if not output or 'choices' not in output or len(output['choices']) == 0:
                    logger.error("Model returned invalid output structure")
                    return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
                
                text = output['choices'][0]['text'].strip()
                
                # Use robust JSON extraction
                result = self._extract_json(text)
                if result:
                    return result
                else:
                    # Fallback to conversational response
                    return {"description": text, "fallback_mode": True}
                    
            except SystemError as e:
                # GGML crashes often manifest as SystemError
                logger.error(f"Model crashed with SystemError (GGML assertion?): {e}", exc_info=True)
                logger.warning("Model may be corrupted or incompatible. Falling back to API.")
                # Mark model as potentially broken
                self.model = None
                return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
                
            except RuntimeError as e:
                # Runtime errors from llama-cpp-python
                error_str = str(e).lower()
                if "assert" in error_str or "ggml" in error_str:
                    logger.error(f"Model crashed with RuntimeError (possible GGML issue): {e}", exc_info=True)
                    logger.warning("Model may be corrupted or incompatible. Falling back to API.")
                    self.model = None
                    return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
                else:
                    logger.error(f"Model RuntimeError: {e}", exc_info=True)
                    return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
                    
            except ValueError as e:
                # Invalid parameters or model state
                logger.error(f"Model ValueError (invalid parameters?): {e}", exc_info=True)
                return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
                
            except Exception as e:
                # Catch-all for other exceptions - NEVER crash, always return something
                logger.error(f"Unexpected error generating with model: {type(e).__name__}: {e}", exc_info=True)
                return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)

    def _generate_with_api_fallback(self, user_message, needs_steps=False):
        """Use alternative AI sources when local models aren't available."""
        # Try Ollama first (common local AI server)
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": f"{self.system_prompt}\n\nUser Request: {user_message}\nJSON Plan:",
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 512}
                },
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "").strip()
                if text:
                    # Use robust JSON extraction
                    extracted = self._extract_json(text)
                    if extracted:
                        return extracted
                    # If extraction failed, treat as conversational
                    return {"description": text, "fallback_mode": True}
        except Exception as e:
            logger.debug(f"Ollama API failed: {e}")

        # Try ollama CLI
        try:
            result = subprocess.run(
                ["ollama", "run", "llama3.2", f"{self.system_prompt}\n\nUser Request: {user_message}\nJSON Plan:"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0 and result.stdout:
                text = result.stdout.strip()
                # Use robust JSON extraction
                extracted = self._extract_json(text)
                if extracted:
                    return extracted
                # If extraction failed, treat as conversational
                return {"description": text, "fallback_mode": True}
        except Exception as e:
            logger.debug(f"Ollama CLI failed: {e}")

        # No AI available - return message to install
        logger.error("No AI models available. Please install models or llama-cpp-python.")
        return {
            "description": "I need AI models to function. Please run: ./scripts/install-models.sh",
            "fallback_mode": True,
            "needs_setup": True
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

