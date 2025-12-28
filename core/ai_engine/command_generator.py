import json
import logging

logger = logging.getLogger(__name__)

class CommandGenerator:
    def __init__(self, model):
        self.model = model
        self.system_prompt = """You are an AI assistant that controls a Linux computer GUI.
You receive a user request and must output a JSON sequence of actions to fulfill it.
Available actions:
- {"action": "click", "target": "name_or_desc", "location": [x, y], "button": "left"|"right"}
- {"action": "type", "text": "string to type"}
- {"action": "key", "key": "key_name" (e.g., Return, Super_L, control+c)}
- {"action": "wait", "seconds": float}
- {"action": "drag", "start": [x1, y1], "end": [x2, y2]}

Output ONLY valid JSON.
Example:
{
    "plan": [
        {"action": "click", "target": "firefox_icon", "location": [100, 50]},
        {"action": "wait", "seconds": 2},
        {"action": "type", "text": "gmail.com"},
        {"action": "key", "key": "Return"}
    ],
    "description": "Opening Firefox and navigating to Gmail",
    "estimated_time": 5
}
"""

    def generate(self, user_message, screen_context=None):
        if not self.model:
            # Smart fallback: Generate basic command plans from common patterns
            return self._generate_fallback_plan(user_message)

        prompt = f"{self.system_prompt}\n\nUser Request: {user_message}\nJSON Plan:"
        
        try:
            # This is a synchronous call to the model
            output = self.model(
                prompt,
                max_tokens=512,
                stop=["User Request:", "JSON Plan:"],
                echo=False
            )
            text = output['choices'][0]['text'].strip()
            
            # Basic JSON cleanup if needed
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error generating command plan: {e}")
            logger.info("Falling back to rule-based generation")
            return self._generate_fallback_plan(user_message)
    
    def _generate_fallback_plan(self, user_message):
        """
        Rule-based command plan generator for when AI models aren't available.
        Handles common patterns like "open X", "search for Y", etc.
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
        
        # Default: Show message that AI model is needed
        else:
            description = f"AI model not loaded. For complex requests like '{user_message}', please install AI models."
            plan = []
            logger.info(f"Fallback generator: No pattern matched for '{user_message}'. Install models for full AI support.")
        
        estimated_time = sum(step.get("seconds", 0.1) for step in plan if step.get("action") == "wait") + len(plan) * 0.1
        
        return {
            "plan": plan,
            "description": description,
            "estimated_time": round(estimated_time, 1),
            "fallback_mode": True
        }
