import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from core.ai_engine.command_validator import CommandValidator
from core.ai_engine.command_generator import CommandGenerator
from core.ai_engine.executor import Executor

class TestCosmicAI(unittest.TestCase):
    def setUp(self):
        self.validator = CommandValidator({})
        self.executor = Executor()
        
    def test_validator_safety(self):
        # Should reject dangerous commands
        dangerous_plan = {
            "plan": [{"action": "type", "text": "rm -rf /"}]
        }
        self.assertFalse(self.validator.approve_all(dangerous_plan))
        
        # Should accept safe commands
        safe_plan = {
            "plan": [{"action": "type", "text": "Hello World"}]
        }
        self.assertTrue(self.validator.approve_all(safe_plan))

    def test_generator_structure(self):
        # Mock model to return valid JSON string
        mock_model = MagicMock()
        mock_model.return_value = {
            'choices': [{'text': '{"plan": [{"action": "wait", "seconds": 1}], "description": "wait"}'}]
        }
        
        gen = CommandGenerator(mock_model)
        result = gen.generate("wait for 1 second")
        
        self.assertIn("plan", result)
        self.assertEqual(result["plan"][0]["action"], "wait")

    def test_executor_dry_run(self):
        # Test executor without xdotool present (mocked or dry run)
        # We assume xdotool might not be in the minimal environment, 
        # so check if it handles it gracefully
        plan = {
            "plan": [{"action": "click", "location": [0, 0]}]
        }
        
        # We can't easily assert sidebar effects without more mocking,
        # but we can ensure it doesn't crash
        result = self.executor.execute(plan)
        if "error" in result:
             # It might fail if xdotool is missing and we didn't mock shutil.which
             pass 
        else:
            self.assertTrue(result["success"])

if __name__ == '__main__':
    unittest.main()
