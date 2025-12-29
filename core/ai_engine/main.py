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
        try:
            self.config = Config()
            
            self.model_manager = ModelManager(self.config)
            try:
                self.model_manager.load_models()
            except Exception as e:
                logger.error(f"Failed to load models: {e}", exc_info=True)
                logger.warning("Continuing with fallback mode...")
            
            try:
                self.model_manager.load_validators()
            except Exception as e:
                logger.error(f"Failed to load validators: {e}", exc_info=True)
                logger.warning("Validators will use heuristics only...")
            
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
        except Exception as e:
            logger.critical(f"Critical error during initialization: {e}", exc_info=True)
            logger.error("System will attempt to continue with minimal functionality...")
            # Set up minimal fallback components
            self.config = Config()
            self.model_manager = None
            self.command_gen = None
            self.validators = None
            self.executor = Executor()
            self.ipc = IPCServer(self)
        
    def start(self):
        logger.info("Starting IPC Server...")
        try:
            self.ipc.start()
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}", exc_info=True)
            logger.error("Cannot continue without IPC server. Exiting...")
            sys.exit(1)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal...")
            self.stop()
        except Exception as e:
            logger.critical(f"Unexpected error in main loop: {e}", exc_info=True)
            logger.info("Attempting to recover...")
            time.sleep(5)
            # Try to restart IPC
            try:
                self.ipc.stop()
                self.ipc.start()
            except:
                logger.error("Recovery failed. Exiting...")
                sys.exit(1)

    def stop(self):
        logger.info("Stopping Cosmic AI...")
        self.ipc.stop()
        sys.exit(0)
    
    def process_request(self, user_message):
        """Process user request with comprehensive error handling - never crashes."""
        try:
            logger.info(f"Processing request: {user_message}")
            
            # 1. Generate command plan
            try:
                if self.command_gen is None:
                    return {"error": "Command generator not available. System may be in fallback mode."}
                plan = self.command_gen.generate(user_message)
                if "error" in plan:
                    return plan
            except Exception as e:
                logger.error(f"Error generating plan: {e}", exc_info=True)
                return {"error": f"Failed to generate plan: {str(e)}"}
                
            # 2. Validate
            try:
                if self.validators is None:
                    logger.warning("Validators not available, skipping validation")
                elif not self.validators.approve_all(plan):
                    return {"success": False, "error": "Plan rejected by validators", "plan": plan}
            except Exception as e:
                logger.error(f"Error during validation: {e}", exc_info=True)
                logger.warning("Validation failed, but continuing with plan...")
            
            # Return plan for GUI approval (execution happens via execute_plan_request)
            return plan
            
        except Exception as e:
            logger.critical(f"Critical error in process_request: {e}", exc_info=True)
            return {"error": f"System error: {str(e)}. Please try again."}

    def execute_plan_request(self, plan):
        """
        Separate endpoint for when user approves the plan.
        Never crashes - always returns a result with comprehensive error handling.
        """
        try:
            logger.info("User approved plan. Executing...")
            
            # Validate plan
            if not plan or not isinstance(plan, dict):
                return {"success": False, "error": "Invalid plan: must be a dictionary"}
            
            if self.executor is None:
                return {"success": False, "error": "Executor not available"}
            
            # Execute with timeout protection
            try:
                result = self.executor.execute(plan)
                if result is None:
                    return {"success": False, "error": "Execution returned no result"}
                return result
            except KeyboardInterrupt:
                logger.warning("Execution interrupted by user")
                return {"success": False, "error": "Execution interrupted"}
            except Exception as e:
                logger.error(f"Error during execution: {e}", exc_info=True)
                return {"success": False, "error": f"Execution failed: {str(e)}"}
                
        except Exception as e:
            logger.critical(f"Unexpected error in execute_plan_request: {e}", exc_info=True)
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    try:
        app = CosmicAI()
        app.start()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        logger.error("System cannot continue. Exiting...")
        sys.exit(1)
