#!/usr/bin/env python3
"""
Test work item relations API after URL fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator

def main():
    print("🔍 Testing Work Item Relations API...")
    
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    if not integrator.enabled:
        print("❌ Integration not enabled")
        return
    
    # First, get a work item ID to test with
    print("\n📝 Getting a work item to test relations...")
    work_item_ids = integrator.query_work_items(
        work_item_type='User Story',
        area_path='Backlog Automation\\Data Visualization',
        max_items=1
    )
    
    if not work_item_ids:
        print("❌ No work items found to test with")
        return
    
    test_id = work_item_ids[0]
    print(f"✅ Testing with work item ID: {test_id}")
    
    # Test getting relations
    print(f"\n🔗 Testing relations for work item {test_id}...")
    try:
        relations = integrator.get_work_item_relations(test_id)
        print(f"✅ Relations API successful!")
        print(f"   Found {len(relations)} relations")
        
        if relations:
            print("   Sample relations:")
            for i, rel in enumerate(relations[:3], 1):
                rel_type = rel.get('rel', 'Unknown')
                url = rel.get('url', '')
                # Extract work item ID from URL if possible
                if 'workitems/' in url:
                    related_id = url.split('workitems/')[-1]
                    print(f"     {i}. {rel_type} → Work Item {related_id}")
                else:
                    print(f"     {i}. {rel_type} → {url}")
        else:
            print("   No relations found (this is normal for isolated work items)")
            
    except Exception as e:
        print(f"❌ Relations API failed: {e}")
    
    print(f"\n✅ Relations test completed!")

if __name__ == "__main__":
    main()
