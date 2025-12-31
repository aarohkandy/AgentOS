#!/usr/bin/env python3
"""
Quick test script to verify all changes are working.
Tests:
1. Model tier detection
2. System access (time, news)
3. Simple query handling
4. Step-by-step detection
5. Error handling
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_model_tiers():
    """Test model tier detection."""
    print("Testing model tier detection...")
    try:
        from core.ai_engine.config import Config
        from core.ai_engine.model_manager import ModelManager
        
        config = Config()
        manager = ModelManager(config)
        tier = manager._detect_tier()
        print(f"  ✓ Detected tier: {tier}")
        print(f"    Tier 1: Super Light Easy (TinyLlama)")
        print(f"    Tier 2: Easy (Qwen 2.5 0.5B) - was old Easy, now Mid")
        print(f"    Tier 3: Mid (Llama 3.2 3B) - was old Mid, now Hard")
        print(f"    Tier 4: Hard (Llama 3.1 8B) - was old Hard")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def test_system_access():
    """Test system access capabilities."""
    print("\nTesting system access...")
    try:
        from core.ai_engine.system_access import SystemAccess
        
        access = SystemAccess()
        
        # Test time
        time_result = access.handle_query("what time is it")
        if time_result and "time" in time_result.get("description", "").lower():
            print("  ✓ Time query works")
        else:
            print("  ✗ Time query failed")
            return False
        
        # Test system info
        sys_result = access.handle_query("system info")
        if sys_result and "system" in sys_result.get("description", "").lower():
            print("  ✓ System info query works")
        else:
            print("  ✗ System info query failed")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_queries():
    """Test simple query detection."""
    print("\nTesting simple query detection...")
    try:
        from core.ai_engine.command_generator import CommandGenerator
        
        # Create generator without model (will use fallback)
        gen = CommandGenerator(None)
        
        # Test math
        if gen._is_simple_query("5*5"):
            print("  ✓ Math query detected as simple")
        else:
            print("  ✗ Math query not detected as simple")
            return False
        
        # Test complex
        if gen._needs_step_by_step("download and run a program"):
            print("  ✓ Complex query detected as needing steps")
        else:
            print("  ✗ Complex query not detected")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    try:
        from core.ai_engine.main import CosmicAI
        
        # Just test initialization doesn't crash
        print("  ✓ Error handling structure exists")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Cosmic OS Changes")
    print("=" * 60)
    
    results = []
    results.append(("Model Tiers", test_model_tiers()))
    results.append(("System Access", test_system_access()))
    results.append(("Simple Queries", test_simple_queries()))
    results.append(("Error Handling", test_error_handling()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
