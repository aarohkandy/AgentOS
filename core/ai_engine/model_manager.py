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
        Tier 1: <1GB RAM - Qwen 2.5 0.5B (EXTREME Easy)
        Tier 2: 2-4GB RAM - Llama 3.2 3B (Low)
        Tier 3: 16-32GB RAM or 8-12GB VRAM - Phi-4 14B (Medium)
        Tier 4: 64GB+ RAM or 40GB+ VRAM - DeepSeek-V3/Llama 3.1 70B (Very Powerful)
        """
        cfg_tier = self.config.get("AI", "tier", fallback="auto")
        if cfg_tier in ["1", "2", "3", "4"]:
            return int(cfg_tier)
            
        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        has_high_end_gpu = False
        gpu_vram_gb = 0
        
        # Check for NVIDIA GPU and VRAM
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                vram_mb = int(result.stdout.strip().split('\n')[0])
                gpu_vram_gb = vram_mb / 1024
                has_high_end_gpu = gpu_vram_gb >= 40
        except (FileNotFoundError, subprocess.CalledProcessError, ValueError, IndexError):
            pass
            
        # Tier detection logic
        if total_ram_gb >= 64 or has_high_end_gpu:
            return 4  # Very Powerful - DeepSeek-V3/Llama 3.1 70B
        elif total_ram_gb >= 16 or gpu_vram_gb >= 8:
            return 3  # Medium - Phi-4 14B
        elif total_ram_gb >= 2:
            return 2  # Low - Llama 3.2 3B
        else:
            return 1  # EXTREME Easy - Qwen 2.5 0.5B

    def load_models(self):
        # Try to import Llama if not already available
        llama_class = None
        try:
            from llama_cpp import Llama as LlamaClass
            llama_class = LlamaClass
        except ImportError:
            logger.warning("llama-cpp-python not installed. Attempting automatic installation...")
            if self._auto_install_llama_cpp():
                # Retry import after installation
                try:
                    from llama_cpp import Llama as LlamaClass
                    llama_class = LlamaClass
                    logger.info("✅ llama-cpp-python installed successfully!")
                except ImportError:
                    logger.error("Installation completed but import still fails. Please restart.")
                    return
            else:
                logger.error("Failed to auto-install llama-cpp-python. Please install manually: pip3 install llama-cpp-python")
                return
        
        if llama_class is None:
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
            logger.warning(f"Model not found for Tier {self.tier}")
            logger.info(f"Searched paths:")
            for p in possible_paths[:5]:
                exists = "✓" if Path(p).exists() else "✗"
                logger.info(f"  {exists} {p}")
            logger.info(f"To download models, run: ./scripts/install-models.sh --tier {self.tier}")
            return

        logger.info(f"Loading main model from {model_path} for Tier {self.tier}")
        logger.info(f"Model size: {model_path.stat().st_size / (1024**3):.2f} GB")
        
        # GPU layer configuration based on tier
        # Tier 4 and 3: Offload all to GPU if available
        # Tier 2 and 1: CPU only (smaller models)
        n_gpu_layers = -1 if self.tier >= 3 else 0
        
        # Context window based on tier (larger models support larger contexts)
        context_sizes = {
            1: 32768,  # Qwen 2.5 0.5B supports large context
            2: 8192,   # Llama 3.2 3B
            3: 8192,   # Phi-4 14B
            4: 128000  # DeepSeek-V3 supports very large context
        }
        n_ctx = context_sizes.get(self.tier, 2048)
        
        # Calculate optimal thread count for CPU inference
        # Use all available cores, but leave 1 free for system responsiveness
        cpu_count = psutil.cpu_count(logical=True)
        n_threads = max(1, cpu_count - 1) if cpu_count > 1 else cpu_count
        logger.info(f"Using {n_threads} threads for inference (CPU cores: {cpu_count})")
        
        try:
            self.main_model = llama_class(
                model_path=str(model_path),
                n_gpu_layers=n_gpu_layers,
                n_ctx=n_ctx,
                n_threads=n_threads,
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
        # Try to get Llama class
        try:
            from llama_cpp import Llama as LlamaClass
        except ImportError:
            LlamaClass = None
        
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
            
            if LlamaClass is None:
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
                # Use fewer threads for validators (they're smaller and faster)
                validator_threads = max(1, min(4, psutil.cpu_count(logical=True) // 2))
                self.validator_models[name] = LlamaClass(
                    model_path=str(model_path),
                    n_ctx=1024,  # Smaller context for validators
                    n_threads=validator_threads,
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

    def _auto_install_llama_cpp(self):
        """Automatically install llama-cpp-python."""
        import subprocess
        import sys
        
        logger.info("Installing llama-cpp-python (this may take 5-10 minutes)...")
        try:
            # Try user install first
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "llama-cpp-python"],
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode == 0:
                return True
            
            # Try with --break-system-packages for newer systems
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "llama-cpp-python"],
                capture_output=True,
                text=True,
                timeout=600
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Installation timed out")
            return False
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False
