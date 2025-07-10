#!/usr/bin/env python3
"""
Simple test to verify agent initialization works properly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from agents.feature_decomposer_agent import FeatureDecomposerAgent
from agents.user_story_decomposer_agent import UserStoryDecomposerAgent

def test_agent_initialization():
    """Test that both new agents can be initialized."""
    print("🧪 Testing Agent Initialization")
    print("=" * 40)
    
    try:
        # Initialize config
        config = Config()
        print("✅ Config loaded")
        
        # Test FeatureDecomposerAgent
        feature_agent = FeatureDecomposerAgent(config)
        print("✅ FeatureDecomposerAgent initialized")
        
        # Test UserStoryDecomposerAgent
        story_agent = UserStoryDecomposerAgent(config)
        print("✅ UserStoryDecomposerAgent initialized")
        
        # Test that they have the expected methods
        assert hasattr(feature_agent, 'decompose_epic'), "FeatureDecomposerAgent missing decompose_epic method"
        assert hasattr(story_agent, 'decompose_feature_to_user_stories'), "UserStoryDecomposerAgent missing decompose_feature_to_user_stories method"
        print("✅ Required methods present")
        
        print("\n🎉 All agents initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_initialization()
    exit(0 if success else 1)
