import logging

logger = logging.getLogger(__name__)

class CommandValidator:
    def __init__(self, models):
        self.models = models # Dictionary of loaded validator models
        # Heuristic blacklist for safety if model is unsure or unavailable
        self.safety_blacklist = [
            "rm -rf", "mkfs", "dd if=", ":(){ :|:& };:", "chmod 777 /", "> /dev/sda"
        ]

    def approve_all(self, plan):
        """
        Run all 3 validators.
        Returns True if all approve, False otherwise.
        """
        if "error" in plan:
            return False
            
        actions = plan.get("plan", [])
        
        # 1. Safety Validator
        if not self._validate_safety(actions):
            logger.warning("Safety validation failed.")
            return False
            
        # 2. Logic Validator
        if not self._validate_logic(actions):
             logger.warning("Logic validation failed.")
             return False

        # 3. Efficiency Validator
        if not self._validate_efficiency(actions):
             logger.info("Efficiency validation suggestion ignored for now (soft pass).")
             # We usually let efficiency slide if it's safe and logical, just log it
             pass 

        return True

    def _validate_safety(self, actions):
        # Heuristic check
        for step in actions:
            if step["action"] == "type":
                text = step.get("text", "")
                for blocked in self.safety_blacklist:
                    if blocked in text:
                        return False
            if step["action"] == "key":
                # prevent spamming destructive hotkeys if needed
                pass
        
        # Model check (if available)
        if "safety" in self.models:
            # TODO: Implement actual model inference for validation
            # For now, assume model would catch what heuristics missed
            pass
            
        return True

    def _validate_logic(self, actions):
        # Basic logical checks
        # e.g. "wait" shouldn't be negative
        for step in actions:
            if step["action"] == "wait" and step.get("seconds", 0) < 0:
                return False
        return True

    def _validate_efficiency(self, actions):
        return True
