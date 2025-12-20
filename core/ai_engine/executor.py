import logging
import time
from core.automation.screen_controller import ScreenController

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self):
        self.screen_ctrl = ScreenController()

    def execute(self, plan):
        if "error" in plan:
            return {"success": False, "error": plan["error"]}
            
        actions = plan.get("plan", [])
        if not actions:
            return {"success": True, "message": "No actions to execute."}
            
        logger.info(f"Executing plan: {plan.get('description', 'Unknown')}")
        
        for step in actions:
            try:
                self._execute_step(step)
            except Exception as e:
                logger.error(f"Step failed: {step} - {e}")
                return {"success": False, "error": str(e), "failed_step": step}
                
        return {"success": True}

    def _execute_step(self, step):
        action = step.get("action")
        
        if action == "click":
            loc = step.get("location")
            if loc:
                self.screen_ctrl.click(loc[0], loc[1])
                
        elif action == "type":
            text = step.get("text", "")
            self.screen_ctrl.type_text(text)
            
        elif action == "key":
            key = step.get("key", "")
            self.screen_ctrl.press_key(key)
            
        elif action == "wait":
            sec = step.get("seconds", 1.0)
            time.sleep(sec)
            
        elif action == "drag":
            s = step.get("start")
            e = step.get("end")
            if s and e:
                self.screen_ctrl.drag(s[0], s[1], e[0], e[1])
        
        else:
            logger.warning(f"Unknown action: {action}")
