#!/bin/sh
# AI Agent Startup Wrapper

echo "========================================"
echo "AI-OS: Starting AI Agent"
echo "========================================"

# Set Python path
export PYTHONPATH=/opt/ai-agent:$PYTHONPATH

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo "AI Agent location: /opt/ai-agent"
echo ""

# Start a simple demo
echo "Running AI Agent demo..."
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/ai-agent')

try:
    from agent.types import Message
    from agent.llm_interface import EchoBackend
    from agent.agent_core import Agent, AgentConfig
    
    print("\n=== AI-OS Agent Starting ===\n")
    print("✓ Agent modules loaded successfully")
    
    # Create a simple test agent
    backend = EchoBackend()
    agent = Agent(backend=backend, config=AgentConfig(max_response_tokens=100))
    
    print("✓ Agent initialized")
    print("\nAgent is ready to process commands!")
    print("(This is a demo - full agent loop will be implemented next)\n")
    
    # Example interaction
    user_msg = Message(role="user", content="Hello, AI-OS!")
    result = agent.run([user_msg])
    print(f"User: {user_msg.content}")
    print(f"Agent: {result.messages[0].content}")
    
except Exception as e:
    print(f"ERROR: Failed to start agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== AI Agent Demo Complete ===")
print("System is ready. You can now develop your AI agent further.\n")
EOF

# DO NOT BLOCK - Exit so boot continues
exit 0
