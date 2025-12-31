import sys
import time
import logging
import signal
from pathlib import Path

# Add project root to sys.path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from core.ai_engine.config import Config, DEFAULT_LOG_FILE
from core.ai_engine.command_generator import CommandGenerator
from core.ai_engine.command_validator import CommandValidator
from core.ai_engine.executor import Executor
from core.ai_engine.ipc_server import IPCServer

# Import API client and conversation context
try:
    from core.ai_engine.api_client import UnifiedAPIClient, get_api_client
except (ImportError, Exception) as e:
    # Import failed - log after logger is set up
    import sys
    print(f"ERROR: Failed to import API client: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    UnifiedAPIClient = None
    get_api_client = None

try:
    from core.ai_engine.conversation_context import ConversationContext, get_conversation_context
except (ImportError, Exception) as e:
    import sys
    print(f"ERROR: Failed to import conversation context: {e}", file=sys.stderr)
    ConversationContext = None
    get_conversation_context = None

# Configure logging with absolute path
log_file = Path(DEFAULT_LOG_FILE)
if not log_file.is_absolute():
    log_file = project_root / DEFAULT_LOG_FILE

# Configure logging - reduce verbosity (suppress QPainter and other Qt noise)
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
    format='%(levelname)s - %(message)s',  # Shorter format
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file))
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger("CosmicAI").setLevel(logging.INFO)  # Main logger at INFO
logging.getLogger("core.ai_engine").setLevel(logging.WARNING)  # AI engine at WARNING
logging.getLogger("core.automation").setLevel(logging.ERROR)  # Automation at ERROR only
logging.getLogger("core.gui").setLevel(logging.ERROR)  # GUI at ERROR only

# Suppress Qt/PyQt6 noise
logging.getLogger("PyQt6").setLevel(logging.CRITICAL)
logging.getLogger("qt").setLevel(logging.CRITICAL)
logging.getLogger("PyQt6.QtCore").setLevel(logging.CRITICAL)
logging.getLogger("PyQt6.QtGui").setLevel(logging.CRITICAL)
logging.getLogger("PyQt6.QtWidgets").setLevel(logging.CRITICAL)

# Suppress QPainter warnings (they're harmless)
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*QPainter.*")

logger = logging.getLogger("CosmicAI")

class CosmicAI:
    def __init__(self):
        logger.info("Initializing Cosmic AI...")
        # Set up signal handlers to prevent crashes
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        try:
            signal.signal(signal.SIGSEGV, self._signal_handler)  # Segmentation fault
        except (ValueError, AttributeError):
            pass  # Not available on all systems
        try:
            signal.signal(signal.SIGABRT, self._signal_handler)  # Abort
        except (ValueError, AttributeError):
            pass  # Not available on all systems
        
        try:
            self.config = Config()
            
            # Check if we should use online API
            use_online_api = self.config.get("AI", "use_online_api", fallback="true").lower() == "true"
            logger.info(f"Online API mode: {use_online_api}")
            
            # Initialize API client if online mode is enabled
            self.api_client = None
            self.conversation_context = None
            
            if use_online_api:
                # Get API configuration
                groq_model = self.config.get("API", "groq_model", fallback="llama-3.1-70b-versatile")
                groq_fallback = self.config.get("API", "groq_fallback_model", fallback="mixtral-8x7b-32768")
                openrouter_model = self.config.get("API", "openrouter_model", fallback="deepseek/deepseek-chat")
                openrouter_fallback = self.config.get("API", "openrouter_fallback_model", fallback="google/gemini-flash-1.5")
                max_context = int(self.config.get("API", "max_context_messages", fallback="50"))
                enable_web_search = self.config.get("API", "enable_web_search", fallback="true").lower() == "true"
                timeout = int(self.config.get("API", "timeout", fallback="30"))
                temperature = float(self.config.get("AI", "temperature", fallback="0.7"))
                max_tokens = int(self.config.get("AI", "max_tokens", fallback="512"))
                
                # Initialize API client
                if get_api_client:
                    try:
                        self.api_client = get_api_client(
                            groq_model=groq_model,
                            groq_fallback_model=groq_fallback,
                            openrouter_model=openrouter_model,
                            openrouter_fallback_model=openrouter_fallback,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout=timeout
                        )
                        logger.info("API client initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize API client: {e}")
                        self.api_client = None
                else:
                    logger.error("API client module import failed - check .env file exists")
                    self.api_client = None
                
                # Initialize conversation context
                if get_conversation_context:
                    try:
                        self.conversation_context = get_conversation_context(
                            max_messages=max_context,
                            enable_web_search=enable_web_search
                        )
                        logger.debug("Conversation context initialized")
                    except Exception as e:
                        logger.warning(f"Failed to initialize conversation context: {e}")
                        self.conversation_context = None
            
            # Initialize command generator with API client and context (online API only)
            # No local models - we only use Groq/OpenRouter API
            self.command_gen = CommandGenerator(
                model=None,  # No local models
                api_client=self.api_client,
                context=self.conversation_context,
                use_online_api=True  # Always use online API
            )
            
            # Validators use heuristics only (no local AI models)
            self.validators = CommandValidator({})
            self.executor = Executor()
            self.ipc = IPCServer(self)
            
            # Preload common queries for instant responses (iOS-quality)
            self._preload_common_queries()
            
            # Log initialization summary
            # Log initialization summary (concise)
            if use_online_api and self.api_client:
                api_status = self.api_client.get_status()
                logger.info(f"Ready - Groq API: {api_status['groq_keys_available']} keys, Model: {api_status['groq_model']}")
            elif use_online_api:
                logger.error("API client not available - check .env file and API keys")
            else:
                logger.warning("Online API disabled in config")
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            # Set up minimal fallback components
            self.config = Config()
            self.api_client = None
            self.conversation_context = None
            self.command_gen = None
            self.validators = CommandValidator({})
            self.executor = Executor()
            self.ipc = IPCServer(self)
        
    def start(self):
        logger.info("Starting...")
        try:
            self.ipc.start()
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}")
            sys.exit(1)
        
        # Main loop with comprehensive error recovery
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while True:
                try:
                    time.sleep(1)
                    consecutive_errors = 0  # Reset on successful iteration
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal...")
                    self.stop()
                    break
                except Exception as e:
                    consecutive_errors += 1
                    logger.critical(f"Unexpected error in main loop (error #{consecutive_errors}): {e}", exc_info=True)
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many consecutive errors ({consecutive_errors}). Attempting recovery...")
                        consecutive_errors = 0  # Reset counter after recovery attempt
                    
                    logger.info("Attempting to recover...")
                    time.sleep(5)
                    # Try to restart IPC with comprehensive error handling
                    try:
                        if hasattr(self, 'ipc') and self.ipc:
                            self.ipc.stop()
                            time.sleep(1)
                            self.ipc.start()
                            logger.info("IPC server recovered successfully")
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {recovery_error}", exc_info=True)
                        logger.info("Continuing with degraded functionality...")
                        # Don't exit - keep trying to serve requests even if IPC is broken
                        time.sleep(10)  # Wait longer before retrying
        except SystemExit:
            # Allow system exit to propagate
            raise
        except BaseException as e:
            # Catch even base exceptions (like SystemExit, KeyboardInterrupt) but handle gracefully
            logger.critical(f"Fatal error in main loop: {e}", exc_info=True)
            try:
                self.stop()
            except:
                pass
            sys.exit(1)

    def _signal_handler(self, signum, frame):
        """Handle signals gracefully - never crash."""
        logger.warning(f"Received signal {signum}. Shutting down gracefully...")
        try:
            self.stop()
        except:
            pass
        sys.exit(0)
    
    def stop(self):
        logger.info("Stopping Cosmic AI...")
        try:
            self.ipc.stop()
        except Exception as e:
            logger.error(f"Error stopping IPC: {e}", exc_info=True)
        sys.exit(0)
    
    def process_request(self, user_message):
        """Process user request with comprehensive error handling - never crashes."""
        try:
            logger.debug(f"Processing: {user_message[:50]}...")
            
            # 1. Generate command plan
            try:
                if self.command_gen is None:
                    return {"error": "Command generator not available. System may be in fallback mode."}
                plan = self.command_gen.generate(user_message)
                if "error" in plan:
                    return plan
            except Exception as e:
                logger.error(f"Error generating plan: {e}")
                return {"error": f"Failed to generate plan: {str(e)}"}
                
            # 2. Validate
            try:
                if self.validators and not self.validators.approve_all(plan):
                    return {"success": False, "error": "Plan rejected by validators", "plan": plan}
            except Exception as e:
                logger.warning(f"Validation error: {e}")
            
            # Return plan for GUI approval (execution happens via execute_plan_request)
            return plan
            
        except Exception as e:
            logger.error(f"Error in process_request: {e}")
            return {"error": f"System error: {str(e)}. Please try again."}

    def _preload_common_queries(self):
        """Preload common queries for instant responses - iOS-quality optimization."""
        if not self.command_gen or not self.command_gen.cache:
            return
        
        common_queries = ["hello", "hi", "what time is it", "system info", "help", "what can you do"]
        
        for query in common_queries:
            try:
                self.command_gen.generate(query)
            except Exception:
                pass  # Silent fail for preloading
    
    def execute_plan_request(self, plan):
        """Execute approved plan."""
        try:
            logger.debug("Executing plan...")
            
            if not plan or not isinstance(plan, dict):
                return {"success": False, "error": "Invalid plan"}
            
            if self.executor is None:
                return {"success": False, "error": "Executor not available"}
            
            try:
                result = self.executor.execute(plan)
                return result if result else {"success": False, "error": "Execution returned no result"}
            except Exception as e:
                logger.error(f"Execution error: {e}")
                return {"success": False, "error": f"Execution failed: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error in execute_plan_request: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def clear_conversation(self):
        """Clear the conversation context."""
        if self.command_gen:
            self.command_gen.clear_context()
            return {"success": True, "message": "Conversation context cleared"}
        return {"success": False, "error": "Command generator not available"}
    
    def get_status(self):
        """Get the current status of the AI system."""
        status = {
            "online_api": self.api_client is not None,
            "local_model": False,  # No local models - online API only
            "conversation_context": self.conversation_context is not None,
        }
        
        if self.api_client:
            status["api_status"] = self.api_client.get_status()
        
        if self.conversation_context:
            status["context_summary"] = self.conversation_context.get_summary()
        
        return status

if __name__ == "__main__":
    try:
        app = CosmicAI()
        app.start()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        logger.error("System cannot continue. Exiting...")
        sys.exit(1)
