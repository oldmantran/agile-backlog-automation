#!/usr/bin/env python3
"""
Quick diagnostic script to identify why jobs stall at 60%
"""

import sys
import os
import requests
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ai_api_connectivity():
    """Test if AI API is responsive."""
    print("🔍 Testing AI API Connectivity...")
    
    try:
        # Import the base agent to test AI connectivity
        from agents.base_agent import BaseAgent
        
        # Create a simple test agent
        agent = BaseAgent()
        
        # Test with a very simple, fast query
        start_time = time.time()
        response = agent.run("Say 'Hello' in one word only.", {})
        end_time = time.time()
        
        if response:
            print(f"✅ AI API responsive ({end_time - start_time:.2f}s)")
            print(f"   Response: {response[:50]}...")
            return True
        else:
            print("❌ AI API returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ AI API test failed: {e}")
        return False

def test_supervisor_initialization():
    """Test if supervisor can initialize without hanging."""
    print("\n🔍 Testing Supervisor Initialization...")
    
    try:
        from supervisor.supervisor import WorkflowSupervisor
        from config.config_loader import Config
        
        start_time = time.time()
        
        # Test supervisor creation (this might hang if there's an init issue)
        supervisor = WorkflowSupervisor(
            organization_url="https://dev.azure.com/test",
            project="test",
            personal_access_token="test",
            area_path="test",
            iteration_path="test"
        )
        
        end_time = time.time()
        print(f"✅ Supervisor initialized successfully ({end_time - start_time:.2f}s)")
        return True
        
    except Exception as e:
        print(f"❌ Supervisor initialization failed: {e}")
        return False

def test_agent_creation():
    """Test if individual agents can be created."""
    print("\n🔍 Testing Individual Agent Creation...")
    
    agent_tests = [
        ("EpicStrategist", "agents.epic_strategist", "EpicStrategist"),
        ("FeatureDecomposer", "agents.feature_decomposer_agent", "FeatureDecomposerAgent"),
        ("UserStoryDecomposer", "agents.user_story_decomposer_agent", "UserStoryDecomposerAgent"),
    ]
    
    results = {}
    
    for name, module_path, class_name in agent_tests:
        try:
            start_time = time.time()
            
            # Dynamic import and creation
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            agent = agent_class()
            
            end_time = time.time()
            print(f"✅ {name} created successfully ({end_time - start_time:.2f}s)")
            results[name] = True
            
        except Exception as e:
            print(f"❌ {name} creation failed: {e}")
            results[name] = False
    
    return results

def analyze_stall_point():
    """Analyze what typically happens at 60% progress."""
    print("\n🔍 Analyzing 60% Progress Point...")
    
    # Based on the supervisor workflow, 60% is typically:
    # - Epic generation complete (30%)
    # - Feature decomposition complete (60%)
    # - About to start user story decomposition
    
    print("📊 60% Progress Point Analysis:")
    print("   - Epic Strategist: ✅ Complete")
    print("   - Feature Decomposer: 🔄 Should be complete")
    print("   - User Story Decomposer: ⏳ About to start")
    print("   - Most likely stall: Feature Decomposer taking too long")
    print("   - Possible cause: Complex feature generation or AI timeout")

def main():
    """Run comprehensive diagnostics."""
    print("🚨 STALL DIAGNOSIS - Quick Efficiency Test")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    # Test AI connectivity first (most likely cause)
    ai_working = test_ai_api_connectivity()
    
    if not ai_working:
        print("\n🎯 PRIMARY SUSPECT: AI API connectivity issues")
        print("💡 RECOMMENDATION: Check API keys, network, or AI service status")
        return False
    
    # Test supervisor initialization
    supervisor_working = test_supervisor_initialization()
    
    if not supervisor_working:
        print("\n🎯 PRIMARY SUSPECT: Supervisor initialization hanging")
        print("💡 RECOMMENDATION: Check Azure DevOps credentials or config")
        return False
    
    # Test individual agents
    agent_results = test_agent_creation()
    
    # Analyze stall point
    analyze_stall_point()
    
    print("\n🎯 DIAGNOSIS SUMMARY:")
    if ai_working and supervisor_working and all(agent_results.values()):
        print("✅ All components appear functional")
        print("💡 LIKELY CAUSE: AI API timeout during complex generation")
        print("🔧 RECOMMENDATION: Add timeout handling and retry logic")
    else:
        print("❌ Issues found in component testing")
        print("💡 RECOMMENDATION: Fix failing components before retry")
    
    print(f"\n⏱️ Diagnosis completed at: {datetime.now().strftime('%H:%M:%S')}")
    return True

if __name__ == "__main__":
    main()
