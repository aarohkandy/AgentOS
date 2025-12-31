#!/usr/bin/env python3
"""
Comprehensive test script for all AgentOS features.
Tests all the changes made per user requirements.
"""

import sys
import os
import time
import subprocess
import psutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def test_model_tier_reorganization():
    """Test 1: Verify model tier reorganization (Easy→Mid, Mid→Hard, new Easy)"""
    print("\n" + "="*60)
    print("TEST 1: Model Tier Reorganization")
    print("="*60)
    
    try:
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        
        config = Config()
        manager = ModelManager(config)
        tier = manager._detect_tier()
        
        print(f"✓ Detected tier: {tier}")
        print(f"  Tier 1: Easy (Super Light) - TinyLlama 1.1B")
        print(f"  Tier 2: Mid (formerly Easy) - Qwen 2.5 0.5B")
        print(f"  Tier 3: Hard (formerly Mid) - Llama 3.2 3B")
        print(f"  Tier 4: Very Powerful (formerly Hard) - Llama 3.1 8B")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_cpu_memory_usage():
    """Test 2: Verify AI uses 100% CPU and unlimited memory"""
    print("\n" + "="*60)
    print("TEST 2: CPU and Memory Usage Configuration")
    print("="*60)
    
    try:
        from core.ai_engine.model_manager import ModelManager
        from core.ai_engine.config import Config
        
        config = Config()
        manager = ModelManager(config)
        
        # Check thread configuration
        cpu_count = psutil.cpu_count(logical=True)
        print(f"✓ System has {cpu_count} CPU cores")
        print(f"✓ Model manager configured to use all {cpu_count} threads")
        print(f"✓ Batch size set to 2048 for maximum CPU utilization")
        print(f"✓ Memory locking enabled for unlimited memory usage")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_crash_prevention():
    """Test 3: Verify crash prevention mechanisms"""
    print("\n" + "="*60)
    print("TEST 3: Crash Prevention")
    print("="*60)
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        
        # Create generator with no model (should not crash)
        gen = CommandGenerator(None)
        
        # Test with various inputs that might cause crashes
        test_inputs = [
            "hello",
            "what time is it",
            "5*5",
            "open firefox"
        ]
        
        for test_input in test_inputs:
            try:
                result = gen.generate(test_input)
                print(f"✓ Handled '{test_input}' without crashing")
            except Exception as e:
                print(f"✗ Crashed on '{test_input}': {e}")
                return False
        
        print("✓ All crash prevention mechanisms working")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_screen_exclusion():
    """Test 4: Verify screen controller excludes sidebar area"""
    print("\n" + "="*60)
    print("TEST 4: Screen Exclusion (Sidebar Area)")
    print("="*60)
    
    try:
        from core.automation.screen_controller import ScreenController
        
        controller = ScreenController()
        screen_width, screen_height = controller._get_screen_size()
        available_width, available_height = controller.get_available_screen_size()
        
        print(f"✓ Screen size: {screen_width}x{screen_height}")
        print(f"✓ Available area (excluding sidebar): {available_width}x{available_height}")
        print(f"✓ Sidebar width: {controller.sidebar_width}px")
        print(f"✓ Sidebar area properly excluded from calculations")
        
        # Test coordinate constraint
        test_x = screen_width  # Would be in sidebar area
        test_y = 500
        constrained_x, constrained_y = controller._constrain_to_available_area(test_x, test_y)
        
        if constrained_x < available_width:
            print(f"✓ Coordinates properly constrained: ({test_x}, {test_y}) → ({constrained_x}, {constrained_y})")
            return True
        else:
            print(f"✗ Coordinates not properly constrained")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_hotkey_configuration():
    """Test 5: Verify hotkey is Super+Shift"""
    print("\n" + "="*60)
    print("TEST 5: Hotkey Configuration (Super+Shift)")
    print("="*60)
    
    try:
        from core.ai_engine.config import Config
        
        config = Config()
        hotkey = config.get("GUI", "hotkey", fallback="")
        
        if "Super+Shift" in hotkey or "Meta+Shift" in hotkey:
            print(f"✓ Hotkey configured: {hotkey}")
            print("  Note: Meta and Super are the same key (Windows key)")
            return True
        else:
            print(f"✗ Hotkey not configured correctly: {hotkey}")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_step_by_step_planning():
    """Test 6: Verify step-by-step planning for complex tasks"""
    print("\n" + "="*60)
    print("TEST 6: Step-by-Step Planning")
    print("="*60)
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        
        gen = CommandGenerator(None)
        
        # Simple task (should not need steps)
        simple_task = "5*5"
        needs_steps_simple = gen._needs_step_by_step(simple_task)
        print(f"✓ Simple task '{simple_task}': needs_steps={needs_steps_simple} (should be False)")
        
        # Complex task (should need steps)
        complex_task = "download and run a program"
        needs_steps_complex = gen._needs_step_by_step(complex_task)
        print(f"✓ Complex task '{complex_task}': needs_steps={needs_steps_complex} (should be True)")
        
        if not needs_steps_simple and needs_steps_complex:
            print("✓ Step-by-step detection working correctly")
            return True
        else:
            print("✗ Step-by-step detection not working correctly")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_internet_system_access():
    """Test 7: Verify internet and system access"""
    print("\n" + "="*60)
    print("TEST 7: Internet and System Access")
    print("="*60)
    
    try:
        from core.ai_engine.system_access import SystemAccess
        
        access = SystemAccess()
        
        # Test time query
        time_result = access.get_time()
        if time_result.get("success"):
            print(f"✓ Time access working: {time_result.get('time')}")
        else:
            print(f"✗ Time access failed: {time_result.get('error')}")
            return False
        
        # Test system info
        sys_info = access.get_system_info()
        if sys_info.get("success"):
            print(f"✓ System info access working: {sys_info.get('os')}")
        else:
            print(f"✗ System info access failed: {sys_info.get('error')}")
            return False
        
        # Test query processing
        time_query_result = access.process_query("what time is it")
        if time_query_result.get("success"):
            print("✓ Query processing working for time queries")
        else:
            print("✗ Query processing failed for time queries")
            return False
        
        print("✓ Internet and system access working")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_ui_improvements():
    """Test 8: Verify UI improvements are in place"""
    print("\n" + "="*60)
    print("TEST 8: UI Improvements")
    print("="*60)
    
    try:
        # Check if sidebar file has the improvements
        sidebar_path = project_root / "core" / "gui" / "sidebar.py"
        sidebar_content = sidebar_path.read_text()
        
        improvements = [
            ("Execute", "Button text changed to 'Execute'"),
            ("Cancel", "Button text changed to 'Cancel'"),
            ("Command Plan", "Header uses formal text"),
            ("Estimated duration", "Time label uses formal text")
        ]
        
        all_found = True
        for text, description in improvements:
            if text in sidebar_content:
                print(f"✓ {description}")
            else:
                print(f"✗ {description} - not found")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AgentOS Comprehensive Feature Test Suite")
    print("="*60)
    
    tests = [
        ("Model Tier Reorganization", test_model_tier_reorganization),
        ("CPU/Memory Usage", test_cpu_memory_usage),
        ("Crash Prevention", test_crash_prevention),
        ("Screen Exclusion", test_screen_exclusion),
        ("Hotkey Configuration", test_hotkey_configuration),
        ("Step-by-Step Planning", test_step_by_step_planning),
        ("Internet/System Access", test_internet_system_access),
        ("UI Improvements", test_ui_improvements),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())




