#!/usr/bin/env python3
"""
Cosmic OS - AI Functionality Test Script
Quick tests to verify AI system is working correctly.
"""

import sys
import json
import socket
import argparse
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ANSI colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_pass(msg: str):
    print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {msg}")


def log_fail(msg: str):
    print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {msg}")


def log_warn(msg: str):
    print(f"{Colors.YELLOW}⚠ WARN:{Colors.RESET} {msg}")


def log_info(msg: str):
    print(f"{Colors.CYAN}ℹ INFO:{Colors.RESET} {msg}")


def test_imports():
    """Test that all modules can be imported."""
    print(f"\n{Colors.BOLD}Testing imports...{Colors.RESET}")
    
    modules = [
        'core.ai_engine.config',
        'core.ai_engine.model_manager',
        'core.ai_engine.command_generator',
        'core.ai_engine.command_validator',
        'core.ai_engine.executor',
        'core.ai_engine.ipc_server',
    ]
    
    all_passed = True
    for module in modules:
        try:
            __import__(module)
            log_pass(f"Imported {module}")
        except ImportError as e:
            log_fail(f"Failed to import {module}: {e}")
            all_passed = False
    
    return all_passed


def test_config():
    """Test configuration loading."""
    print(f"\n{Colors.BOLD}Testing configuration...{Colors.RESET}")
    
    try:
        from core.ai_engine.config import Config
        config = Config()
        
        # Test getting values
        tier = config.get("AI", "tier", fallback="auto")
        log_pass(f"Config loaded, AI tier: {tier}")
        
        hotkey = config.get("GUI", "hotkey", fallback="Meta+Shift")
        log_pass(f"GUI hotkey: {hotkey}")
        
        return True
    except Exception as e:
        log_fail(f"Config error: {e}")
        return False


def test_hardware_detection():
    """Test hardware tier detection."""
    print(f"\n{Colors.BOLD}Testing hardware detection...{Colors.RESET}")
    
    try:
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        
        config = Config()
        manager = ModelManager(config)
        
        tier = manager.tier
        log_pass(f"Detected hardware tier: {tier}")
        
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        log_info(f"System RAM: {ram_gb:.1f} GB")
        
        return True
    except Exception as e:
        log_fail(f"Hardware detection error: {e}")
        return False


def test_xdotool():
    """Test xdotool availability."""
    print(f"\n{Colors.BOLD}Testing xdotool...{Colors.RESET}")
    
    import shutil
    import subprocess
    
    xdotool_path = shutil.which("xdotool")
    if not xdotool_path:
        log_fail("xdotool not found. Install with: sudo apt install xdotool")
        return False
    
    log_pass(f"xdotool found at: {xdotool_path}")
    
    try:
        result = subprocess.run(
            ["xdotool", "getmouselocation"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            log_pass(f"xdotool working: {result.stdout.strip()}")
            return True
        else:
            log_fail(f"xdotool error: {result.stderr}")
            return False
    except Exception as e:
        log_fail(f"xdotool test failed: {e}")
        return False


def test_command_generator():
    """Test command generator with mock model."""
    print(f"\n{Colors.BOLD}Testing command generator...{Colors.RESET}")
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        
        # Test without model (fallback mode)
        generator = CommandGenerator(None)
        result = generator.generate("open firefox")
        
        if "plan" in result or "error" not in result:
            log_pass(f"Generator working (fallback mode)")
            log_info(f"Response: {result.get('description', str(result))}")
            return True
        else:
            log_fail(f"Generator returned error: {result}")
            return False
    except Exception as e:
        log_fail(f"Generator error: {e}")
        return False


def test_validator():
    """Test command validator."""
    print(f"\n{Colors.BOLD}Testing command validator...{Colors.RESET}")
    
    try:
        from core.ai_engine.command_validator import CommandValidator
        
        validator = CommandValidator({})
        
        # Test safe plan
        safe_plan = {
            "plan": [
                {"action": "click", "target": "firefox", "location": [100, 100]},
                {"action": "wait", "seconds": 1},
                {"action": "type", "text": "google.com"}
            ]
        }
        
        if validator.approve_all(safe_plan):
            log_pass("Safe plan approved")
        else:
            log_fail("Safe plan rejected unexpectedly")
            return False
        
        # Test dangerous plan
        dangerous_plan = {
            "plan": [
                {"action": "type", "text": "rm -rf /"}
            ]
        }
        
        if not validator.approve_all(dangerous_plan):
            log_pass("Dangerous plan correctly rejected")
        else:
            log_warn("Dangerous plan was approved (safety check may be incomplete)")
        
        return True
    except Exception as e:
        log_fail(f"Validator error: {e}")
        return False


def test_executor_dry_run():
    """Test executor in dry-run mode."""
    print(f"\n{Colors.BOLD}Testing executor (dry run)...{Colors.RESET}")
    
    try:
        from core.ai_engine.executor import Executor
        
        executor = Executor()
        
        # Test with xdotool not available (simulated)
        test_plan = {
            "plan": [
                {"action": "click", "location": [100, 100]},
                {"action": "type", "text": "test"},
                {"action": "key", "key": "Return"},
                {"action": "wait", "seconds": 0.1}
            ],
            "description": "Test plan"
        }
        
        # This should work even without xdotool (logs but doesn't execute)
        result = executor.execute(test_plan)
        
        log_pass(f"Executor processed plan: {result}")
        return True
    except Exception as e:
        log_fail(f"Executor error: {e}")
        return False


def test_ipc_connection():
    """Test IPC socket connection."""
    print(f"\n{Colors.BOLD}Testing IPC connection...{Colors.RESET}")
    
    socket_path = "/tmp/cosmic-ai.sock"
    
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(socket_path)
        
        # Send test message
        sock.sendall(b"test connection")
        response = sock.recv(4096)
        sock.close()
        
        log_pass(f"IPC connection successful, received {len(response)} bytes")
        return True
    except FileNotFoundError:
        log_warn(f"Socket not found at {socket_path} - AI daemon may not be running")
        return False
    except ConnectionRefusedError:
        log_warn("Connection refused - AI daemon may not be running")
        return False
    except socket.timeout:
        log_warn("Connection timed out")
        return False
    except Exception as e:
        log_fail(f"IPC error: {e}")
        return False


def test_automation_module():
    """Test automation primitives."""
    print(f"\n{Colors.BOLD}Testing automation module...{Colors.RESET}")
    
    try:
        from core.automation.screen_controller import ScreenController
        from core.automation.action_primitives import ActionPrimitives
        from core.automation.window_manager import WindowManager
        
        # Test screen controller (dry run)
        screen = ScreenController(dry_run=True)
        log_pass("ScreenController initialized")
        
        # Test resolution detection
        try:
            res = screen.get_screen_resolution()
            log_pass(f"Screen resolution: {res[0]}x{res[1]}")
        except Exception as e:
            log_warn(f"Could not detect resolution: {e}")
        
        # Test action primitives
        actions = ActionPrimitives(screen)
        result = actions.click(100, 100)
        log_pass(f"ActionPrimitives working: {result.message}")
        
        # Test window manager
        wm = WindowManager(screen)
        log_pass("WindowManager initialized")
        
        return True
    except ImportError as e:
        log_fail(f"Import error: {e}")
        return False
    except Exception as e:
        log_fail(f"Automation error: {e}")
        return False


def run_quick_tests():
    """Run minimal tests for hot-reload feedback."""
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("Validator", test_validator()))
    
    return results


def run_full_tests():
    """Run all tests."""
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("Hardware Detection", test_hardware_detection()))
    results.append(("xdotool", test_xdotool()))
    results.append(("Command Generator", test_command_generator()))
    results.append(("Validator", test_validator()))
    results.append(("Executor", test_executor_dry_run()))
    results.append(("Automation Module", test_automation_module()))
    results.append(("IPC Connection", test_ipc_connection()))
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Cosmic OS AI Test Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument("--full", action="store_true", help="Run all tests (default)")
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{'='*50}")
    print("Cosmic OS - AI System Tests")
    print(f"{'='*50}{Colors.RESET}")
    
    start_time = time.time()
    
    if args.quick:
        results = run_quick_tests()
    else:
        results = run_full_tests()
    
    duration = time.time() - start_time
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*50}")
    print("Test Summary")
    print(f"{'='*50}{Colors.RESET}")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{Colors.BOLD}Results:{Colors.RESET} {passed} passed, {failed} failed")
    print(f"Duration: {duration:.2f}s")
    
    if failed > 0:
        print(f"\n{Colors.YELLOW}Some tests failed. Check output above for details.{Colors.RESET}")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}All tests passed!{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()

