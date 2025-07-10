#!/usr/bin/env python3
"""
Quick AI API test to diagnose the stall
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ai_api_quick():
    """Quick test of AI API that might be causing stall."""
    print("🔍 Quick AI API Test")
    print("=" * 30)
    
    try:
        from agents.epic_strategist import EpicStrategist
        from config.config_loader import Config
        
        print("📡 Testing AI API with simple query...")
        start_time = time.time()
        
        config = Config()
        strategist = EpicStrategist(config)
        
        # Test with minimal input to see if API responds
        test_vision = "Simple test app with user login"
        context = {'domain': 'test', 'max_epics': 1}
        
        print("⏳ Calling AI API... (timeout in 30 seconds)")
        
        # This should complete quickly if API is working
        result = strategist.generate_epics(test_vision, context, max_epics=1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ AI API responded in {duration:.2f} seconds")
        print(f"📝 Generated {len(result)} epics")
        
        if duration > 30:
            print("⚠️ WARNING: AI API very slow (>30s)")
            return "slow"
        elif duration > 10:
            print("⚠️ WARNING: AI API slow (>10s)")
            return "slow"
        else:
            print("✅ AI API performing normally")
            return "normal"
            
    except Exception as e:
        print(f"❌ AI API test failed: {e}")
        return "failed"

def main():
    result = test_ai_api_quick()
    
    print(f"\n🎯 DIAGNOSIS:")
    if result == "failed":
        print("❌ AI API completely broken")
        print("💡 Check API keys, network, or service status")
    elif result == "slow":
        print("⚠️ AI API working but very slow")
        print("💡 Jobs likely timing out due to slow AI responses")
        print("🔧 SOLUTION: Add timeouts and retry logic")
    else:
        print("✅ AI API working normally")
        print("💡 Stall likely caused by complex content or infinite loop")
    
    return result

if __name__ == "__main__":
    main()
