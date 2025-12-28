import json
import logging
import requests
import subprocess
import sys
import re

logger = logging.getLogger(__name__)

class CommandGenerator:
    def __init__(self, model):
        self.model = model
        self.system_prompt = """You are Cosmic AI, an intelligent assistant that controls a Linux computer GUI through natural language.

When the user wants to perform actions, output a JSON plan with these available actions:
- {"action": "click", "target": "name_or_desc", "location": [x, y], "button": "left"|"right"}
- {"action": "type", "text": "string to type"}
- {"action": "key", "key": "key_name" (e.g., Return, Super_L, control+c)}
- {"action": "wait", "seconds": float}
- {"action": "drag", "start": [x1, y1], "end": [x2, y2]}

For conversational messages (greetings, questions, chat), respond naturally with only:
{
    "description": "Your natural, friendly, conversational response here"
}

For action requests, output:
{
    "plan": [list of actions],
    "description": "What you're doing",
    "estimated_time": seconds
}

Always respond intelligently and naturally. Be helpful and conversational."""

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
        if self.model:
            return self._generate_with_model(user_message)
        else:
            # Try to use online AI API as fallback
            return self._generate_with_api_fallback(user_message)

    def _generate_with_model(self, user_message):
        """Generate response using local AI model."""
        prompt = f"{self.system_prompt}\n\nUser Request: {user_message}\nJSON Plan:"
        
        try:
            output = self.model(
                prompt,
                max_tokens=512,
                stop=["User Request:", "JSON Plan:"],
                echo=False
            )
            text = output['choices'][0]['text'].strip()
            
            # Use robust JSON extraction
            result = self._extract_json(text)
            if result:
                return result
            else:
                # Fallback to conversational response
                return {"description": text, "fallback_mode": True}
        except Exception as e:
            logger.error(f"Error generating with model: {e}")
            return self._generate_with_api_fallback(user_message)

    def _generate_with_api_fallback(self, user_message):
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

