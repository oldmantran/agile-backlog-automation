#!/usr/bin/env python3
"""
Test the fixed WIQL query and area path functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator

def test_fixed_integration():
    print("🔧 Testing Fixed Azure DevOps Integration...")
    
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    if not integrator.enabled:
        print("❌ Integration not enabled")
        return
    
    # Test WIQL query for User Stories
    print("\n📋 Testing WIQL query for User Stories...")
    try:
        user_story_ids = integrator.query_work_items("User Story", max_items=10)
        print(f"✅ Found {len(user_story_ids)} User Stories")
        
        if user_story_ids:
            print(f"   IDs: {user_story_ids[:5]}..." if len(user_story_ids) > 5 else f"   IDs: {user_story_ids}")
    except Exception as e:
        print(f"❌ User Story query failed: {e}")
    
    # Test WIQL query with area path filter
    print(f"\n📍 Testing WIQL query with area path filter...")
    try:
        area_path = "Backlog Automation\\Data Visualization"
        filtered_ids = integrator.query_work_items("User Story", area_path=area_path, max_items=10)
        print(f"✅ Found {len(filtered_ids)} User Stories in '{area_path}'")
        
        if filtered_ids:
            print(f"   IDs: {filtered_ids}")
            
            # Get details for these work items
            print(f"\n📝 Getting details for filtered work items...")
            details = integrator.get_work_item_details(filtered_ids[:3])
            if details:
                print(f"✅ Retrieved details for {len(details)} work items")
                for wi in details:
                    area = wi.get('fields', {}).get('System.AreaPath', 'Unknown')
                    title = wi.get('fields', {}).get('System.Title', 'No Title')
                    print(f"   - ID {wi['id']}: {title} (Area: {area})")
            else:
                print(f"❌ Failed to get work item details")
    except Exception as e:
        print(f"❌ Area path filtered query failed: {e}")
    
    # Test Epic query
    print(f"\n👑 Testing Epic query...")
    try:
        epic_ids = integrator.query_work_items("Epic", max_items=5)
        print(f"✅ Found {len(epic_ids)} Epics")
        if epic_ids:
            print(f"   IDs: {epic_ids}")
    except Exception as e:
        print(f"❌ Epic query failed: {e}")

if __name__ == "__main__":
    test_fixed_integration()
