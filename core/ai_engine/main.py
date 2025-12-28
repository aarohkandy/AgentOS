import sys
import time
import logging
from pathlib import Path

# Add project root to sys.path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from core.ai_engine.config import Config
from core.ai_engine.model_manager import ModelManager
from core.ai_engine.command_generator import CommandGenerator
from core.ai_engine.command_validator import CommandValidator
from core.ai_engine.executor import Executor
from core.ai_engine.ipc_server import IPCServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("cosmic-ai.log")
    ]
)
logger = logging.getLogger("CosmicAI")

class CosmicAI:
    def __init__(self):
        logger.info("Initializing Cosmic AI...")
        self.config = Config()
        
        self.model_manager = ModelManager(self.config)
        self.model_manager.load_models()
        self.model_manager.load_validators()
        
        self.command_gen = CommandGenerator(self.model_manager.main_model)
        self.validators = CommandValidator(self.model_manager.validator_models)
        self.executor = Executor()
        self.ipc = IPCServer(self)
        
        # Log initialization summary
        logger.info("=" * 60)
        logger.info("Cosmic AI Initialization Complete")
        logger.info("=" * 60)
        logger.info(f"Main Model: {'Loaded' if self.model_manager.main_model else 'Not loaded (using fallback)'}")
        validator_count = sum(1 for v in self.model_manager.validator_models.values() if v is not None)
        logger.info(f"Validators: {validator_count}/3 with AI models, {3-validator_count}/3 using heuristics")
        logger.info("=" * 60)
        
    def start(self):
        logger.info("Starting IPC Server...")
        self.ipc.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info("Stopping Cosmic AI...")
        self.ipc.stop()
        sys.exit(0)
    
    def process_request(self, user_message):
        logger.info(f"Processing request: {user_message}")
        
        # 1. Generate command plan
        plan = self.command_gen.generate(user_message)
        if "error" in plan:
            return plan
            
        # 2. Validate
        if not self.validators.approve_all(plan):
            return {"success": False, "error": "Plan rejected by validators", "plan": plan}
        
        # 3. Execute (if we were running automatically, but typically we wait for GUI approval)
        # For this architecture, we might return the plan to the GUI for approval first.
        # But per Instructions.txt architecture: "Process requests: user message -> command plan -> validation -> execution"
        # It seems this main loop does it all.
        # However, the GUI Sidebar requirements say "Shows command plan before execution with approve/deny buttons"
        # So likely we should just RETURN the plan here, and let the GUI call a separate "execute_plan" method?
        # Re-reading Instructions.txt: "Approving plan executes actual GUI clicks"
        # So "process_request" should probably be "generate_plan", and we need an "execute_plan" method.
        # Or "process_request" returns the plan, and the GUI later calls another endpoint.
        
        # For now, adhering to the architecture snippet in Instructions.txt which says:
        # result = self.executor.execute(plan)
        # But this contradicts "Shows command plan before execution". 
        # I will implement it such that it returns the plan, and we'll add an execute method.
        
        return plan

    def execute_plan_request(self, plan):
        """
        Separate endpoint for when user approves the plan.
        """
        logger.info("User approved plan. Executing...")
        return self.executor.execute(plan)

if __name__ == "__main__":
    app = CosmicAI()
    app.start()
