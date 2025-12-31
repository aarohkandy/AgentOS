#!/usr/bin/env python3
"""
Comprehensive test suite for Cosmic OS
Tests all features without requiring full model loading
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_system_access():
    """Test system access functionality"""
    print("\n" + "="*60)
    print("TEST 1: System Access")
    print("="*60)
    
    try:
        from core.ai_engine.system_access import SystemAccess
        sa = SystemAccess()
        
        tests = [
            ("Math", "5*5", "25"),
            ("Math", "10+20", "30"),
            ("Time", "what time is it", "Current time"),
            ("System Info", "system info", "System Information"),
        ]
        
        passed = 0
        for name, query, expected in tests:
            try:
                result = sa.handle_query(query)
                if result and expected.lower() in str(result).lower():
                    print(f"  ✓ {name}: {query}")
                    passed += 1
                else:
                    print(f"  ✗ {name}: {query} - Unexpected result: {result}")
            except Exception as e:
                print(f"  ✗ {name}: {query} - Error: {e}")
        
        print(f"\n  Result: {passed}/{len(tests)} passed")
        return passed == len(tests)
    except Exception as e:
        print(f"  ✗ System Access test failed: {e}")
        traceback.print_exc()
        return False

def test_command_generator():
    """Test command generator"""
    print("\n" + "="*60)
    print("TEST 2: Command Generator")
    print("="*60)
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        cg = CommandGenerator(None)  # No model - test fallback
        
        tests = [
            ("Math Query", "5*5", True, False),  # Should have description, no plan
            ("Time Query", "what time is it", True, False),
            ("Greeting", "hello", True, False),
            ("GUI Command", "open firefox", True, True),  # Should have plan
            ("Complex Task", "download and install firefox", True, True),
        ]
        
        passed = 0
        for name, query, should_have_desc, should_have_plan in tests:
            try:
                result = cg.generate(query)
                # Check description - it should exist and be non-empty string
                desc_value = result.get("description", "")
                has_desc = bool(desc_value) and isinstance(desc_value, str) and len(desc_value.strip()) > 0
                has_plan = "plan" in result and len(result.get("plan", [])) > 0
                
                if has_desc == should_have_desc and has_plan == should_have_plan:
                    print(f"  ✓ {name}: {query}")
                    passed += 1
                else:
                    desc_preview = desc_value[:30] if desc_value else "None"
                    print(f"  ✗ {name}: {query} - desc={has_desc} (\"{desc_preview}\") plan={has_plan} (expected desc={should_have_desc} plan={should_have_plan})")
            except Exception as e:
                print(f"  ✗ {name}: {query} - Error: {e}")
                traceback.print_exc()
        
        print(f"\n  Result: {passed}/{len(tests)} passed")
        return passed == len(tests)
    except Exception as e:
        print(f"  ✗ Command Generator test failed: {e}")
        traceback.print_exc()
        return False

def test_step_by_step_detection():
    """Test step-by-step detection"""
    print("\n" + "="*60)
    print("TEST 3: Step-by-Step Detection")
    print("="*60)
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        cg = CommandGenerator(None)
        
        complex_tasks = [
            "download and install firefox",
            "download and run a program",
            "setup and configure git",
        ]
        
        simple_tasks = [
            "open firefox",
            "click button",
            "type hello",
        ]
        
        passed = 0
        total = len(complex_tasks) + len(simple_tasks)
        
        for task in complex_tasks:
            needs = cg._needs_step_by_step(task)
            if needs:
                print(f"  ✓ Complex: {task}")
                passed += 1
            else:
                print(f"  ✗ Complex: {task} - Should need steps")
        
        for task in simple_tasks:
            needs = cg._needs_step_by_step(task)
            if not needs:
                print(f"  ✓ Simple: {task}")
                passed += 1
            else:
                print(f"  ✗ Simple: {task} - Should NOT need steps")
        
        print(f"\n  Result: {passed}/{total} passed")
        return passed == total
    except Exception as e:
        print(f"  ✗ Step-by-step test failed: {e}")
        traceback.print_exc()
        return False

def test_screen_controller():
    """Test screen controller"""
    print("\n" + "="*60)
    print("TEST 4: Screen Controller")
    print("="*60)
    
    try:
        from core.automation.screen_controller import ScreenController
        sc = ScreenController()
        
        # Test sidebar exclusion
        if sc.available_width == sc.screen_width - sc.sidebar_width:
            print(f"  ✓ Sidebar exclusion: {sc.available_width} = {sc.screen_width} - {sc.sidebar_width}")
        else:
            print(f"  ✗ Sidebar exclusion failed")
            return False
        
        # Test coordinate constraint
        test_coords = [
            (100, 100, 100, 100),  # Normal
            (2000, 500, sc.available_width - 1, 500),  # Should be constrained
            (sc.available_width + 100, 300, sc.available_width - 1, 300),  # In sidebar
        ]
        
        passed = 0
        for x, y, expected_x, expected_y in test_coords:
            cx, cy = sc._constrain_to_available_area(x, y)
            if cx == expected_x and cy == expected_y:
                print(f"  ✓ Constraint: ({x}, {y}) -> ({cx}, {cy})")
                passed += 1
            else:
                print(f"  ✗ Constraint: ({x}, {y}) -> ({cx}, {cy}), expected ({expected_x}, {expected_y})")
        
        print(f"\n  Result: {passed}/{len(test_coords)} passed")
        return passed == len(test_coords)
    except Exception as e:
        print(f"  ✗ Screen Controller test failed: {e}")
        traceback.print_exc()
        return False

def test_model_manager():
    """Test model manager tier detection"""
    print("\n" + "="*60)
    print("TEST 5: Model Manager")
    print("="*60)
    
    try:
        from core.ai_engine.model_manager import ModelManager
        from core.ai_engine.config import Config
        
        config = Config()
        mm = ModelManager(config)
        
        tier = mm.tier
        if 1 <= tier <= 5:
            print(f"  ✓ Tier detection: {tier}")
            tier_names = {
                1: "Easy (Super Light)",
                2: "Mid (Easy)",
                3: "Hard (Mid)",
                4: "Very Powerful (Hard)",
                5: "Frontier (Very Powerful)"
            }
            print(f"    Tier name: {tier_names.get(tier, 'Unknown')}")
            return True
        else:
            print(f"  ✗ Invalid tier: {tier}")
            return False
    except Exception as e:
        print(f"  ✗ Model Manager test failed: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling"""
    print("\n" + "="*60)
    print("TEST 6: Error Handling")
    print("="*60)
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        cg = CommandGenerator(None)
        
        # Test with various edge cases
        edge_cases = [
            ("", "Empty string"),
            ("   ", "Whitespace only"),
            ("a" * 10000, "Very long string"),
            ("!@#$%^&*()", "Special characters"),
        ]
        
        passed = 0
        for query, desc in edge_cases:
            try:
                result = cg.generate(query)
                # Should not crash, should return something
                if result and isinstance(result, dict):
                    print(f"  ✓ {desc}: Handled gracefully")
                    passed += 1
                else:
                    print(f"  ✗ {desc}: Invalid result")
            except Exception as e:
                print(f"  ✗ {desc}: Crashed - {e}")
        
        print(f"\n  Result: {passed}/{len(edge_cases)} passed")
        return passed == len(edge_cases)
    except Exception as e:
        print(f"  ✗ Error handling test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("COSMIC OS - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = [
        ("System Access", test_system_access),
        ("Command Generator", test_command_generator),
        ("Step-by-Step Detection", test_step_by_step_detection),
        ("Screen Controller", test_screen_controller),
        ("Model Manager", test_model_manager),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ {name} test crashed: {e}")
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

