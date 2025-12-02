import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath('src'))

from agent.types import Message
from agent.llm_interface import EchoBackend
from agent.agent_core import Agent, AgentConfig

def run_demo():
    print("\n=== AI-OS Agent Status Check ===\n")
    
    # 1. Initialize
    print("1. Initializing Agent Core...")
    try:
        backend = EchoBackend()
        agent = Agent(backend=backend, config=AgentConfig(max_response_tokens=100))
        print("   ✓ Agent initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return

    # 2. Run a test interaction
    print("\n2. Testing Interaction Loop...")
    try:
        user_input = "System status check"
        print(f"   User Input: '{user_input}'")
        
        user_msg = Message(role="user", content=user_input)
        result = agent.run([user_msg])
        
        response = result.messages[0].content
        print(f"   Agent Response: '{response}'")
        print("   ✓ Interaction loop working")
    except Exception as e:
        print(f"   ❌ Interaction failed: {e}")
        return

    print("\n=== Status: OPERATIONAL ===")
    print("The agent core is functional. The OS layer needs to be built to run this in a VM.")

if __name__ == "__main__":
    run_demo()
