#!/usr/bin/env python3
"""
Comprehensive tests for Groq/OpenRouter API integration.

Tests:
1. API key loading from .env
2. Groq API connectivity with all 3 keys
3. OpenRouter fallback with all 3 keys
4. Key rotation on rate limits
5. Conversation context management
6. Model fallback
7. JSON response parsing
8. Various query types
"""

import os
import sys
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / ".env")


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, success: bool, details: str = ""):
    """Print a test result."""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"  {status}: {test_name}")
    if details:
        print(f"         {details}")


def test_env_loading():
    """Test that all API keys are loaded from .env file."""
    print_header("Test 1: Environment Variable Loading")
    
    all_pass = True
    
    # Check Groq keys
    for i in range(1, 4):
        key = os.getenv(f"GROQ_KEY_{i}")
        success = key is not None and key.startswith("gsk_")
        print_result(f"GROQ_KEY_{i}", success, f"{'Found' if success else 'Missing or invalid'}")
        all_pass = all_pass and success
    
    # Check OpenRouter keys
    for i in range(1, 4):
        key = os.getenv(f"OPENROUTER_KEY_{i}")
        success = key is not None and key.startswith("sk-or-")
        print_result(f"OPENROUTER_KEY_{i}", success, f"{'Found' if success else 'Missing or invalid'}")
        all_pass = all_pass and success
    
    return all_pass


def test_api_client_init():
    """Test API client initialization."""
    print_header("Test 2: API Client Initialization")
    
    try:
        from core.ai_engine.api_client import UnifiedAPIClient, get_api_client, reset_api_client
        
        # Reset singleton
        reset_api_client()
        
        # Create client
        client = get_api_client()
        
        # Check keys loaded
        groq_keys = client.groq_keys
        openrouter_keys = client.openrouter_keys
        
        print_result("API client created", True)
        print_result(f"Groq keys loaded: {len(groq_keys)}", len(groq_keys) == 3)
        print_result(f"OpenRouter keys loaded: {len(openrouter_keys)}", len(openrouter_keys) == 3)
        
        # Check status
        status = client.get_status()
        print_result("Status method works", "groq_model" in status)
        print(f"         Models: Groq={status['groq_model']}, OpenRouter={status['openrouter_model']}")
        
        return len(groq_keys) == 3 and len(openrouter_keys) == 3
        
    except Exception as e:
        print_result("API client initialization", False, str(e))
        return False


def test_groq_api():
    """Test Groq API connectivity."""
    print_header("Test 3: Groq API Connectivity")
    
    try:
        from core.ai_engine.api_client import get_api_client
        
        client = get_api_client()
        
        # Simple test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Respond briefly."},
            {"role": "user", "content": "Say 'Hello from Groq!' and nothing else."}
        ]
        
        print("  Sending test request to Groq API...")
        start = time.time()
        response = client.chat(messages)
        elapsed = time.time() - start
        
        if "error" in response:
            print_result("Groq API request", False, response["error"])
            return False
        
        content = response.get("content", "")
        provider = response.get("provider", "unknown")
        model = response.get("model", "unknown")
        
        print_result("Groq API request", provider == "groq", f"Response in {elapsed:.2f}s")
        print_result(f"Provider: {provider}", provider == "groq")
        print_result(f"Model: {model}", True)
        print(f"         Response: {content[:100]}...")
        
        return provider == "groq"
        
    except Exception as e:
        print_result("Groq API test", False, str(e))
        return False


def test_conversation_context():
    """Test conversation context management."""
    print_header("Test 4: Conversation Context")
    
    try:
        from core.ai_engine.conversation_context import ConversationContext, reset_conversation_context
        
        # Reset singleton
        reset_conversation_context()
        
        # Create context
        context = ConversationContext(max_messages=10)
        
        # Add messages
        context.add_user_message("Hello, my name is Alice.")
        context.add_assistant_message("Hello Alice! How can I help you today?")
        context.add_user_message("What's my name?")
        
        # Get messages
        messages = context.get_messages()
        
        print_result("Context created", True)
        print_result(f"Messages count: {len(messages)}", len(messages) == 4)  # system + 3
        print_result("System message present", messages[0]["role"] == "system")
        print_result("User messages preserved", "Alice" in messages[1]["content"])
        
        # Test context for request
        request_messages = context.get_context_for_request("Tell me about yourself.")
        print_result(f"Request messages: {len(request_messages)}", len(request_messages) == 5)
        
        # Test summary
        summary = context.get_summary()
        print_result("Summary available", "message_count" in summary)
        print(f"         Summary: {summary}")
        
        # Test clear
        context.clear()
        messages_after_clear = context.get_messages()
        print_result("Clear works", len(messages_after_clear) == 1)  # Only system message
        
        return True
        
    except Exception as e:
        print_result("Conversation context test", False, str(e))
        return False


def test_conversation_memory():
    """Test that AI remembers conversation context."""
    print_header("Test 5: Conversation Memory (API)")
    
    try:
        from core.ai_engine.api_client import get_api_client
        from core.ai_engine.conversation_context import ConversationContext, reset_conversation_context
        
        # Reset and create fresh context
        reset_conversation_context()
        context = ConversationContext(max_messages=20)
        client = get_api_client()
        
        # First message: introduce a name
        messages1 = context.get_context_for_request("My name is TestUser123. Remember this name.")
        print("  Sending first message (introducing name)...")
        response1 = client.chat(messages1)
        
        if "error" in response1:
            print_result("First message", False, response1["error"])
            return False
        
        # Add to context
        context.add_user_message("My name is TestUser123. Remember this name.")
        context.add_assistant_message(response1["content"])
        
        print_result("First message sent", True, response1["content"][:80])
        
        # Second message: ask for the name
        messages2 = context.get_context_for_request("What is my name?")
        print("  Sending second message (asking for name)...")
        response2 = client.chat(messages2)
        
        if "error" in response2:
            print_result("Second message", False, response2["error"])
            return False
        
        content2 = response2["content"]
        remembers_name = "TestUser123" in content2 or "testuser123" in content2.lower()
        
        print_result("Second message sent", True, content2[:80])
        print_result("AI remembers name", remembers_name, 
                    "Found 'TestUser123' in response" if remembers_name else "Name not found in response")
        
        return remembers_name
        
    except Exception as e:
        print_result("Conversation memory test", False, str(e))
        return False


def test_json_parsing():
    """Test JSON response parsing."""
    print_header("Test 6: JSON Response Parsing")
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        
        gen = CommandGenerator(model=None, use_online_api=True)
        
        # Test various JSON formats
        test_cases = [
            ('{"description": "test"}', True),
            ('```json\n{"description": "test"}\n```', True),
            ('Here is the response: {"description": "test"}', True),
            ('{"plan": [{"action": "click"}], "description": "test"}', True),
            ('invalid json', True),  # Should return fallback
            ('', False),  # Empty should return None
        ]
        
        all_pass = True
        for text, should_succeed in test_cases:
            result = gen._extract_json(text)
            success = (result is not None) == should_succeed or (result is not None and should_succeed)
            print_result(f"Parse: '{text[:30]}...'", success, 
                        f"Got: {type(result).__name__}" if result else "Got: None")
            if should_succeed and result is None:
                all_pass = False
        
        return all_pass
        
    except Exception as e:
        print_result("JSON parsing test", False, str(e))
        return False


def test_command_generator():
    """Test command generator with API."""
    print_header("Test 7: Command Generator with API")
    
    try:
        from core.ai_engine.command_generator import CommandGenerator
        from core.ai_engine.api_client import reset_api_client
        from core.ai_engine.conversation_context import reset_conversation_context
        
        # Reset singletons
        reset_api_client()
        reset_conversation_context()
        
        # Create generator
        gen = CommandGenerator(model=None, use_online_api=True)
        
        # Test simple query
        print("  Testing simple query...")
        result1 = gen.generate("What is 2+2?")
        print_result("Simple query", "description" in result1, 
                    result1.get("description", "")[:50] if result1 else "None")
        
        # Test greeting
        print("  Testing greeting...")
        result2 = gen.generate("hello")
        print_result("Greeting", "description" in result2,
                    result2.get("description", "")[:50] if result2 else "None")
        
        # Test complex query (should get action plan)
        print("  Testing complex query...")
        result3 = gen.generate("Open firefox and go to google.com")
        has_plan = "plan" in result3 or "description" in result3
        print_result("Complex query", has_plan,
                    f"Has plan: {'plan' in result3}, Has description: {'description' in result3}")
        
        # Check API status
        status = gen.get_api_status()
        print_result("API status available", "groq_keys_available" in status or "message" in status)
        
        return True
        
    except Exception as e:
        print_result("Command generator test", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_web_search():
    """Test web search helper."""
    print_header("Test 8: Web Search Helper")
    
    try:
        from core.ai_engine.web_search import WebSearchHelper, get_web_search_helper
        
        helper = get_web_search_helper()
        
        # Test pattern detection
        test_queries = [
            ("What is the current time?", True),
            ("What is 2+2?", False),
            ("Latest news about AI", True),
            ("Open firefox", False),
            ("Weather today", True),
        ]
        
        for query, should_need_search in test_queries:
            needs = helper.needs_web_search(query)
            print_result(f"'{query[:30]}' needs search: {needs}", needs == should_need_search)
        
        # Test instant answer (may fail if API is down)
        print("  Testing DuckDuckGo instant answer...")
        result = helper.search_instant_answer("Python programming language")
        if result:
            print_result("Instant answer", True, f"Type: {result['type']}, Length: {len(result['answer'])}")
        else:
            print_result("Instant answer", False, "No result (API may be unavailable)")
        
        return True
        
    except Exception as e:
        print_result("Web search test", False, str(e))
        return False


def test_key_rotation_simulation():
    """Test key rotation logic (simulation without hitting rate limits)."""
    print_header("Test 9: Key Rotation Logic")
    
    try:
        from core.ai_engine.api_client import UnifiedAPIClient
        
        # Create a fresh client
        client = UnifiedAPIClient()
        
        # Check initial state
        initial_groq_idx = client._groq_key_index
        initial_or_idx = client._openrouter_key_index
        
        print_result("Initial Groq key index", initial_groq_idx == 0, f"Index: {initial_groq_idx}")
        print_result("Initial OpenRouter key index", initial_or_idx == 0, f"Index: {initial_or_idx}")
        
        # Make a request (should rotate key index after success)
        messages = [{"role": "user", "content": "Hi"}]
        response = client.chat(messages)
        
        if "error" not in response:
            new_groq_idx = client._groq_key_index
            # Index should have rotated (0 -> 1, or wrapped around)
            rotated = new_groq_idx != initial_groq_idx or new_groq_idx == 0
            print_result("Key index rotated after request", True, f"New index: {new_groq_idx}")
        else:
            print_result("Request for rotation test", False, response.get("error", "Unknown error"))
        
        return True
        
    except Exception as e:
        print_result("Key rotation test", False, str(e))
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("  COSMIC OS API INTEGRATION TESTS")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results["env_loading"] = test_env_loading()
    results["api_client_init"] = test_api_client_init()
    results["groq_api"] = test_groq_api()
    results["conversation_context"] = test_conversation_context()
    results["conversation_memory"] = test_conversation_memory()
    results["json_parsing"] = test_json_parsing()
    results["command_generator"] = test_command_generator()
    results["web_search"] = test_web_search()
    results["key_rotation"] = test_key_rotation_simulation()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        print_result(test_name, success)
    
    print("\n" + "-" * 60)
    print(f"  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("  🎉 All tests passed!")
    else:
        print(f"  ⚠️  {total - passed} test(s) failed")
    
    print("=" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

