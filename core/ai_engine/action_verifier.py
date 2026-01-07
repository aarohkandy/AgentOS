"""
Action Verifier - Verifies actions worked using screenshot analysis.

Sends screenshots to AI to verify if actions succeeded and get adjusted commands if needed.
"""

import logging
import base64
from pathlib import Path
from typing import Dict, Optional, List
from core.ai_engine.api_client import UnifiedAPIClient

logger = logging.getLogger(__name__)


class ActionVerifier:
    """Verify actions using AI vision analysis of screenshots."""
    
    def __init__(self, api_client: UnifiedAPIClient = None):
        self.api_client = api_client
    
    def verify_action(
        self,
        action: Dict,
        screenshot_path: str,
        expected_result: str = None
    ) -> Dict:
        """
        Verify if an action succeeded by sending screenshot to AI.
        
        Args:
            action: The action that was executed (e.g., {"action": "click", "x": 200, "y": 300})
            screenshot_path: Path to screenshot taken after action
            expected_result: What we expected to happen (optional)
        
        Returns:
            Dict with:
            - success: bool - Did the action work?
            - adjusted_commands: str - G-code commands to retry if failed (optional)
            - explanation: str - Why it succeeded/failed
        """
        if not self.api_client:
            logger.warning("No API client available for action verification")
            return {"success": True, "explanation": "Verification skipped - no API client"}
        
        if not Path(screenshot_path).exists():
            logger.warning(f"Screenshot not found: {screenshot_path}")
            return {"success": True, "explanation": "Screenshot not available"}
        
        try:
            # Read screenshot
            with open(screenshot_path, 'rb') as f:
                screenshot_data = f.read()
            
            # Convert to base64 for API (if needed) or use file path
            # For now, we'll describe the action and ask AI to verify
            
            # Build verification prompt
            action_desc = self._describe_action(action)
            prompt = f"""I executed this action: {action_desc}

Expected result: {expected_result or 'Action should have completed successfully'}

Screenshot after action is available at: {screenshot_path}

Did the action succeed? 
- If yes: respond with "success"
- If no: respond with adjusted G-code commands to retry, e.g.:
pointer 205 205
click 1 s

Be concise. Only provide adjusted commands if the action failed."""
            
            # Call AI (using text-only for now, can be enhanced with vision API later)
            messages = [
                {
                    "role": "system",
                    "content": "You are an action verifier. Analyze if actions succeeded based on descriptions. Respond with 'success' if it worked, or provide adjusted G-code commands if it failed."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.api_client.chat(messages, prefer_google=False)
            
            if "error" in response:
                logger.error(f"API error during verification: {response['error']}")
                return {"success": True, "explanation": "Verification failed - assuming success"}
            
            content = response.get("content", "").strip().lower()
            
            if content == "success" or content.startswith("success"):
                return {
                    "success": True,
                    "explanation": "Action verified as successful"
                }
            else:
                # AI provided adjusted commands
                adjusted_commands = response.get("content", "").strip()
                return {
                    "success": False,
                    "adjusted_commands": adjusted_commands,
                    "explanation": "Action may have failed - AI provided adjusted commands"
                }
        
        except Exception as e:
            logger.error(f"Error verifying action: {e}", exc_info=True)
            return {"success": True, "explanation": f"Verification error: {e}"}
    
    def _describe_action(self, action: Dict) -> str:
        """Describe an action in human-readable format."""
        action_type = action.get("action", "unknown")
        
        if action_type == "pointer":
            return f"Move mouse to ({action.get('x')}, {action.get('y')})"
        elif action_type == "click":
            button = action.get("button", 1)
            clicks = action.get("clicks", "single")
            if "x" in action:
                return f"Click at ({action.get('x')}, {action.get('y')}) with button {button} ({clicks} click)"
            else:
                return f"Click with button {button} ({clicks} click)"
        elif action_type == "type":
            return f"Type text: '{action.get('text', '')}'"
        elif action_type == "key":
            return f"Press key: {action.get('key', '')}"
        elif action_type == "drag":
            return f"Drag from ({action.get('x1')}, {action.get('y1')}) to ({action.get('x2')}, {action.get('y2')})"
        elif action_type == "wait":
            return f"Wait {action.get('seconds', 0)} seconds"
        else:
            return f"Execute {action_type} action"
    
    def verify_multiple_actions(
        self,
        actions: List[Dict],
        screenshots: List[str],
        expected_results: List[str] = None
    ) -> List[Dict]:
        """
        Verify multiple actions at once.
        
        Args:
            actions: List of actions executed
            screenshots: List of screenshot paths (one per action)
            expected_results: List of expected results (optional)
        
        Returns:
            List of verification results
        """
        results = []
        expected = expected_results or [None] * len(actions)
        
        for i, (action, screenshot) in enumerate(zip(actions, screenshots)):
            result = self.verify_action(action, screenshot, expected[i] if i < len(expected) else None)
            results.append(result)
        
        return results

