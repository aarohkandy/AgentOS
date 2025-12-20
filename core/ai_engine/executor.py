import logging
import time
import subprocess
import shutil

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self):
        self.xdotool_path = shutil.which("xdotool")
        if not self.xdotool_path:
            logger.warning("xdotool not found. GUI execution will fail.")

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
                self._run_xdotool(f"mousemove {loc[0]} {loc[1]} click 1")
                
        elif action == "type":
            text = step.get("text", "")
            # escape double quotes
            text = text.replace('"', '\\"')
            self._run_xdotool(f"type --delay 50 \"{text}\"")
            
        elif action == "key":
            key = step.get("key", "")
            self._run_xdotool(f"key {key}")
            
        elif action == "wait":
            sec = step.get("seconds", 1.0)
            time.sleep(sec)
            
        elif action == "drag":
            # Drag logic usually involves mousedown -> mousemove -> mouseup
            s = step.get("start")
            e = step.get("end")
            if s and e:
                self._run_xdotool(f"mousemove {s[0]} {s[1]} mousedown 1 mousemove {e[0]} {e[1]} mouseup 1")
        
        else:
            logger.warning(f"Unknown action: {action}")

    def _run_xdotool(self, args):
        if not self.xdotool_path:
            logger.info(f"[Dry Run] xdotool {args}")
            return
            
        cmd = f"{self.xdotool_path} {args}"
        subprocess.run(cmd, shell=True, check=True)
