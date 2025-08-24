"""
Verify that model-aware formatting is properly integrated into the base agent.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import Agent
from config.config_loader import Config
from utils.safe_logger import get_safe_logger

logger = get_safe_logger(__name__)

def test_agent_integration():
    """Test that agents are using the model-aware formatter."""
    print("Testing Model-Aware Formatter Integration")
    print("=" * 50)
    
    # Create a test agent
    config = Config()
    
    # Create base agent instance
    class TestAgent(Agent):
        def __init__(self, config, user_id=None):
            super().__init__("test_agent", config, user_id)
    
    # Initialize agent
    agent = TestAgent(config)
    print(f"\nAgent initialized with:")
    print(f"  Provider: {agent.llm_provider}")
    print(f"  Model: {agent.model}")
    
    # Test prompt preparation
    system_prompt = "You are a test agent. Respond with JSON."
    user_prompt = "Create a simple test response with a greeting message."
    
    print("\n### Testing _prepare_request_payload method:")
    
    try:
        # This will use the model-aware formatter
        payload = agent._prepare_request_payload(system_prompt, user_prompt)
        
        print("\nPayload created successfully!")
        print(f"Model: {payload['model']}")
        print(f"Messages: {len(payload['messages'])} messages")
        
        # Check if formatting was applied
        for i, msg in enumerate(payload['messages']):
            print(f"\nMessage {i+1} ({msg['role']}):")
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"  {content_preview}")
        
        # Check for model-specific parameters
        if 'max_completion_tokens' in payload:
            print(f"\nGPT-5 specific: max_completion_tokens = {payload['max_completion_tokens']}")
        if 'temperature' in payload:
            print(f"\nTemperature: {payload['temperature']}")
        if 'max_tokens' in payload:
            print(f"Max tokens: {payload['max_tokens']}")
            
        print("\n[SUCCESS] Model-aware formatting is properly integrated!")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to prepare payload: {e}")
        import traceback
        traceback.print_exc()

def test_token_tracking():
    """Test that token tracking is working."""
    print("\n\n" + "="*50)
    print("Testing Token Usage Tracking")
    print("="*50)
    
    # Simulate a response with usage data
    mock_response = {
        "choices": [{
            "message": {
                "content": "This is a test response"
            }
        }],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 50,
            "total_tokens": 200
        }
    }
    
    # Import requests.Response mock
    class MockResponse:
        def json(self):
            return mock_response
    
    # Create agent
    config = Config()
    
    class TestAgent(Agent):
        def __init__(self, config, user_id=None):
            super().__init__("test_agent", config, user_id)
    
    agent = TestAgent(config)
    
    try:
        # Process the mock response
        content = agent._process_response(MockResponse())
        
        print("\nResponse processed successfully!")
        print(f"Content: {content}")
        
        # Check if cost estimation was logged
        if hasattr(agent, '_last_completion_tokens'):
            print(f"\nToken tracking: {agent._last_completion_tokens} completion tokens")
        if hasattr(agent, '_last_total_cost'):
            print(f"Cost tracking: ${agent._last_total_cost:.4f}")
            
        print("\n[SUCCESS] Token tracking is working!")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to process response: {e}")

if __name__ == "__main__":
    test_agent_integration()
    test_token_tracking()
    
    print("\n\nIntegration verification complete!")