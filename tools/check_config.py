#!/usr/bin/env python3
"""
Check which config file is being loaded and what the epic limits are
"""

from config.config_loader import Config

def check_config():
    """Check the current configuration."""
    
    print("🔍 Checking Configuration")
    print("=" * 50)
    
    try:
        # Load config
        config = Config()
        
        # Check epic limits
        limits = config.settings.get('workflow', {}).get('limits', {})
        max_epics = limits.get('max_epics')
        max_features = limits.get('max_features_per_epic')
        max_user_stories = limits.get('max_user_stories_per_feature')
        
        print(f"📋 Epic Limits:")
        print(f"   max_epics: {max_epics} ({type(max_epics)})")
        print(f"   max_features_per_epic: {max_features} ({type(max_features)})")
        print(f"   max_user_stories_per_feature: {max_user_stories} ({type(max_user_stories)})")
        
        # Check if this looks like testing config
        if max_epics is not None and max_epics <= 5:
            print(f"⚠️  WARNING: This appears to be a testing configuration!")
            print(f"   max_epics is limited to {max_epics}")
        else:
            print(f"✅ This appears to be a production configuration (unlimited epics)")
        
        # Check other settings
        print(f"\n🔧 Other Settings:")
        print(f"   Workflow sequence: {config.get_workflow_sequence()}")
        print(f"   Parallel processing enabled: {config.settings.get('workflow', {}).get('parallel_processing', {}).get('enabled', False)}")
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_config() 