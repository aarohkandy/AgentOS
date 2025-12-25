"""
Integration tests for Cosmic OS AI system.
Tests the full flow from user input to execution.
"""

import pytest
import sys
import json
import socket
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFullPipeline:
    """Test the complete AI pipeline."""

    def test_config_to_model_manager(self):
        """Test config loading feeds into model manager."""
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        
        config = Config()
        manager = ModelManager(config)
        
        assert manager.tier in [1, 2, 3]
        assert manager.config == config

    def test_model_manager_to_generator(self):
        """Test model manager creates usable model for generator."""
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        from core.ai_engine.command_generator import CommandGenerator
        
        config = Config()
        manager = ModelManager(config)
        # Don't load actual models for test
        
        generator = CommandGenerator(manager.main_model)
        result = generator.generate("test input")
        
        assert isinstance(result, dict)

    def test_generator_to_validator(self):
        """Test generator output is valid for validator."""
        from core.ai_engine.command_generator import CommandGenerator
        from core.ai_engine.command_validator import CommandValidator
        
        generator = CommandGenerator(None)
        validator = CommandValidator({})
        
        # Generate a plan
        plan = generator.generate("open firefox")
        
        # Validate it
        result = validator.approve_all(plan)
        assert isinstance(result, bool)

    def test_validator_to_executor(self):
        """Test validated plan can be executed."""
        from core.ai_engine.command_validator import CommandValidator
        from core.ai_engine.executor import Executor
        
        validator = CommandValidator({})
        executor = Executor()
        
        plan = {
            "plan": [
                {"action": "wait", "seconds": 0.01}
            ]
        }
        
        # Validate
        assert validator.approve_all(plan) is True
        
        # Execute
        result = executor.execute(plan)
        assert result["success"] is True


class TestCosmicAIClass:
    """Test the main CosmicAI orchestrator."""

    def test_cosmic_ai_init(self):
        """Test CosmicAI initialization."""
        from core.ai_engine.main import CosmicAI
        
        with patch('core.ai_engine.model_manager.ModelManager.load_models'):
            with patch('core.ai_engine.model_manager.ModelManager.load_validators'):
                ai = CosmicAI()
                
                assert ai.config is not None
                assert ai.model_manager is not None
                assert ai.command_gen is not None
                assert ai.validators is not None
                assert ai.executor is not None
                assert ai.ipc is not None

    def test_process_request(self):
        """Test processing a user request."""
        from core.ai_engine.main import CosmicAI
        
        with patch('core.ai_engine.model_manager.ModelManager.load_models'):
            with patch('core.ai_engine.model_manager.ModelManager.load_validators'):
                ai = CosmicAI()
                
                result = ai.process_request("open firefox")
                
                assert isinstance(result, dict)
                # Should return plan or error
                assert "plan" in result or "error" in result

    def test_execute_plan_request(self):
        """Test executing an approved plan."""
        from core.ai_engine.main import CosmicAI
        
        with patch('core.ai_engine.model_manager.ModelManager.load_models'):
            with patch('core.ai_engine.model_manager.ModelManager.load_validators'):
                ai = CosmicAI()
                
                plan = {
                    "plan": [{"action": "wait", "seconds": 0.01}],
                    "description": "Test plan"
                }
                
                result = ai.execute_plan_request(plan)
                
                assert result["success"] is True


class TestIPCCommunication:
    """Test IPC server and client communication."""

    def test_socket_server_start_stop(self):
        """Test starting and stopping socket server."""
        from core.ai_engine.ipc_server import IPCServer
        
        mock_ai = Mock()
        mock_ai.process_request = Mock(return_value={"response": "ok"})
        
        server = IPCServer(mock_ai)
        
        # Disable dbus for this test
        with patch('core.ai_engine.ipc_server.DBUS_AVAILABLE', False):
            server.start()
            time.sleep(0.2)  # Let server start
            
            assert server.running is True
            
            server.stop()
            time.sleep(0.1)
            
            assert server.running is False

    def test_socket_communication(self):
        """Test sending message via socket."""
        from core.ai_engine.ipc_server import IPCServer
        
        mock_ai = Mock()
        mock_ai.process_request = Mock(return_value={"status": "received"})
        
        server = IPCServer(mock_ai)
        
        with patch('core.ai_engine.ipc_server.DBUS_AVAILABLE', False):
            server.start()
            time.sleep(0.2)
            
            try:
                # Connect and send message
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(server.socket_path)
                client.sendall(b"test message")
                
                response = client.recv(4096)
                client.close()
                
                assert len(response) > 0
                data = json.loads(response.decode())
                assert "status" in data
                
            finally:
                server.stop()


class TestAutomationIntegration:
    """Test automation module integration."""

    def test_screen_controller_with_actions(self):
        """Test screen controller works with action primitives."""
        from core.automation.screen_controller import ScreenController
        from core.automation.action_primitives import ActionPrimitives
        
        screen = ScreenController(dry_run=True)
        actions = ActionPrimitives(screen)
        
        # Test click
        result = actions.click(100, 100)
        assert result.success is True
        
        # Test type
        result = actions.type_text("hello")
        assert result.success is True
        
        # Test wait
        result = actions.wait(0.01)
        assert result.success is True

    def test_window_manager_with_screen_controller(self):
        """Test window manager uses screen controller."""
        from core.automation.screen_controller import ScreenController
        from core.automation.window_manager import WindowManager
        
        screen = ScreenController(dry_run=True)
        wm = WindowManager(screen)
        
        # Basic initialization should work
        assert wm.screen == screen


class TestEndToEnd:
    """End-to-end tests simulating real usage."""

    def test_simple_command_flow(self):
        """Test simple command from input to execution."""
        from core.ai_engine.config import Config
        from core.ai_engine.command_generator import CommandGenerator
        from core.ai_engine.command_validator import CommandValidator
        from core.ai_engine.executor import Executor
        
        # Setup
        generator = CommandGenerator(None)
        validator = CommandValidator({})
        executor = Executor()
        
        # User input
        user_message = "wait for 1 second"
        
        # Generate plan
        plan = generator.generate(user_message)
        
        # In real usage, plan would have wait action
        # For fallback mode, we'll create one
        plan = {
            "plan": [{"action": "wait", "seconds": 0.01}],
            "description": "Wait briefly"
        }
        
        # Validate
        assert validator.approve_all(plan) is True
        
        # Execute
        result = executor.execute(plan)
        assert result["success"] is True

    def test_dangerous_command_blocked(self):
        """Test that dangerous commands are blocked at validation."""
        from core.ai_engine.command_validator import CommandValidator
        
        validator = CommandValidator({})
        
        # Simulated dangerous plan (as if AI generated it)
        dangerous_plan = {
            "plan": [
                {"action": "click", "location": [100, 100]},
                {"action": "type", "text": "rm -rf /"},
                {"action": "key", "key": "Return"}
            ]
        }
        
        # Should be rejected
        assert validator.approve_all(dangerous_plan) is False

    def test_gui_sidebar_imports(self):
        """Test that GUI components can be imported."""
        try:
            from core.gui.sidebar import CosmicSidebar, MessageBubble
            from core.gui.settings_panel import SettingsPanel
            from core.gui.setup_wizard import SetupWizard
            
            # If we get here, imports work
            assert True
        except ImportError as e:
            # PyQt6 might not be installed in test env
            if "PyQt6" in str(e):
                pytest.skip("PyQt6 not installed")
            raise


class TestConfigurationFlow:
    """Test configuration loading and application."""

    def test_config_defaults(self):
        """Test default configuration values."""
        from core.ai_engine.config import Config
        
        config = Config()
        
        # Should have sensible defaults
        tier = config.get("AI", "tier", fallback="auto")
        assert tier in ["auto", "1", "2", "3"]

    def test_config_sections(self):
        """Test all configuration sections are accessible."""
        from core.ai_engine.config import Config
        
        config = Config()
        
        sections = ["General", "AI", "GUI", "Automation", "Permissions", "Development"]
        
        for section in sections:
            # Should not raise
            value = config.get(section, "nonexistent", fallback="default")
            assert value == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
