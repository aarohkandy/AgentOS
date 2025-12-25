"""
Tests for CommandGenerator
"""

import pytest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ai_engine.command_generator import CommandGenerator


class TestCommandGenerator:
    """Test suite for CommandGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Initialize generator without model (fallback mode)
        self.generator = CommandGenerator(None)

    def test_init_without_model(self):
        """Test initialization without a model."""
        gen = CommandGenerator(None)
        assert gen.model is None
        assert gen.system_prompt is not None
        assert len(gen.system_prompt) > 0

    def test_generate_fallback_response(self):
        """Test that generate returns fallback when no model."""
        result = self.generator.generate("open firefox")
        
        assert "plan" in result
        assert "description" in result
        assert "estimated_time" in result
        assert isinstance(result["plan"], list)

    def test_generate_echo_message(self):
        """Test that fallback includes the user message."""
        message = "navigate to google.com"
        result = self.generator.generate(message)
        
        assert message in result.get("description", "")

    def test_system_prompt_contains_actions(self):
        """Test that system prompt defines available actions."""
        prompt = self.generator.system_prompt
        
        assert "click" in prompt
        assert "type" in prompt
        assert "key" in prompt
        assert "wait" in prompt
        assert "drag" in prompt

    def test_system_prompt_has_json_example(self):
        """Test that system prompt includes JSON format example."""
        prompt = self.generator.system_prompt
        
        assert "JSON" in prompt
        assert "plan" in prompt
        assert "action" in prompt


class TestCommandGeneratorWithMockModel:
    """Test with a mock model for more realistic scenarios."""

    class MockModel:
        """Mock model that returns predefined responses."""
        
        def __init__(self, response: str):
            self.response = response

        def __call__(self, prompt, **kwargs):
            return {
                'choices': [{'text': self.response}]
            }

    def test_generate_with_mock_model(self):
        """Test generation with a mock model."""
        mock_response = json.dumps({
            "plan": [
                {"action": "click", "target": "firefox", "location": [100, 50]}
            ],
            "description": "Open Firefox",
            "estimated_time": 2
        })
        
        model = self.MockModel(mock_response)
        generator = CommandGenerator(model)
        result = generator.generate("open firefox")
        
        assert "plan" in result
        assert len(result["plan"]) == 1
        assert result["plan"][0]["action"] == "click"

    def test_generate_handles_json_markdown(self):
        """Test that generator strips markdown from JSON response."""
        mock_response = """```json
{
    "plan": [{"action": "wait", "seconds": 1}],
    "description": "Wait",
    "estimated_time": 1
}
```"""
        
        model = self.MockModel(mock_response)
        generator = CommandGenerator(model)
        result = generator.generate("wait a second")
        
        assert "plan" in result
        assert result["plan"][0]["action"] == "wait"

    def test_generate_handles_invalid_json(self):
        """Test that generator handles invalid JSON gracefully."""
        mock_response = "This is not valid JSON at all"
        
        model = self.MockModel(mock_response)
        generator = CommandGenerator(model)
        result = generator.generate("do something")
        
        assert "error" in result

    def test_generate_complex_plan(self):
        """Test generation of complex multi-step plan."""
        mock_response = json.dumps({
            "plan": [
                {"action": "click", "target": "firefox", "location": [100, 50]},
                {"action": "wait", "seconds": 2},
                {"action": "type", "text": "google.com"},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 3}
            ],
            "description": "Open Firefox and navigate to Google",
            "estimated_time": 7
        })
        
        model = self.MockModel(mock_response)
        generator = CommandGenerator(model)
        result = generator.generate("open firefox and go to google")
        
        assert len(result["plan"]) == 5
        assert result["estimated_time"] == 7


class TestCommandGeneratorActions:
    """Test specific action types in generated plans."""

    def test_click_action_format(self):
        """Test click action has required fields."""
        action = {"action": "click", "target": "button", "location": [100, 200]}
        
        assert action["action"] == "click"
        assert "location" in action
        assert len(action["location"]) == 2

    def test_type_action_format(self):
        """Test type action has required fields."""
        action = {"action": "type", "text": "hello world"}
        
        assert action["action"] == "type"
        assert "text" in action
        assert isinstance(action["text"], str)

    def test_key_action_format(self):
        """Test key action has required fields."""
        action = {"action": "key", "key": "Return"}
        
        assert action["action"] == "key"
        assert "key" in action

    def test_wait_action_format(self):
        """Test wait action has required fields."""
        action = {"action": "wait", "seconds": 2.5}
        
        assert action["action"] == "wait"
        assert "seconds" in action
        assert isinstance(action["seconds"], (int, float))

    def test_drag_action_format(self):
        """Test drag action has required fields."""
        action = {"action": "drag", "start": [100, 100], "end": [200, 200]}
        
        assert action["action"] == "drag"
        assert "start" in action
        assert "end" in action
        assert len(action["start"]) == 2
        assert len(action["end"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
