#!/usr/bin/env python3
"""
Debug script to identify what's causing agent lockups.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from config.config_loader import Config
from agents.epic_strategist import EpicStrategist

def test_simple_agent_call():
    """Test a simple agent call to see if it hangs."""
    print("🔍 Testing simple agent call")
    print("-" * 40)
    
    try:
        # Initialize config
        config = Config()
        print("✅ Config loaded")
        
        # Initialize agent
        agent = EpicStrategist(config)
        print("✅ Epic strategist initialized")
        
        # Test simple product vision
        simple_vision = """
Create a simple task management app that allows users to:
- Create and manage personal tasks
- Set due dates and priorities
- Mark tasks as complete
"""
        
        print("📤 Sending request to agent...")
        start_time = time.time()
        
        # Call agent with timeout awareness
        response = agent.generate_epics(simple_vision)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"📥 Response received in {elapsed:.2f} seconds")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(response) if response else 0}")
        
        if response:
            print("✅ Agent call successful")
            return True
        else:
            print("❌ Agent returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ Agent call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_values():
    """Test if config values are properly loaded."""
    print("\\n🔍 Testing config values")
    print("-" * 40)
    
    try:
        config = Config()
        
        # Check essential values
        grok_api_key = config.get_env("GROK_API_KEY")
        grok_model = config.get_env("GROK_MODEL")
        
        print(f"GROK_API_KEY: {'✅ Set' if grok_api_key else '❌ Missing'}")
        print(f"GROK_MODEL: {grok_model if grok_model else '❌ Missing'}")
        
        if grok_api_key and grok_model:
            print("✅ Grok configuration complete")
            return True
        else:
            print("❌ Grok configuration incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_network_connectivity():
    """Test basic network connectivity to Grok API."""
    print("\\n🔍 Testing network connectivity")
    print("-" * 40)
    
    try:
        import requests
        
        # Test basic connectivity (without auth)
        url = "https://api.x.ai"
        response = requests.get(url, timeout=10)
        
        print(f"API endpoint reachable: {'✅' if response.status_code else '❌'}")
        print(f"Status code: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

def main():
    """Run all debug tests."""
    print("🐛 Debug Agent Lockup")
    print("=" * 50)
    
    # Run tests
    config_ok = test_config_values()
    network_ok = test_network_connectivity()
    
    if config_ok and network_ok:
        agent_ok = test_simple_agent_call()
        
        if agent_ok:
            print("\\n✅ All tests passed - no obvious lockup cause found")
        else:
            print("\\n❌ Agent call failed - this is likely the issue")
    else:
        print("\\n❌ Basic configuration or network issues detected")

if __name__ == "__main__":
    main()
