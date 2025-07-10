#!/usr/bin/env python3
"""
Test supervisor initialization with new agents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from supervisor.supervisor import WorkflowSupervisor

def test_supervisor_initialization():
    """Test that supervisor initializes with new agents."""
    print("🧪 Testing Supervisor with New Agents")
    print("=" * 45)
    
    try:
        # Initialize config
        config = Config()
        print("✅ Config loaded")
        
        # Initialize supervisor
        supervisor = WorkflowSupervisor()
        print("✅ Supervisor initialized")
        
        # Check that new agents are present
        expected_agents = [
            'epic_strategist',
            'feature_decomposer_agent', 
            'user_story_decomposer_agent',
            'developer_agent',
            'qa_tester_agent'
        ]
        
        for agent_name in expected_agents:
            assert agent_name in supervisor.agents, f"Missing agent: {agent_name}"
            print(f"✅ {agent_name} present")
        
        # Check backward compatibility
        if 'decomposition_agent' in supervisor.agents:
            print("✅ decomposition_agent backward compatibility present")
        
        # Test default workflow stages
        default_stages = supervisor._get_default_stages()
        print(f"✅ Default workflow stages: {default_stages}")
        
        # Verify workflow can handle the new agents (either directly or via backward compatibility)
        workflow_agents = set(default_stages)
        available_agents = set(supervisor.agents.keys())
        
        # All workflow agents should be available in the supervisor
        missing_agents = workflow_agents - available_agents
        if missing_agents:
            print(f"⚠️  Missing workflow agents: {missing_agents}")
        else:
            print("✅ All workflow agents available in supervisor")
        
        # Verify the new agents can be executed directly
        assert 'feature_decomposer_agent' in supervisor.agents, "feature_decomposer_agent not accessible"
        assert 'user_story_decomposer_agent' in supervisor.agents, "user_story_decomposer_agent not accessible"
        print("✅ New agents directly accessible")
        
        print("\n🎉 Supervisor initialization successful!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supervisor_initialization()
    exit(0 if success else 1)
