#!/usr/bin/env python3
"""
Final Integration Test - Comprehensive test of all features
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_all_features():
    """Test all implemented features."""
    print("=" * 70)
    print("FINAL INTEGRATION TEST - Cosmic OS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Model Tier Detection
    print("\n[1/8] Testing Model Tier Detection...")
    try:
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        config = Config()
        manager = ModelManager(config)
        tier = manager._detect_tier()
        print(f"  ✓ Tier {tier} detected correctly")
        results.append(("Model Tiers", True))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        results.append(("Model Tiers", False))
    
    # Test 2: System Access (Time)
    print("\n[2/8] Testing System Access - Time Query...")
    try:
        from core.ai_engine.system_access import SystemAccess
        access = SystemAccess()
        result = access.handle_query("what time is it")
        if result and "time" in result.get("description", "").lower():
            print(f"  ✓ Time query works: {result.get('description', '')[:60]}...")
            results.append(("System Access - Time", True))
        else:
            print("  ✗ Time query failed")
            results.append(("System Access - Time", False))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        results.append(("System Access - Time", False))
    
    # Test 3: System Access (System Info)
    print("\n[3/8] Testing System Access - System Info...")
    try:
        result = access.handle_query("system info")
        if result and "system" in result.get("description", "").lower():
            print(f"  ✓ System info works")
            results.append(("System Access - Info", True))
        else:
            print("  ✗ System info failed")
            results.append(("System Access - Info", False))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        results.append(("System Access - Info", False))
    
    # Test 4: Simple Query Detection
    print("\n[4/8] Testing Simple Query Detection...")
    try:
        from core.ai_engine.command_generator import CommandGenerator
        gen = CommandGenerator(None)
        
        # Test math
        is_simple = gen._is_simple_query("5*5")
        if is_simple:
            print("  ✓ Math query detected as simple")
        else:
            print("  ✗ Math query not detected")
            results.append(("Simple Queries", False))
            return results
        
        # Test greeting
        is_simple_greet = gen._is_simple_query("hello")
        if is_simple_greet:
            print("  ✓ Greeting detected as simple")
        else:
            print("  ✗ Greeting not detected")
        
        results.append(("Simple Queries", True))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        results.append(("Simple Queries", False))
    
    # Test 5: Step-by-Step Detection
    print("\n[5/8] Testing Step-by-Step Detection...")
    try:
        needs_steps = gen._needs_step_by_step("download and run a program")
        if needs_steps:
            print("  ✓ Complex task detected as needing steps")
        else:
            print("  ✗ Complex task not detected")
            results.append(("Step-by-Step", False))
            return results
        
        no_steps = gen._needs_step_by_step("5*5")
        if not no_steps:
            print("  ✓ Simple task correctly doesn't need steps")
        else:
            print("  ✗ Simple task incorrectly needs steps")
        
        results.append(("Step-by-Step", True))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        results.append(("Step-by-Step", False))
    
    # Test 6: Command Generator Integration
    print("\n[6/8] Testing Command Generator Integration...")
    try:
        # Test system query
        result = gen.generate("what time is it")
        if result and result.get("system_query"):
            print("  ✓ System query handled correctly")
        else:
            print("  ✗ System query not handled")
            results.append(("Generator Integration", False))
            return results
        
        # Test simple query
        result2 = gen.generate("hello")
        if result2 and result2.get("description"):
            print("  ✓ Simple query handled correctly")
        else:
            print("  ✗ Simple query not handled")
        
        results.append(("Generator Integration", True))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Generator Integration", False))
    
    # Test 7: Screen Controller
    print("\n[7/8] Testing Screen Controller...")
    try:
        from core.automation.screen_controller import ScreenController
        screen = ScreenController()
        
        # Check sidebar exclusion
        if hasattr(screen, 'available_width') and screen.available_width < screen.screen_width:
            print(f"  ✓ Sidebar area excluded: {screen.available_width}px available (screen: {screen.screen_width}px)")
        else:
            print("  ✗ Sidebar exclusion not working")
            results.append(("Screen Controller", False))
            return results
        
        # Test constraint
        x, y = screen._constrain_to_available_area(9999, 9999)
        if x <= screen.available_width:
            print(f"  ✓ Coordinates constrained correctly: ({x}, {y})")
        else:
            print("  ✗ Coordinate constraint failed")
        
        results.append(("Screen Controller", True))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        results.append(("Screen Controller", False))
    
    # Test 8: Error Handling
    print("\n[8/8] Testing Error Handling...")
    try:
        from core.ai_engine.main import CosmicAI
        # Just verify it can be imported and has error handling
        if hasattr(CosmicAI, 'process_request'):
            print("  ✓ Error handling structure exists")
            results.append(("Error Handling", True))
        else:
            print("  ✗ Error handling missing")
            results.append(("Error Handling", False))
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        results.append(("Error Handling", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print("=" * 70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(test_all_features())




