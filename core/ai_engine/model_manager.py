import psutil
import platform
import logging
from pathlib import Path
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None 

from core.ai_engine.config import Config

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, config: Config):
        self.config = config
        self.tier = self._detect_tier()
        self.main_model = None
        self.validator_models = {}
        
    def _detect_tier(self):
        """
        Detect hardware tier based on RAM and GPU.
        Tier 1: <8GB RAM, no GPU
        Tier 2: 8-16GB RAM
        Tier 3: >16GB RAM or GPU
        """
        cfg_tier = self.config.get("AI", "tier", fallback="auto")
        if cfg_tier in ["1", "2", "3"]:
            return int(cfg_tier)
            
        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        has_gpu = False
        
        # Simple GPU check (can be expanded)
        try:
            # Check for nvidia-smi
            import subprocess
            subprocess.check_call(["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            has_gpu = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
            
        if total_ram_gb > 16 or has_gpu:
            return 3
        elif total_ram_gb >= 8:
            return 2
        else:
            return 1

    def load_models(self):
        if Llama is None:
            logger.error("llama-cpp-python not installed. Cannot load models.")
            return

        model_path = self.config.get("AI", "main_model_path")
        # Logic to adjust path based on tier if auto-selected
        # For now, we use the config path or fallback to a tier-based path construction
        
        if not Path(model_path).exists():
            logger.warning(f"Model not found at {model_path}. Please run install-models.sh")
            return

        logger.info(f"Loading main model from {model_path} for Tier {self.tier}")
        
        n_gpu_layers = -1 if self.tier == 3 else 0 # Offload all to GPU if Tier 3
        
        try:
            self.main_model = Llama(
                model_path=model_path,
                n_gpu_layers=n_gpu_layers,
                n_ctx=2048, # Context window
                verbose=False
            )
            logger.info("Main model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load main model: {e}")

    def load_validators(self):
        # Placeholder for loading 3 tiny validator models
        pass
