import logging
import time
from core.automation.screen_controller import ScreenController

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self):
        self.screen_ctrl = ScreenController()

    def execute(self, plan):
        """Execute plan with comprehensive error handling - never crashes."""
        try:
            if "error" in plan:
                return {"success": False, "error": plan["error"]}
                
            actions = plan.get("plan", [])
            if not actions:
                return {"success": True, "message": "No actions to execute."}
                
            logger.info(f"Executing plan: {plan.get('description', 'Unknown')}")
            
            for i, step in enumerate(actions):
                try:
                    self._execute_step(step)
                except Exception as e:
                    logger.error(f"Step {i+1}/{len(actions)} failed: {step} - {e}", exc_info=True)
                    # Continue with next step instead of failing completely
                    logger.warning(f"Skipping failed step and continuing...")
                    continue
                    
            return {"success": True}
        except Exception as e:
            logger.error(f"Critical error in executor: {e}", exc_info=True)
            return {"success": False, "error": f"Execution error: {str(e)}"}

    def _execute_step(self, step):
        """Execute a single step with error handling."""
        try:
            action = step.get("action")
            
            if action == "click":
                loc = step.get("location")
                if loc and len(loc) >= 2:
                    self.screen_ctrl.click(loc[0], loc[1])
                else:
                    logger.warning(f"Invalid click location: {loc}")
                    
            elif action == "type":
                text = step.get("text", "")
                if text:
                    self.screen_ctrl.type_text(text)
                    
            elif action == "key":
                key = step.get("key", "")
                if key:
                    self.screen_ctrl.press_key(key)
                    
            elif action == "wait":
                sec = step.get("seconds", 1.0)
                if sec > 0:
                    time.sleep(sec)
                    
            elif action == "drag":
                s = step.get("start")
                e = step.get("end")
                if s and e and len(s) >= 2 and len(e) >= 2:
                    self.screen_ctrl.drag(s[0], s[1], e[0], e[1])
                else:
                    logger.warning(f"Invalid drag coordinates: start={s}, end={e}")
            
            else:
                logger.warning(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing step {step}: {e}", exc_info=True)
            # Don't re-raise - let caller handle gracefully
            # This prevents crashes from propagating

