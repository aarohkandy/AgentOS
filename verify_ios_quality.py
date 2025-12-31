#!/usr/bin/env python3
"""
iOS-Quality Verification Script
Quick check that everything is ready for instant, smooth operation
"""

import sys
import time
from pathlib import Path

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def main():
    print("="*60)
    print("iOS-QUALITY VERIFICATION")
    print("="*60)
    print()
    
    checks = []
    
    # Core dependencies
    print("Checking dependencies...")
    deps = [
        ("PyQt6", "PyQt6"),
        ("psutil", "psutil"),
        ("requests", "requests"),
    ]
    
    for name, module in deps:
        ok, error = check_import(module)
        if ok:
            print(f"  ✅ {name}")
            checks.append(True)
        else:
            print(f"  ❌ {name}: {error}")
            checks.append(False)
    
    print()
    
    # Core modules
    print("Checking core modules...")
    core_modules = [
        ("Response Cache", "core.ai_engine.response_cache"),
        ("System Access", "core.ai_engine.system_access"),
        ("Command Generator", "core.ai_engine.command_generator"),
        ("Screen Controller", "core.automation.screen_controller"),
        ("Sidebar", "core.gui.sidebar"),
    ]
    
    for name, module in core_modules:
        try:
            __import__(module)
            print(f"  ✅ {name}")
            checks.append(True)
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            checks.append(False)
    
    print()
    
    # Test cache
    print("Testing response cache...")
    try:
        from core.ai_engine.response_cache import ResponseCache
        cache = ResponseCache()
        cache.set("test", {"description": "test"})
        result = cache.get("test")
        if result and result.get("description") == "test":
            print("  ✅ Cache working")
            checks.append(True)
        else:
            print("  ❌ Cache not working")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Cache error: {e}")
        checks.append(False)
    
    print()
    
    # Test command generator
    print("Testing command generator...")
    try:
        from core.ai_engine.command_generator import CommandGenerator
        cg = CommandGenerator(None)
        
        # Test simple query
        result = cg.generate("5*5")
        if result and result.get("description"):
            print("  ✅ Command generator working")
            checks.append(True)
        else:
            print("  ❌ Command generator not working")
            checks.append(False)
        
        # Check cache
        if cg.cache:
            print("  ✅ Response cache enabled")
            checks.append(True)
        else:
            print("  ⚠️  Response cache disabled")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Command generator error: {e}")
        checks.append(False)
    
    print()
    
    # Test screen controller
    print("Testing screen controller...")
    try:
        from core.automation.screen_controller import ScreenController
        sc = ScreenController()
        if sc.available_width == sc.screen_width - sc.sidebar_width:
            print("  ✅ Screen exclusion working")
            checks.append(True)
        else:
            print("  ❌ Screen exclusion not working")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Screen controller error: {e}")
        checks.append(False)
    
    print()
    
    # Summary
    print("="*60)
    passed = sum(checks)
    total = len(checks)
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("🎉 READY FOR iOS-QUALITY EXPERIENCE!")
        print()
        print("Start with: ./start_cosmic.sh")
        print("Hotkey: Meta+Shift (Windows+Shift)")
        return 0
    else:
        print()
        print("⚠️  Some checks failed. Install missing dependencies:")
        print("   pip3 install --user PyQt6 psutil requests")
        return 1

if __name__ == "__main__":
    sys.exit(main())




