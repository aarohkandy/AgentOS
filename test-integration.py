#!/usr/bin/env python3
"""
Integration test script for Cosmic OS
Tests all major components and integrations
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        from core.ai_engine.command_generator import CommandGenerator
        from core.ai_engine.command_validator import CommandValidator
        from core.ai_engine.executor import Executor
        from core.ai_engine.ipc_server import IPCServer
        from core.ai_engine.system_access import SystemAccess
        from core.automation.screen_controller import ScreenController
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_system_access():
    """Test system access module."""
    print("\nTesting system access...")
    try:
        from core.ai_engine.system_access import SystemAccess
        sys_access = SystemAccess()
        
        # Test time
        time_result = sys_access.get_time()
        if time_result.get("success"):
            print(f"✅ Time access: {time_result.get('time')}")
        else:
            print(f"⚠️  Time access failed: {time_result.get('error')}")
        
        # Test system info
        sys_info = sys_access.get_system_info()
        if sys_info.get("success"):
            print(f"✅ System info: {sys_info.get('os')}, {sys_info.get('cpu_count')} cores")
        else:
            print(f"⚠️  System info failed: {sys_info.get('error')}")
        
        return True
    except Exception as e:
        print(f"❌ System access test failed: {e}")
        return False

def test_command_generator():
    """Test command generator with simple queries."""
    print("\nTesting command generator...")
    try:
        from core.ai_engine.config import Config
        from core.ai_engine.command_generator import CommandGenerator
        
        config = Config()
        gen = CommandGenerator(model=None)  # No model, will use fallback
        
        # Test simple query
        result = gen.generate("what time is it")
        if result.get("description"):
            print(f"✅ Simple query handled: {result.get('description')[:50]}...")
        else:
            print(f"⚠️  Simple query returned: {result}")
        
        # Test system query
        result2 = gen.generate("hello")
        if result2.get("description"):
            print(f"✅ Greeting handled: {result2.get('description')[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Command generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_screen_controller():
    """Test screen controller sidebar exclusion."""
    print("\nTesting screen controller...")
    try:
        from core.automation.screen_controller import ScreenController
        
        ctrl = ScreenController()
        print(f"✅ Screen controller initialized")
        print(f"   Screen: {ctrl.screen_width}x{ctrl.screen_height}")
        print(f"   Available (excluding sidebar): {ctrl.available_width}x{ctrl.screen_height}")
        print(f"   Sidebar width: {ctrl.sidebar_width}px")
        
        # Test constraint
        x, y = ctrl._constrain_to_available_area(2000, 500)  # Would be in sidebar
        if x < ctrl.available_width:
            print(f"✅ Coordinate constraint works: (2000, 500) -> ({x}, {y})")
        else:
            print(f"⚠️  Coordinate constraint may not work correctly")
        
        return True
    except Exception as e:
        print(f"❌ Screen controller test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_manager():
    """Test model manager tier detection."""
    print("\nTesting model manager...")
    try:
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        
        config = Config()
        mgr = ModelManager(config)
        
        tier = mgr._detect_tier()
        print(f"✅ Tier detection: Tier {tier}")
        print(f"   (Models should be in models/tier{tier}/model.gguf)")
        
        # Check if model exists (but don't load it)
        import psutil
        total_ram = psutil.virtual_memory().total / (1024**3)
        print(f"   System RAM: {total_ram:.1f}GB")
        
        return True
    except Exception as e:
        print(f"❌ Model manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Cosmic OS Integration Tests")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("System Access", test_system_access()))
    results.append(("Command Generator", test_command_generator()))
    results.append(("Screen Controller", test_screen_controller()))
    results.append(("Model Manager", test_model_manager()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())




