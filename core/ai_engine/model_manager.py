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
            logger.warning("llama-cpp-python not installed. AI will use rule-based fallback.")
            logger.info("Install with: pip3 install llama-cpp-python")
            return

        # Get model path from config or auto-detect based on tier
        config_path = self.config.get("AI", "main_model_path", fallback=None)
        
        # Try multiple path resolutions
        possible_paths = []
        
        if config_path:
            # Try as-is (absolute or relative to current dir)
            possible_paths.append(Path(config_path))
            # Try relative to project root
            project_root = Path(__file__).parent.parent.parent
            possible_paths.append(project_root / config_path)
        
        # Auto-detect based on tier
        project_root = Path(__file__).parent.parent.parent
        
        # Check base folder first (persists across installs)
        base_model_paths = [
            project_root / "models" / f"tier{self.tier}" / "model.gguf",  # Base folder
            Path.home() / "cosmic-os-models" / f"tier{self.tier}" / "model.gguf",  # User home base
            Path("/opt/cosmic-os/models") / f"tier{self.tier}" / "model.gguf",  # System base
        ]
        possible_paths = base_model_paths + possible_paths
        
        # Then check local project folder
        tier_paths = [
            project_root / "core" / "ai_engine" / "models" / f"tier{self.tier}" / "model.gguf",
            project_root / "core" / "ai_engine" / "models" / f"tier{self.tier}" / "*.gguf",
        ]
        possible_paths.extend(tier_paths)
        
        # Find first existing model
        model_path = None
        for path in possible_paths:
            if path.exists() and path.suffix == ".gguf":
                model_path = path
                break
            # Try glob for wildcard
            if "*" in str(path):
                import glob
                matches = glob.glob(str(path))
                if matches:
                    model_path = Path(matches[0])
                    break
        
        if not model_path or not model_path.exists():
            logger.warning(f"Model not found. Searched: {[str(p) for p in possible_paths[:3]]}")
            logger.info(f"To download models, run: ./scripts/install-models.sh --tier {self.tier}")
            return

        logger.info(f"Loading main model from {model_path} for Tier {self.tier}")
        
        n_gpu_layers = -1 if self.tier == 3 else 0 # Offload all to GPU if Tier 3
        
        try:
            self.main_model = Llama(
                model_path=str(model_path),
                n_gpu_layers=n_gpu_layers,
                n_ctx=2048, # Context window
                verbose=False
            )
            logger.info("✅ Main model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load main model: {e}")
            logger.info("AI will use rule-based fallback.")

    def load_validators(self):
        """
        Load the 3 validator models: safety, logic, and efficiency.
        If models aren't available, validators will use heuristics as fallback.
        """
        validator_names = ["safety", "logic", "efficiency"]
        project_root = Path(__file__).parent.parent.parent
        
        # Check base folder first (persists across installs)
        base_validator_paths = [
            project_root / "models" / "validators",  # Base folder
            Path.home() / "cosmic-os-models" / "validators",  # User home base
            Path("/opt/cosmic-os/models") / "validators",  # System base
            project_root / "core" / "ai_engine" / "models" / "validators",  # Local fallback
        ]
        
        logger.info("Loading validator models...")
        
        for name in validator_names:
            model_path = None
            # Try each possible location
            for base_path in base_validator_paths:
                candidate = base_path / f"{name}.gguf"
                if candidate.exists():
                    model_path = candidate
                    break
            
            if Llama is None:
                logger.warning(f"llama-cpp-python not installed. {name.capitalize()} validator will use heuristics only.")
                self.validator_models[name] = None
                continue
            
            if model_path is None or not model_path.exists():
                logger.warning(f"{name.capitalize()} validator model not found")
                logger.info(f"  {name.capitalize()} validator will use heuristics (safe fallback)")
                self.validator_models[name] = None
                continue
            
            try:
                logger.info(f"Loading {name} validator from {model_path}")
                self.validator_models[name] = Llama(
                    model_path=str(model_path),
                    n_ctx=1024,  # Smaller context for validators
                    verbose=False
                )
                logger.info(f"✓ {name.capitalize()} validator loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load {name} validator: {e}")
                logger.info(f"  {name.capitalize()} validator will use heuristics (safe fallback)")
                self.validator_models[name] = None
        
        # Log summary
        loaded = sum(1 for v in self.validator_models.values() if v is not None)
        total = len(validator_names)
        if loaded == total:
            logger.info(f"✅ All {total} validators loaded with AI models")
        elif loaded > 0:
            logger.info(f"⚠️  {loaded}/{total} validators loaded with AI models, {total - loaded} using heuristics")
        else:
            logger.info(f"ℹ️  All {total} validators using heuristic fallback (models not available)")
