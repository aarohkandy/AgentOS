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
        
        # Store last search results for citation mapping
        self._last_search_results = None
        
        # Cache for AI-based search detection (query -> bool)
        self._ai_search_cache = {}
        
        # System prompt is now handled by ConversationContext with personality support
        # This is kept as a fallback if context is not available
        self.system_prompt = """Fast assistant. JSON only.

Simple questions: {"description": "answer"}
Computer control tasks: {"plan": [{"action": "click", "location": [x,y]}, {"action": "type", "text": "text"}, {"action": "key", "key": "Return"}, {"action": "wait", "seconds": 0.5}], "description": "brief", "estimated_time": N}

WHEN TO CREATE A PLAN:
- User asks to open/launch/start an application → CREATE PLAN with click/type/key actions
- User asks to click something, type something, press keys → CREATE PLAN
- User asks to control the computer in any way → CREATE PLAN
- User asks to navigate, search, interact with GUI → CREATE PLAN
- User asks a question (not a command) → Just {"description": "answer"}

CRITICAL WEB SEARCH RULES:
- If web search results with content are provided (marked with [Current Information from Web Search]), READ THE CONTENT and provide a direct answer
- DO NOT just list URLs or links - synthesize information from the content provided
- Extract key facts from the search result content and give a clear, direct answer to the user's question
- ONLY claim you performed a web search if results are provided in the user's message
- If NO web search results are provided, DO NOT claim you did a web search - be honest that you're using your training data
- If a note says "web search was attempted but no results", be honest about your knowledge limitations
- DO NOT fabricate or make up current information - only use what's provided in web search results

Be instant. No explanations."""

    def _extract_and_map_citations(self, result: Dict[str, Any], content: str, search_results_text: str, search_results_data: list = None) -> Dict[str, Any]:
        """
        Extract citations from response and map them to source URLs.
        
        Args:
            result: Parsed JSON result
            content: Raw response content
            search_results_text: Formatted search results string
            search_results_data: Raw search results list (optional, for better source extraction)
            
        Returns:
            Result dict with sources added
        """
        # Extract citation numbers from content (e.g., [1], [2], [3])
        citation_pattern = r'\[(\d+)\]'
        citations = re.findall(citation_pattern, content)
        
        if not citations:
            return result
        
        sources = []
        source_map = {}
        
        # Try to use raw search results data first (more reliable)
        if search_results_data:
            for i, result_item in enumerate(search_results_data, 1):
                url = result_item.get('url', '')
                title = result_item.get('title', f'Source {i}')
                source_map[i] = {"url": url, "title": title, "index": i}
        else:
            # Fall back to parsing formatted search results text
            source_pattern = r'Source (\d+):\s*([^\n]+)\nURL:\s*([^\n]+)'
            source_matches = re.findall(source_pattern, search_results_text)
            
            # Build sources list with index mapping
            for match in source_matches:
                index = int(match[0])
                title = match[1].strip()
                url = match[2].strip()
                source_map[index] = {"url": url, "title": title, "index": index}
        
        # Add sources that were cited
        cited_indices = set(int(c) for c in citations if c.isdigit())
        for idx in cited_indices:
            if idx in source_map:
                sources.append(source_map[idx])
        
        # Add sources to result
        if sources:
            result["sources"] = sources
        
        return result

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
        
        logger.info(f"📝 Generating response for: {user_message[:50]}...")
        
        # All queries go through AI - no pre-coded responses, no cache checking
        
        # For complex tasks, check if step-by-step planning is needed
        try:
            needs_steps = self._needs_step_by_step(user_message)
        except Exception as e:
            logger.debug(f"Step-by-step check failed: {e}")
            needs_steps = False
        
            # Always use online API (no local models)
        if self.api_client:
            logger.info("🤖 Calling AI API...")
            result = self._generate_with_api(user_message, needs_steps=needs_steps, screen_context=screen_context)
            return result
        else:
            # API client is required - this should never happen if initialized correctly
            logger.error("API client not available - cannot generate response")
            return {
                "description": "API client not available. Please check your .env file and API keys.",
                "error": True
            }
    
    def _generate_with_api(self, user_message: str, needs_steps: bool = False, screen_context: str = None) -> Dict[str, Any]:
        """
        Generate response using online API (Groq/OpenRouter) with conversation context.
        
        Args:
            user_message: The user's message
            needs_steps: Whether the task needs step-by-step planning
            screen_context: Description of screen content (from Vision)
        
        Returns:
            Dict with the command plan or description
        """
        if not self.api_client:
            return self._generate_with_api_fallback(user_message, needs_steps=needs_steps)
        
        try:
            # Augment user message with web search
            # Dual detection: pattern-based (fast) + AI-based (smart)
            augmented_message = user_message
            try:
                from core.ai_engine.web_search import get_web_search_helper, SEARCH_CONFIG
                helper = get_web_search_helper()
                
                # Check if search is needed using dual detection
                # Search ONLY for current/real-time information - not for general queries
                # 1. Pattern-based detection (fast)
                pattern_says_search = helper.needs_web_search(user_message)
                
                # 2. AI-based detection (smart, only if pattern didn't trigger)
                ai_says_search = False
                if not pattern_says_search:
                    ai_says_search = self._ai_detects_search_needed(user_message)
                
                # Perform search ONLY if detection says it needs current information
                # always_try_search means "always try when detection says yes", not "search everything"
                should_search = pattern_says_search or ai_says_search
                
                search_results_text = None
                if should_search:
                    # Log which detection method triggered
                    detection_method = []
                    if pattern_says_search:
                        detection_method.append("pattern")
                    if ai_says_search:
                        detection_method.append("AI")
                    logger.info(f"🔍 Searching web (detected by: {', '.join(detection_method)})...")
                    
                    # Get raw search results for citation mapping
                    try:
                        from core.ai_engine.searxng_client import get_searxng_client
                        searxng_client = get_searxng_client()
                        if searxng_client.is_available():
                            self._last_search_results = searxng_client.search(user_message, num_results=5)
                    except:
                        self._last_search_results = None
                    
                    # Add timeout to prevent slow loading (max 3 seconds - fast enough)
                    search_results_text = helper.augment_query_with_search(user_message, timeout=3.0)
                    if search_results_text:
                        # Add web search results to the user message automatically
                        # Make it very clear that search results contain the answer
                        augmented_message = f"{user_message}\n\n=== CURRENT INFORMATION FROM WEB SEARCH (READ THIS CAREFULLY) ===\n{search_results_text}\n=== END OF SEARCH RESULTS ===\n\nIMPORTANT: The search results above contain the answer to the user's question. Read them carefully and provide a direct, concise answer with citations [1], [2], etc."
                        logger.info(f"✓ Web search complete ({len(search_results_text)} chars)")
                    elif should_search:
                        # If search was attempted but failed, just use original message
                        # Don't add a note - let AI answer from its knowledge naturally
                        logger.debug("Web search attempted but no results, AI will use training knowledge")
                        self._last_search_results = None
                else:
                    self._last_search_results = None
                except Exception as e:
                logger.debug(f"Web search augmentation failed: {e}")
                # Continue without augmentation
            
            # Add screen context if available
            if screen_context:
                augmented_message += f"\n\n[Current Screen Content]:\n{screen_context}"
            
            # Detect query type and apply appropriate personality
            query_type = self._detect_query_type(user_message)
            is_factual = self._is_factual_query(user_message)
            
            # Build the messages with conversation context
            if self.context:
                # Get full conversation history
                messages = self.context.get_context_for_request(augmented_message)
                
                # Check if this is a computer control request
                is_control_request = self._is_control_request(user_message)
                
                # Apply expert personality for factual queries (override user personality)
                if is_factual and messages and messages[0]["role"] == "system":
                    # Add expert tone instruction for factual queries
                    from core.ai_engine.conversation_context import ConversationContext
                    expert_personality = ConversationContext.PERSONALITY_PROMPTS.get("expert", "")
                    if expert_personality:
                        # Append expert personality instructions for this factual query
                        messages[0]["content"] += f"\n\n{expert_personality}\n\nIMPORTANT: For this factual query, use an expert, journalistic, unbiased tone. Provide detailed, well-sourced answers with proper citations."
                
                # Enhance system prompt for control requests
                if messages and messages[0]["role"] == "system":
                    if is_control_request:
                        messages[0]["content"] += "\n\n⚠️ USER WANTS COMPUTER CONTROL - Generate G-code style commands (one per line). Example:\npointer 200 200\nclick 1 s\nwait 1.5\ntype \"text\"\nkey Return\n\nDO NOT use JSON format. Generate simple text commands only."
                    if needs_steps:
                        messages[0]["content"] += "\n\nIMPORTANT: This is a COMPLEX task requiring multiple steps. Break it into detailed step-by-step actions."
            else:
                # No context, build simple messages
                enhanced_prompt = self.system_prompt
                
                # Check if this is a computer control request
                is_control_request = self._is_control_request(user_message)
                if is_control_request:
                    enhanced_prompt += "\n\n⚠️ USER WANTS COMPUTER CONTROL - Generate G-code style commands (one per line). Example:\npointer 200 200\nclick 1 s\nwait 1.5\ntype \"text\"\nkey Return\n\nDO NOT use JSON format. Generate simple text commands only."
                
                if needs_steps:
                    enhanced_prompt += "\n\nIMPORTANT: This is a COMPLEX task requiring multiple steps. Break it into detailed step-by-step actions."
                
                messages = [
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": augmented_message}
                ]
            
            logger.debug(f"Sending request to API with {len(messages)} messages")
            
            # Determine provider preference: Use Google for search queries, Groq for general queries
            # If web search was performed (search_results_text is not None), prefer Google
            # Otherwise, use Groq directly (better rate limits for general knowledge)
            prefer_google = (search_results_text is not None and len(search_results_text) > 0)
            
            if prefer_google:
                logger.info("🔍 Web search detected - using Google Gemini (Groq fallback available)")
            else:
                logger.debug("💬 General query - using Groq (better rate limits)")
            
            # Make the API request
            response = self.api_client.chat(messages, prefer_google=prefer_google)
            
            if "error" in response:
                logger.error(f"API error: {response['error']}")
                return {
                    "description": f"API error: {response['error']}. Please try again.",
                    "error": True
                }
            
            # Extract the response content
            content = response.get("content", "")
            provider = response.get("provider", "unknown")
            model = response.get("model", "unknown")
            
            logger.info(f"✓ Response received from {provider}/{model} ({len(content)} chars)")
            
            # Check if this is a computer control request
            is_control_request = self._is_control_request(user_message)
            
            # Parse response based on request type
            if is_control_request:
                # Computer control: Parse G-code style commands
                from core.automation.command_parser import CommandParser
                parser = CommandParser()
                try:
                    commands = parser.parse(content)
                    if commands:
                        result = {
                            "plan": commands,  # Store as "plan" for compatibility
                            "gcode": content,  # Store original G-code text
                            "description": f"Executing {len(commands)} commands",
                            "estimated_time": len(commands) * 0.5  # Rough estimate
                        }
                    else:
                        logger.warning("Control request but no valid commands found, treating as description")
                        result = {"description": content, "fallback_mode": True}
                except Exception as e:
                    logger.error(f"Error parsing G-code commands: {e}")
                    result = {"description": content, "fallback_mode": True, "error": str(e)}
            else:
                # Question/answer: Comet style - natural markdown response (not JSON)
                # Check if response is JSON (old format) or natural (Comet style)
                json_result = self._extract_json(content)
                if json_result and "description" in json_result:
                    # Old JSON format - extract description
                    result = json_result
                else:
                    # Comet style - natural markdown response
                    result = {"description": content, "comet_style": True}
            
            # Extract citations and map to sources if web search was used
            if result and should_search and search_results_text:
                result = self._extract_and_map_citations(result, content, search_results_text, self._last_search_results)
                # Clear stored results after use
                self._last_search_results = None
            
            # Add metadata about the provider
            if result:
                result["_provider"] = provider
                result["_model"] = model
            
            # Update conversation context with the exchange (use original message, not augmented)
            if self.context and result:
                self.context.add_user_message(user_message)  # Store original, not augmented
                # Store the raw content for context, not the parsed JSON
                self.context.add_assistant_message(content)
            
            return result or {"description": content, "fallback_mode": True}
            
        except Exception as e:
            logger.error(f"Error generating with API: {e}", exc_info=True)
            return {
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

    def _generate_with_api_fallback(self, user_message, needs_steps=False, screen_context=None):
        """Fallback when API is not available - returns error message."""
        logger.error("API client not available - cannot generate response")
        return {
            "description": "API client not available. Please check your .env file and ensure API keys are configured.",
            "fallback_mode": True,
            "needs_setup": True,
            "error": True
        }
    
    def _is_control_request(self, user_message: str) -> bool:
        """Check if user message is requesting computer control (needs a plan)."""
        message_lower = user_message.lower().strip()
        
        # Control action keywords
        control_keywords = [
            "open", "launch", "start", "run", "execute",
            "click", "press", "type", "enter", "input",
            "close", "quit", "exit", "kill",
            "navigate", "go to", "visit", "browse",
            "search for", "find", "look for",
            "move", "drag", "scroll", "swipe",
            "select", "choose", "pick",
            "create", "make", "new", "add",
            "delete", "remove", "clear",
            "copy", "paste", "cut",
            "save", "load", "open file",
            "switch to", "change to", "go back", "go forward"
        ]
        
        # Check if message contains control keywords
        for keyword in control_keywords:
            if keyword in message_lower:
            return True
        
        # Imperative sentences (commands) usually need control
        # Check for imperative patterns
        imperative_patterns = [
            r'^(open|launch|start|run|click|press|type|enter|close|quit|exit|kill|navigate|go|visit|browse|search|find|move|drag|scroll|create|make|delete|remove|copy|paste|save|load|switch|change)',
            r'^(let\'s|let me|can you|please|could you).*(open|launch|start|run|click|press|type|enter|close|quit|exit|navigate|go|visit|browse|search|find|move|drag|create|make|delete|remove|copy|paste|save|load|switch|change)',
        ]
        
        for pattern in imperative_patterns:
            if re.match(pattern, message_lower):
            return True
        
        return False
    
    def _detect_query_type(self, user_message: str) -> str:
        """
        Detect the type of query to apply appropriate formatting rules.
        
        Returns:
            Query type: "news", "people", "coding", "math", "factual", "conversational", "control"
        """
        message_lower = user_message.lower().strip()
        
        # Check for computer control queries FIRST (but only if it's clearly a control request)
        # Don't mistake "what is the latest news" as control
        control_keywords = ["open", "launch", "start", "run", "click", "press", "type", "close", "navigate"]
        if any(keyword in message_lower and (message_lower.startswith(keyword) or f" {keyword} " in message_lower) for keyword in control_keywords):
            if self._is_control_request(user_message):
                return "control"
        
        # News queries (check before control to avoid false positives)
        if any(word in message_lower for word in ["news", "latest", "recent", "breaking", "current events", "today's news"]):
            return "news"
        
        # People queries
        if any(phrase in message_lower for phrase in ["who is", "who was", "tell me about", "biography of"]):
            return "people"
        
        # Coding queries
        if any(word in message_lower for word in ["code", "program", "function", "script", "algorithm", "python", "javascript", "how to code"]):
            return "coding"
        
        # Math queries (check before factual to catch pure math)
        if re.match(r'^[\d+\-*/().\s]+$', user_message.strip()):
            return "math"
        # Simple math questions like "what is 5 * 5"
        if re.match(r'^what is\s+[\d+\-*/().\s]+$', message_lower):
            if re.search(r'\d+\s*[\+\-\*/×÷]\s*\d+', user_message):
                return "math"
        if any(word in message_lower for word in ["calculate", "solve", "compute"]):
            # Check if it's a math expression
            if re.search(r'\d+\s*[\+\-\*/×÷]\s*\d+', user_message):
                return "math"
        
        # Computer control queries (check again if not already identified)
        if self._is_control_request(user_message):
            return "control"
        
        # Factual queries (need expert tone)
        if self._is_factual_query(user_message):
            return "factual"
        
        # Conversational queries
        return "conversational"
    
    def _ai_detects_search_needed(self, user_message: str) -> bool:
        """
        Use AI to intelligently detect if a query needs current/real-time information.
        This is a lightweight check that complements pattern-based detection.
        
        Args:
            user_message: The user's query
            
        Returns:
            True if AI determines the query needs current information
        """
        # Check cache first
        cache_key = user_message.lower().strip()
        if cache_key in self._ai_search_cache:
            return self._ai_search_cache[cache_key]
        
        # Only use AI detection if API client is available
        if not self.api_client:
            return False
        
        try:
            # Lightweight prompt for fast detection
            detection_prompt = f"""Query: "{user_message}"

Does this query require current, real-time, or post-training-cutoff information (after January 2025)?
Examples that need current info: "who is the president", "latest news", "current weather", "what happened today"
Examples that don't: "explain quantum physics", "how does photosynthesis work", "what is 2+2"

Answer with ONLY: yes or no"""
            
            # Make a fast API call with minimal tokens
            # Use Groq for this detection query (general knowledge, not search)
            messages = [
                {"role": "system", "content": "You are a query classifier. Answer only 'yes' or 'no'."},
                {"role": "user", "content": detection_prompt}
            ]
            
            response = self.api_client.chat(messages, prefer_google=False)
            
            if "error" in response:
                logger.debug(f"AI search detection failed: {response.get('error')}")
                return False
            
            content = response.get("content", "").strip().lower()
            
            # Parse yes/no answer
            is_search_needed = "yes" in content and "no" not in content[:10]  # Check first 10 chars to avoid "no" in longer responses
            
            # Cache the result
            self._ai_search_cache[cache_key] = is_search_needed
            
            # Limit cache size
            if len(self._ai_search_cache) > 100:
                # Remove oldest entries (simple FIFO)
                oldest_key = next(iter(self._ai_search_cache))
                del self._ai_search_cache[oldest_key]
            
            logger.debug(f"AI search detection: '{user_message[:50]}...' -> {is_search_needed}")
            return is_search_needed
            
        except Exception as e:
            logger.debug(f"AI search detection error: {e}")
            return False
    
    def _is_factual_query(self, user_message: str) -> bool:
        """
        Determine if query is factual and needs expert/journalistic tone.
        
        Returns:
            True if query is factual (news, research, current events, etc.)
        """
        message_lower = user_message.lower().strip()
        
        # Factual indicators
        factual_keywords = [
            "news", "current", "latest", "recent", "today", "now", "2024", "2025",
            "who is", "what is", "when did", "where is", "how many", "how much",
            "research", "study", "data", "statistics", "report", "according to",
            "search", "find", "look up", "google"
        ]
        
        if any(keyword in message_lower for keyword in factual_keywords):
            return True
        
        # URL in query
        if re.search(r'https?://', user_message):
            return True
        
        # Explicit search request
        if any(phrase in message_lower for phrase in ["search for", "look up", "find information about"]):
            return True
        
            return False
    
    def _needs_step_by_step(self, user_message: str) -> bool:
        """Determine if a task needs step-by-step planning (complex multi-command operations)."""
        message_lower = user_message.lower().strip()
        
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
            r"download.*program", r"install.*software", r"setup.*environment",
            r"create.*file.*and", r"write.*script.*and", r"build.*project",
            r"install.*and", r"download.*and", r"create.*and",
            r"first.*then", r"after.*that"
        ]
        
        for pattern in multi_step_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
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
