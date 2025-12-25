"""
Tests for Executor
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ai_engine.executor import Executor


class TestExecutor:
    """Test suite for Executor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.executor = Executor()

    def test_init(self):
        """Test executor initialization."""
        executor = Executor()
        # Should initialize without error
        assert executor is not None

    def test_execute_empty_plan(self):
        """Test executing plan with no actions."""
        plan = {"plan": []}
        result = self.executor.execute(plan)
        
        assert result["success"] is True
        assert "No actions" in result.get("message", "")

    def test_execute_error_plan(self):
        """Test executing plan with error."""
        plan = {"error": "Something went wrong"}
        result = self.executor.execute(plan)
        
        assert result["success"] is False
        assert "error" in result

    def test_execute_returns_result(self):
        """Test that execute returns a result dict."""
        plan = {"plan": [{"action": "wait", "seconds": 0.01}]}
        result = self.executor.execute(plan)
        
        assert isinstance(result, dict)
        assert "success" in result


class TestExecutorActions:
    """Test individual action execution."""

    def setup_method(self):
        self.executor = Executor()

    def test_wait_action(self):
        """Test wait action execution."""
        import time
        
        plan = {"plan": [{"action": "wait", "seconds": 0.1}]}
        
        start = time.time()
        result = self.executor.execute(plan)
        elapsed = time.time() - start
        
        assert result["success"] is True
        assert elapsed >= 0.1

    def test_unknown_action(self):
        """Test handling of unknown action type."""
        plan = {
            "plan": [{"action": "unknown_action", "param": "value"}]
        }
        
        # Unknown actions should be logged but not fail
        result = self.executor.execute(plan)
        assert result["success"] is True


class TestExecutorXdotool:
    """Test xdotool integration."""

    def setup_method(self):
        self.executor = Executor()

    @patch('subprocess.run')
    def test_click_calls_xdotool(self, mock_run):
        """Test that click action calls xdotool."""
        mock_run.return_value = Mock(returncode=0)
        
        if self.executor.xdotool_path:
            plan = {
                "plan": [{"action": "click", "location": [100, 200]}]
            }
            self.executor.execute(plan)
            
            # Check that subprocess.run was called
            assert mock_run.called

    @patch('subprocess.run')
    def test_type_calls_xdotool(self, mock_run):
        """Test that type action calls xdotool."""
        mock_run.return_value = Mock(returncode=0)
        
        if self.executor.xdotool_path:
            plan = {
                "plan": [{"action": "type", "text": "hello"}]
            }
            self.executor.execute(plan)
            
            assert mock_run.called

    @patch('subprocess.run')
    def test_key_calls_xdotool(self, mock_run):
        """Test that key action calls xdotool."""
        mock_run.return_value = Mock(returncode=0)
        
        if self.executor.xdotool_path:
            plan = {
                "plan": [{"action": "key", "key": "Return"}]
            }
            self.executor.execute(plan)
            
            assert mock_run.called

    def test_no_xdotool_dry_run(self):
        """Test dry run when xdotool not available."""
        # Temporarily remove xdotool path
        original_path = self.executor.xdotool_path
        self.executor.xdotool_path = None
        
        plan = {
            "plan": [
                {"action": "click", "location": [100, 200]},
                {"action": "type", "text": "test"}
            ]
        }
        
        # Should not raise, just log
        result = self.executor.execute(plan)
        assert result["success"] is True
        
        # Restore
        self.executor.xdotool_path = original_path


class TestExecutorDrag:
    """Test drag action."""

    def setup_method(self):
        self.executor = Executor()

    @patch('subprocess.run')
    def test_drag_action(self, mock_run):
        """Test drag action execution."""
        mock_run.return_value = Mock(returncode=0)
        
        if self.executor.xdotool_path:
            plan = {
                "plan": [{
                    "action": "drag",
                    "start": [100, 100],
                    "end": [200, 200]
                }]
            }
            result = self.executor.execute(plan)
            
            assert result["success"] is True


class TestExecutorErrorHandling:
    """Test error handling in executor."""

    def setup_method(self):
        self.executor = Executor()

    @patch('subprocess.run')
    def test_xdotool_failure(self, mock_run):
        """Test handling of xdotool failure."""
        mock_run.side_effect = Exception("xdotool crashed")
        
        if self.executor.xdotool_path:
            plan = {
                "plan": [{"action": "click", "location": [100, 200]}]
            }
            result = self.executor.execute(plan)
            
            assert result["success"] is False
            assert "error" in result

    def test_missing_location(self):
        """Test handling of click without location."""
        plan = {
            "plan": [{"action": "click"}]  # Missing location
        }
        # Should handle gracefully
        result = self.executor.execute(plan)
        # Might succeed or fail, but shouldn't crash
        assert isinstance(result, dict)

    def test_invalid_plan_format(self):
        """Test handling of invalid plan format."""
        plan = {"invalid": "format"}
        result = self.executor.execute(plan)
        
        # Should handle missing 'plan' key
        assert "success" in result


class TestExecutorSequence:
    """Test execution of action sequences."""

    def setup_method(self):
        self.executor = Executor()

    def test_sequential_execution(self):
        """Test that actions execute in order."""
        execution_order = []
        
        original_execute_step = self.executor._execute_step
        
        def tracking_execute(step):
            execution_order.append(step["action"])
            original_execute_step(step)
        
        self.executor._execute_step = tracking_execute
        
        plan = {
            "plan": [
                {"action": "wait", "seconds": 0.01},
                {"action": "wait", "seconds": 0.01},
                {"action": "wait", "seconds": 0.01}
            ]
        }
        
        self.executor.execute(plan)
        
        assert len(execution_order) == 3
        assert all(a == "wait" for a in execution_order)

    def test_stop_on_error(self):
        """Test that execution stops on first error."""
        execution_count = [0]
        
        def failing_execute(step):
            execution_count[0] += 1
            if execution_count[0] == 2:
                raise Exception("Simulated failure")
        
        self.executor._execute_step = failing_execute
        
        plan = {
            "plan": [
                {"action": "step1"},
                {"action": "step2"},  # This will fail
                {"action": "step3"}   # This shouldn't execute
            ]
        }
        
        result = self.executor.execute(plan)
        
        assert result["success"] is False
        assert execution_count[0] == 2  # Stopped after failure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
