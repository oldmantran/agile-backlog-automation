#!/usr/bin/env python3
"""
Run end-to-end test with limited output for quick validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
import json

def run_limited_end_to_end_test():
    """Run end-to-end test with constraints for quick validation."""
    print("🚀 Starting Limited End-to-End Test")
    print("=" * 60)
    print("Constraints:")
    print("  • Max Epics: 2")
    print("  • Max Features per Epic: 3")
    print("  • Expected Total Features: ≤ 6")
    print("=" * 60)
    
    try:
        # Initialize configuration
        config = Config()
        
        # Create test payload for ride-sharing platform
        test_payload = {
            "product_vision": "Create a comprehensive ride-sharing platform that connects drivers and passengers with real-time matching, secure payments, and intelligent routing.",
            "domain": "ride_sharing",
            "project_name": "RideShare Platform Test",
            "target_users": "drivers and passengers",
            "timeline": "6 months",
            "area_path": "Grit",  # Use existing area path with work items
            "iteration_path": "Backlog Automation",  # Use project root
            "enableMockMode": False  # Set to False to create real ADO artifacts
        }
        
        print(f"🎯 Product Vision: {test_payload['product_vision'][:80]}...")
        print(f"🏷️  Domain: {test_payload['domain']}")
        print(f"📍 Area Path: {test_payload['area_path']}")
        print(f"🔄 Mock Mode: {test_payload['enableMockMode']}")
        
        # Initialize supervisor (pass None to use default config)
        supervisor = WorkflowSupervisor(None)
        
        # Set testing constraints
        supervisor._test_max_epics = 2
        supervisor._test_max_features = 3
        
        print("\n⚡ Starting workflow execution...")
        print("-" * 40)
        
        # Execute the workflow
        result = supervisor.execute_workflow(test_payload)
        
        print("\n📊 Execution Results:")
        print("=" * 40)
        
        if result.get('success'):
            # Count generated artifacts
            epics = result.get('epics', [])
            total_features = 0
            total_user_stories = 0
            total_test_cases = 0
            
            print(f"✅ Workflow completed successfully!")
            print(f"📋 Generated {len(epics)} epics")
            
            for i, epic in enumerate(epics, 1):
                features = epic.get('features', [])
                total_features += len(features)
                print(f"   Epic {i}: '{epic.get('title')}' → {len(features)} features")
                
                for j, feature in enumerate(features, 1):
                    user_stories = feature.get('user_stories', [])
                    total_user_stories += len(user_stories)
                    print(f"     Feature {i}.{j}: '{feature.get('title')}' → {len(user_stories)} user stories")
                    
                    for story in user_stories:
                        test_cases = story.get('test_cases', [])
                        total_test_cases += len(test_cases)
            
            print(f"\n📈 Total Artifacts Generated:")
            print(f"   🎯 Epics: {len(epics)} (≤ 2)")
            print(f"   🏗️  Features: {total_features} (≤ 6)")
            print(f"   📖 User Stories: {total_user_stories}")
            print(f"   🧪 Test Cases: {total_test_cases}")
            
            # Validate constraints
            constraint_violations = []
            if len(epics) > 2:
                constraint_violations.append(f"Epic count ({len(epics)}) exceeds limit (2)")
            if total_features > 6:
                constraint_violations.append(f"Feature count ({total_features}) exceeds limit (6)")
            
            if constraint_violations:
                print(f"\n❌ Constraint violations:")
                for violation in constraint_violations:
                    print(f"   • {violation}")
                return False
            else:
                print(f"\n✅ All constraints satisfied!")
                
            # ADO artifacts check
            if not test_payload.get('enableMockMode'):
                print(f"\n🔗 Azure DevOps Integration:")
                print(f"   Organization: {os.getenv('AZURE_DEVOPS_ORG')}")
                print(f"   Project: {os.getenv('AZURE_DEVOPS_PROJECT')}")
                print(f"   Expected test artifacts created in ADO Test Plans")
                print(f"   🧪 Check ADO for {total_test_cases} test cases organized in test suites")
            
            return True
            
        else:
            print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_limited_end_to_end_test()
    if success:
        print("\n🎉 LIMITED END-TO-END TEST SUCCESSFUL!")
        print("✅ All constraints working properly")
        print("✅ Expected test artifacts should be visible in Azure DevOps")
        print("🔍 Check your ADO Test Plans for the generated test structure")
    else:
        print("\n❌ Limited end-to-end test failed!")
        print("⚠️  Check logs for details")
    
    exit(0 if success else 1)
