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
            if not plan or not isinstance(plan, dict):
                logger.error("Invalid plan: plan is not a dictionary")
                return {"success": False, "error": "Invalid plan format"}
            
            if "error" in plan:
                return {"success": False, "error": plan["error"]}
                
            actions = plan.get("plan", [])
            if not actions:
                return {"success": True, "message": "No actions to execute."}
            
            # Check if this is a complex task that needs step-by-step execution
            is_complex = plan.get("complex", False) or len(actions) > 5
            
            logger.info(f"Executing plan: {plan.get('description', 'Unknown')} ({len(actions)} steps, complex={is_complex})")
            
            executed_steps = 0
            failed_steps = 0
            
            for i, step in enumerate(actions):
                try:
                    if not isinstance(step, dict):
                        logger.warning(f"Step {i+1} is not a dictionary, skipping: {step}")
                        failed_steps += 1
                        continue
                    
                    # For complex tasks, log each step
                    if is_complex:
                        logger.info(f"Step {i+1}/{len(actions)}: {step.get('action', 'unknown')}")
                    
                    self._execute_step(step)
                    executed_steps += 1
                    
                    # Small delay between steps for complex tasks
                    if is_complex and i < len(actions) - 1:
                        time.sleep(0.1)
                        
                except KeyboardInterrupt:
                    logger.warning("Execution interrupted by user")
                    return {"success": False, "error": "Execution interrupted by user", "executed": executed_steps, "total": len(actions)}
                except Exception as e:
                    logger.error(f"Step {i+1}/{len(actions)} failed: {step} - {e}", exc_info=True)
                    failed_steps += 1
                    # Continue with next step instead of failing completely
                    logger.warning(f"Skipping failed step and continuing...")
                    continue
                    
            if failed_steps > 0:
                logger.warning(f"Execution completed with {failed_steps} failed steps out of {len(actions)} total")
                return {"success": True, "warning": f"{failed_steps} steps failed", "executed": executed_steps, "total": len(actions)}
            else:
                return {"success": True, "executed": executed_steps, "total": len(actions)}
        except KeyboardInterrupt:
            logger.warning("Execution interrupted by user")
            return {"success": False, "error": "Execution interrupted by user"}
        except Exception as e:
            logger.error(f"Critical error in executor: {e}", exc_info=True)
            # Never crash - always return error response
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

