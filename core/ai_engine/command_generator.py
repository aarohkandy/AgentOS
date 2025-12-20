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
            # Fallback for testing/NO-AI mode
            return {
                "plan": [],
                "description": "AI not loaded. Echo: " + user_message,
                "estimated_time": 0
            }

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
            return {"error": str(e)}
