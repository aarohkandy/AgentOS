#!/usr/bin/env python3
"""
Comprehensive system test - verifies everything works end-to-end.
"""

import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    try:
        from core.ai_engine.main import CosmicAI
        from core.ai_engine.command_generator import CommandGenerator
        from core.ai_engine.system_access import SystemAccess
        from core.gui.sidebar import CosmicSidebar
        from core.automation.screen_controller import ScreenController
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_access():
    """Test system access capabilities."""
    print("\nTesting system access...")
    try:
        from core.ai_engine.system_access import SystemAccess
        access = SystemAccess()
        
        # Test time
        result = access.handle_query("what time is it")
        if result and "time" in result.get("description", "").lower():
            print("  ✓ Time query works")
        else:
            print("  ✗ Time query failed")
            return False
        
        # Test system info
        result = access.handle_query("system info")
        if result and "system" in result.get("description", "").lower():
            print("  ✓ System info works")
        else:
            print("  ✗ System info failed")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ System access failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_command_generator():
    """Test command generator."""
    print("\nTesting command generator...")
    try:
        from core.ai_engine.command_generator import CommandGenerator
        
        gen = CommandGenerator(None)  # No model - use fallback
        
        # Test simple query detection
        if gen._is_simple_query("5*5"):
            print("  ✓ Simple query detection works")
        else:
            print("  ✗ Simple query detection failed")
            return False
        
        # Test step-by-step detection
        if gen._needs_step_by_step("download and run a program"):
            print("  ✓ Step-by-step detection works")
        else:
            print("  ✗ Step-by-step detection failed")
            return False
        
        # Test simple query handling
        result = gen._handle_simple_query("5*5")
        if result and "25" in result.get("description", ""):
            print("  ✓ Simple query handling works")
        else:
            print("  ✗ Simple query handling failed")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Command generator failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sidebar_creation():
    """Test sidebar can be created (without showing)."""
    print("\nTesting sidebar creation...")
    try:
        from PySide6.QtWidgets import QApplication
        from core.gui.sidebar import CosmicSidebar
        
        # Create app (required for Qt widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create sidebar
        sidebar = CosmicSidebar()
        print("  ✓ Sidebar created successfully")
        
        # Check properties
        assert sidebar.sidebar_width == 420, "Sidebar width should be 420"
        assert hasattr(sidebar, 'toggle_sidebar'), "Should have toggle_sidebar method"
        assert hasattr(sidebar, 'show_sidebar'), "Should have show_sidebar method"
        assert hasattr(sidebar, 'hide_sidebar'), "Should have hide_sidebar method"
        print("  ✓ Sidebar properties correct")
        
        return True
    except Exception as e:
        print(f"  ✗ Sidebar creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_screen_controller():
    """Test screen controller."""
    print("\nTesting screen controller...")
    try:
        from core.automation.screen_controller import ScreenController
        
        controller = ScreenController()
        assert controller.sidebar_width == 420, "Sidebar width should be 420"
        assert hasattr(controller, 'available_width'), "Should have available_width"
        print("  ✓ Screen controller initialized")
        print(f"  ✓ Available width: {controller.available_width}px (excludes sidebar)")
        
        return True
    except Exception as e:
        print(f"  ✗ Screen controller failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("Cosmic OS - Comprehensive System Test")
    print("=" * 70)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("System Access", test_system_access()))
    results.append(("Command Generator", test_command_generator()))
    results.append(("Sidebar Creation", test_sidebar_creation()))
    results.append(("Screen Controller", test_screen_controller()))
    
    print("\n" + "=" * 70)
    print("Test Results:")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:25} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("✓ All tests passed! System is ready.")
        return 0
    else:
        print("✗ Some tests failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())




