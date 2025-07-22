#!/usr/bin/env python3
"""
Script to list all test plans in the Backlog Automation project.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_loader import Config
import requests

def list_test_plans():
    """List all test plans in the Backlog Automation project."""
    
    # Configuration
    organization_url = "https://dev.azure.com/c4workx"
    project = "Backlog Automation"
    
    # Get PAT from config
    config = Config()
    pat = config.env.get('AZURE_DEVOPS_PAT')
    
    if not pat:
        raise ValueError("Personal Access Token is required")
    
    # Set up authentication and headers
    auth = requests.auth.HTTPBasicAuth('', pat)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print("🔍 Listing all test plans in Backlog Automation project...")
    print("=" * 80)
    
    try:
        # Query test plans using WIQL
        wiql_url = f"{organization_url}/{requests.utils.quote(project)}/_apis/wit/wiql?api-version=7.0"
        query = "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Test Plan' AND [System.TeamProject] = 'Backlog Automation' ORDER BY [System.Id]"
        
        payload = {"query": query}
        
        print(f"📋 WIQL Query: {query}")
        print("=" * 80)
        
        response = requests.post(wiql_url, json=payload, auth=auth, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        work_items = result.get('workItems', [])
        test_plan_ids = [item['id'] for item in work_items]
        
        print(f"✅ Found {len(test_plan_ids)} test plans")
        print("=" * 80)
        
        if test_plan_ids:
            print("📋 TEST PLANS IN BACKLOG AUTOMATION PROJECT:")
            print("=" * 80)
            print(f"{'ID':<8} {'State':<12} {'Title'}")
            print("-" * 80)
            
            # Get full details for each test plan
            for plan_id in test_plan_ids:
                plan_url = f"{organization_url}/{requests.utils.quote(project)}/_apis/wit/workitems/{plan_id}?api-version=7.0"
                plan_response = requests.get(plan_url, auth=auth, headers=headers)
                
                if plan_response.status_code == 200:
                    plan_item = plan_response.json()
                    title = plan_item.get('fields', {}).get('System.Title', 'Unknown')
                    state = plan_item.get('fields', {}).get('System.State', 'Unknown')
                    
                    print(f"{plan_id:<8} {state:<12} {title}")
                else:
                    print(f"{plan_id:<8} {'Error':<12} Could not retrieve details")
            
            print("=" * 80)
            print(f"Total test plans: {len(test_plan_ids)}")
            
            # Show summary by state
            state_counts = {}
            for plan_id in test_plan_ids:
                plan_url = f"{organization_url}/{requests.utils.quote(project)}/_apis/wit/workitems/{plan_id}?api-version=7.0"
                plan_response = requests.get(plan_url, auth=auth, headers=headers)
                
                if plan_response.status_code == 200:
                    plan_item = plan_response.json()
                    state = plan_item.get('fields', {}).get('System.State', 'Unknown')
                    state_counts[state] = state_counts.get(state, 0) + 1
                else:
                    state_counts['Error'] = state_counts.get('Error', 0) + 1
            
            print(f"\n📊 SUMMARY BY STATE:")
            print("-" * 30)
            for state, count in sorted(state_counts.items()):
                print(f"{state}: {count}")
            
            return test_plan_ids
        else:
            print("✅ No test plans found")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return []

if __name__ == "__main__":
    list_test_plans() 