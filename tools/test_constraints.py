#!/usr/bin/env python3
"""
Validate the epic and feature constraints for end-to-end testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.feature_decomposer_agent import FeatureDecomposerAgent

def test_constraints():
    """Test that the epic and feature constraints are working."""
    print("🔍 Testing Epic and Feature Generation Constraints")
    print("=" * 60)
    
    try:
        # Initialize config and agents
        config = Config()
        epic_strategist = EpicStrategist(config)
        feature_decomposer = FeatureDecomposerAgent(config)
        
        # Test product vision
        test_vision = "Create a comprehensive ride-sharing platform that connects drivers and passengers with real-time matching, secure payments, and intelligent routing."
        
        print("Testing Epic Generation with 2 epic limit...")
        print("-" * 40)
        
        # Test epic generation with constraint
        context = {
            'domain': 'ride_sharing',
            'project_name': 'RideShare Platform',
            'target_users': 'drivers and passengers',
            'timeline': '6 months',
            'budget_constraints': 'standard budget',
            'methodology': 'Agile/Scrum'
        }
        
        epics = epic_strategist.generate_epics(test_vision, context, max_epics=2)
        
        print(f"✅ Generated {len(epics)} epics (should be ≤ 2)")
        for i, epic in enumerate(epics, 1):
            print(f"   {i}. {epic.get('title', 'Untitled Epic')}")
        
        if len(epics) > 2:
            print("❌ ERROR: Epic limit constraint not working!")
            return False
        
        print("\nTesting Feature Generation with 3 feature limit...")
        print("-" * 40)
        
        # Test feature generation with constraint for first epic
        if epics:
            first_epic = epics[0]
            features = feature_decomposer.decompose_epic(first_epic, context, max_features=3)
            
            print(f"✅ Generated {len(features)} features for '{first_epic.get('title')}' (should be ≤ 3)")
            for i, feature in enumerate(features, 1):
                print(f"   {i}. {feature.get('title', 'Untitled Feature')}")
            
            if len(features) > 3:
                print("❌ ERROR: Feature limit constraint not working!")
                return False
        
        print(f"\n🎉 Constraints working correctly!")
        print(f"   Max epics: {len(epics)} ≤ 2")
        print(f"   Max features per epic: {len(features)} ≤ 3")
        print(f"   Expected max total features: {len(epics)} epics × 3 features = {len(epics) * 3} features")
        
        return True
        
    except Exception as e:
        print(f"❌ Constraint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_constraints()
    if success:
        print("\n✅ Constraint validation successful!")
        print("🚀 Ready for end-to-end testing with limited output")
    else:
        print("\n❌ Constraint validation failed!")
        print("⚠️  Check agent implementation")
    
    exit(0 if success else 1)
