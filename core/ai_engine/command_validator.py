import logging

logger = logging.getLogger(__name__)

class CommandValidator:
    def __init__(self, models):
        self.models = models # Dictionary of loaded validator models
        # Heuristic blacklist for safety if model is unsure or unavailable
        self.safety_blacklist = [
            "rm -rf", "mkfs", "dd if=", ":(){ :|:& };:", "chmod 777 /", "> /dev/sda",
            "format", "fdisk", "parted", "mkfs.ext", "mkfs.ntfs", "wipefs"
        ]
        
        # Log validator status
        self._log_validator_status()
    
    def _log_validator_status(self):
        """Log which validators are active (AI models vs heuristics)."""
        status = []
        for name in ["safety", "logic", "efficiency"]:
            if name in self.models and self.models[name] is not None:
                status.append(f"{name.capitalize()}: AI model")
            else:
                status.append(f"{name.capitalize()}: Heuristics")
        logger.info(f"Validators active: {', '.join(status)}")

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
        """
        Safety validator: Checks for destructive or dangerous commands.
        Uses AI model if available, otherwise falls back to heuristics.
        """
        # Heuristic check (always runs as first line of defense)
        for step in actions:
            if step.get("action") == "type":
                text = step.get("text", "").lower()
                for blocked in self.safety_blacklist:
                    if blocked.lower() in text:
                        logger.warning(f"Safety validator (heuristic): Blocked dangerous text: {blocked}")
                        return False
            if step.get("action") == "key":
                key = step.get("key", "").lower()
                # Block dangerous key combinations
                dangerous_keys = ["ctrl+alt+del", "ctrl+alt+f1", "ctrl+alt+f2"]
                if any(dk in key for dk in dangerous_keys):
                    logger.warning(f"Safety validator (heuristic): Blocked dangerous key combo: {key}")
                    return False
        
        # AI model check (if available)
        if "safety" in self.models and self.models["safety"] is not None:
            try:
                # Use AI model for more sophisticated safety checking
                actions_json = str(actions)
                prompt = f"""Is this command sequence safe to execute? Answer only YES or NO.
                
Command sequence: {actions_json}

Answer:"""
                
                result = self.models["safety"](
                    prompt,
                    max_tokens=10,
                    stop=["\n"],
                    echo=False
                )
                
                response = result['choices'][0]['text'].strip().upper()
                if "NO" in response or "UNSAFE" in response or "DANGEROUS" in response:
                    logger.warning(f"Safety validator (AI): Rejected unsafe command sequence")
                    return False
                logger.debug(f"Safety validator (AI): Approved command sequence")
            except Exception as e:
                logger.warning(f"Safety validator AI model error: {e}, using heuristic result")
        
        return True

    def _validate_logic(self, actions):
        """
        Logic validator: Verifies command sequence makes sense.
        Uses AI model if available, otherwise falls back to heuristics.
        """
        # Heuristic checks (always runs)
        for step in actions:
            action = step.get("action", "")
            
            # Wait shouldn't be negative
            if action == "wait" and step.get("seconds", 0) < 0:
                logger.warning("Logic validator (heuristic): Negative wait time detected")
                return False
            
            # Click should have location
            if action == "click" and not step.get("location"):
                logger.warning("Logic validator (heuristic): Click action missing location")
                return False
            
            # Type should have text
            if action == "type" and not step.get("text"):
                logger.warning("Logic validator (heuristic): Type action missing text")
                return False
        
        # AI model check (if available)
        if "logic" in self.models and self.models["logic"] is not None:
            try:
                actions_json = str(actions)
                prompt = f"""Does this command sequence make logical sense? Answer only YES or NO.
                
Command sequence: {actions_json}

Answer:"""
                
                result = self.models["logic"](
                    prompt,
                    max_tokens=10,
                    stop=["\n"],
                    echo=False
                )
                
                response = result['choices'][0]['text'].strip().upper()
                if "NO" in response or "INVALID" in response or "ILLOGICAL" in response:
                    logger.warning(f"Logic validator (AI): Rejected illogical command sequence")
                    return False
                logger.debug(f"Logic validator (AI): Approved command sequence")
            except Exception as e:
                logger.warning(f"Logic validator AI model error: {e}, using heuristic result")
        
        return True

    def _validate_efficiency(self, actions):
        """
        Efficiency validator: Suggests optimizations and faster alternatives.
        This is a soft validator - it suggests but doesn't block.
        Uses AI model if available, otherwise falls back to heuristics.
        """
        # Heuristic checks for obvious inefficiencies
        wait_times = [step.get("seconds", 0) for step in actions if step.get("action") == "wait"]
        total_wait = sum(wait_times)
        
        if total_wait > 30:
            logger.info(f"Efficiency validator (heuristic): High total wait time ({total_wait}s) - consider optimization")
        
        if len(actions) > 20:
            logger.info(f"Efficiency validator (heuristic): Long action sequence ({len(actions)} steps) - consider breaking into smaller tasks")
        
        # AI model check (if available) - for suggestions only
        if "efficiency" in self.models and self.models["efficiency"] is not None:
            try:
                actions_json = str(actions)
                prompt = f"""Is this command sequence efficient? Suggest improvements if needed. Answer YES if efficient, or NO with a brief suggestion.
                
Command sequence: {actions_json}

Answer:"""
                
                result = self.models["efficiency"](
                    prompt,
                    max_tokens=50,
                    stop=["\n\n"],
                    echo=False
                )
                
                response = result['choices'][0]['text'].strip().upper()
                if "NO" in response or "INEFFICIENT" in response:
                    suggestion = result['choices'][0]['text'].strip()
                    logger.info(f"Efficiency validator (AI): Suggestion - {suggestion}")
                else:
                    logger.debug(f"Efficiency validator (AI): Sequence is efficient")
            except Exception as e:
                logger.debug(f"Efficiency validator AI model error: {e}, using heuristic result")
        
        # Efficiency validator always passes (soft validator)
        return True
