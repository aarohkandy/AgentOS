import logging
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
from core.automation.screen_controller import ScreenController
from core.vision.vision import VisionEngine

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self, vision_engine=None, api_client=None):
        self.screen_ctrl = ScreenController()
        self.vision = vision_engine or VisionEngine()
        self.task_queue = None
        self.api_client = api_client
        self.executor_binary_path = None
        self._find_executor_binary()

    def _find_executor_binary(self):
        """Find the executor binary path."""
        project_root = Path(__file__).resolve().parent.parent.parent
        possible_paths = [
            project_root / "core" / "automation" / "executor_binary",
            project_root / "executor_binary",
            Path("/usr/local/bin/executor_binary"),
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                self.executor_binary_path = str(path)
                logger.debug(f"Found executor binary at: {self.executor_binary_path}")
                return
        
        logger.warning("Executor binary not found - will use Python execution fallback")
        self.executor_binary_path = None
    
    def execute(self, plan):
        """Execute plan with comprehensive error handling - never crashes."""
        try:
            if not plan or not isinstance(plan, dict):
                logger.error("Invalid plan: plan is not a dictionary")
                return {"success": False, "error": "Invalid plan format"}
            
            if "error" in plan:
                return {"success": False, "error": plan["error"]}
            
            # Check if plan has G-code format
            gcode = plan.get("gcode")
            if gcode:
                # Use executor binary if available
                if self.executor_binary_path:
                    return self._execute_with_binary(gcode)
                else:
                    # Fallback to Python execution
                    logger.info("Using Python execution fallback (binary not available)")
            
            actions = plan.get("plan", [])
            if not actions:
                return {"success": True, "message": "No actions to execute."}
            
            # Check if this is a complex task that needs step-by-step execution
            is_complex = plan.get("complex", False) or len(actions) > 5
            
            logger.info(f"Executing plan: {plan.get('description', 'Unknown')} ({len(actions)} steps, complex={is_complex})")
            
            executed_steps = 0
            failed_steps = 0
            screenshots = []
            
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
                    
                    # Take screenshot after action (for verification)
                    screenshot_path = self._take_screenshot(i+1, step.get("action", "unknown"))
                    if screenshot_path:
                        screenshots.append(screenshot_path)
                    
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
            
            result = {
                "success": True,
                "executed": executed_steps,
                "total": len(actions),
                "screenshots": screenshots
            }
            
            if failed_steps > 0:
                logger.warning(f"Execution completed with {failed_steps} failed steps out of {len(actions)} total")
                result["warning"] = f"{failed_steps} steps failed"
            
            return result
        except KeyboardInterrupt:
            logger.warning("Execution interrupted by user")
            return {"success": False, "error": "Execution interrupted by user"}
        except Exception as e:
            logger.error(f"Critical error in executor: {e}", exc_info=True)
            # Never crash - always return error response
            return {"success": False, "error": f"Execution error: {str(e)}"}
    
    def _execute_with_binary(self, gcode: str) -> Dict:
        """Execute G-code commands using the executor binary."""
        import tempfile
        
        try:
            # Write G-code to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.gcode', delete=False) as f:
                f.write(gcode)
                temp_file = f.name
            
            # Execute binary
            cmd = [self.executor_binary_path, "--screenshots-dir", "/tmp/cosmic-screenshots", temp_file]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
            
            if result.returncode != 0:
                logger.error(f"Executor binary failed: {result.stderr}")
                return {"success": False, "error": f"Binary execution failed: {result.stderr}"}
            
            # Parse JSON output
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError:
                logger.error(f"Could not parse binary output: {result.stdout}")
                return {"success": False, "error": "Could not parse binary output"}
        
        except subprocess.TimeoutExpired:
            logger.error("Executor binary timed out")
            return {"success": False, "error": "Execution timed out"}
        except Exception as e:
            logger.error(f"Error executing binary: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _take_screenshot(self, step: int, action: str) -> Optional[str]:
        """Take a screenshot after an action."""
        try:
            from core.vision.screenshot import ScreenshotManager
            screenshot_mgr = ScreenshotManager()
            filename = f"screenshot_step_{step}_{action}_{int(time.time())}.png"
            path = screenshot_mgr.capture_screen(filename)
            return str(path) if path else None
        except Exception as e:
            logger.debug(f"Could not take screenshot: {e}")
            return None

    def _execute_step(self, step):
        """Execute a single step with error handling. Supports both old JSON format and new G-code format."""
        try:
            action = step.get("action")
            
            # G-code style commands (new format)
            if action == "pointer":
                x = step.get("x")
                y = step.get("y")
                if x is not None and y is not None:
                    self.screen_ctrl.mousemove(x, y)
                else:
                    logger.warning(f"Invalid pointer coordinates: x={x}, y={y}")
            
            elif action == "click":
                # G-code format: click button clicks (coordinates should be set by previous pointer command)
                # But we can also have click with coordinates directly
                button = step.get("button", 1)
                clicks = step.get("clicks", "single")
                
                # Check if coordinates are in this step (from parser)
                if "x" in step and "y" in step:
                    x, y = step["x"], step["y"]
                    self.screen_ctrl.click(x, y, button=button)
                    if clicks == "double":
                        time.sleep(0.1)
                        self.screen_ctrl.click(x, y, button=button)
                else:
                    # Old format: click with location
                    loc = step.get("location")
                    if loc and len(loc) >= 2:
                        self.screen_ctrl.click(loc[0], loc[1], button=button)
                        if clicks == "double":
                            time.sleep(0.1)
                            self.screen_ctrl.click(loc[0], loc[1], button=button)
                    else:
                        # No coordinates - click at current mouse position
                        logger.warning(f"Click command without coordinates - using current mouse position")
                        # Use xdotool to click at current position
                        import subprocess
                        subprocess.run(["xdotool", "click", str(button)], check=False)
                        if clicks == "double":
                            time.sleep(0.1)
                            subprocess.run(["xdotool", "click", str(button)], check=False)
                    
            elif action == "type":
                text = step.get("text", "")
                if text:
                    self.screen_ctrl.type_text(text)
                    
            elif action == "key":
                key = step.get("key", "")
                if key:
                    self.screen_ctrl.press_key(key)
            
            elif action == "keycombo":
                combo = step.get("combo", "")
                if combo:
                    # Parse combo like "Ctrl+Shift+T"
                    keys = combo.split("+")
                    # Press all modifier keys, then main key
                    for key in keys[:-1]:
                        self.screen_ctrl.press_key(key.strip())
                    self.screen_ctrl.press_key(keys[-1].strip())
                    # Release in reverse
                    for key in reversed(keys[:-1]):
                        self.screen_ctrl.press_key(f"{key.strip()}Up")
                    
            elif action == "wait":
                sec = step.get("seconds", 1.0)
                if sec > 0:
                    time.sleep(sec)
            
            elif action == "drag":
                # G-code format: drag x1 y1 x2 y2 duration
                if "x1" in step:
                    x1 = step.get("x1")
                    y1 = step.get("y1")
                    x2 = step.get("x2")
                    y2 = step.get("y2")
                    duration = step.get("duration", 1.0)
                    self.screen_ctrl.drag(x1, y1, x2, y2)
                else:
                    # Old format: drag with start/end
                    s = step.get("start")
                    e = step.get("end")
                    if s and e and len(s) >= 2 and len(e) >= 2:
                        self.screen_ctrl.drag(s[0], s[1], e[0], e[1])
                    else:
                        logger.warning(f"Invalid drag coordinates: start={s}, end={e}")
            
            elif action == "scroll":
                x = step.get("x")
                y = step.get("y")
                amount = step.get("amount", 3)
                if x is not None and y is not None:
                    # Move to position, then scroll
                    self.screen_ctrl.click(x, y, button=0)  # Move mouse
                    # Use xdotool to scroll
                    import subprocess
                    subprocess.run(["xdotool", "click", "--repeat", abs(amount), "4" if amount > 0 else "5"], check=False)
            
            elif action == "screenshot":
                filename = step.get("filename", f"screenshot_{int(time.time())}.png")
                from core.vision.screenshot import ScreenshotManager
                screenshot_mgr = ScreenshotManager()
                screenshot_mgr.capture_screen(filename)
                logger.info(f"Screenshot saved: {filename}")
                    
            elif action == "wait_for_text":
                text = step.get("text")
                timeout = step.get("timeout", 5.0)
                if text:
                    self._wait_for_text(text, timeout)
                    
            elif action == "click_text":
                text = step.get("text")
                if text:
                    self._click_text(text)
                    
            elif action == "schedule_task":
                command = step.get("command")
                if command and self.task_queue:
                    logger.info(f"Scheduling background task: {command}")
                    self.task_queue.add_task(command, type="general")
                elif not self.task_queue:
                    logger.warning("Cannot schedule task: task_queue not initialized")
            
            else:
                logger.warning(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error executing step {step}: {e}", exc_info=True)
            # Don't re-raise - let caller handle gracefully
            # This prevents crashes from propagating

    def _wait_for_text(self, text, timeout):
        """Wait for text to appear on screen."""
        logger.info(f"Waiting for text '{text}' (timeout: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            coords = self.vision.find_text(text)
            if coords:
                logger.info(f"Found '{text}' at {coords}")
                return True
            time.sleep(0.5)
            # Force refresh after first check
            self.vision.analyze_screen(force_refresh=True)
            
        logger.warning(f"Timeout waiting for text '{text}'")
        return False

    def _click_text(self, text):
        """Find text on screen and click it."""
        logger.info(f"Attempting to click text '{text}'...")
        # Try to find it immediately (maybe cached)
        coords = self.vision.find_text(text)
        
        # If not found, force refresh and try again
        if not coords:
            self.vision.analyze_screen(force_refresh=True)
            coords = self.vision.find_text(text)
            
        if coords:
            x, y = coords
            logger.info(f"Clicking '{text}' at {int(x)}, {int(y)}")
            self.screen_ctrl.click(int(x), int(y))
            return True
        else:
            logger.warning(f"Could not find text '{text}' to click")
            return False

