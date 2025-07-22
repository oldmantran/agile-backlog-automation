#!/usr/bin/env python3
"""
Script to check for test cases in the DataVis area path within the Backlog Automation project.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_loader import Config
import requests

def check_datavis_test_cases():
    """Check for test cases in the DataVis area path within the Backlog Automation project."""
    
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
    
    print("🔍 Checking for test cases in DataVis area path within Backlog Automation project...")
    print("=" * 80)
    
    try:
        # Query test cases using WIQL - specifically in DataVis area path
        wiql_url = f"{organization_url}/{requests.utils.quote(project)}/_apis/wit/wiql?api-version=7.0"
        query = "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.WorkItemType] = 'Test Case' AND [System.AreaPath] UNDER 'Backlog Automation\\DataVis' ORDER BY [System.Id]"
        
        payload = {"query": query}
        
        print(f"📋 WIQL Query: {query}")
        print("=" * 80)
        
        response = requests.post(wiql_url, json=payload, auth=auth, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        work_items = result.get('workItems', [])
        
        print(f"✅ Found {len(work_items)} test cases in DataVis area path")
        print("=" * 80)
        
        if work_items:
            print("📋 TEST CASES IN DATAVIS AREA PATH:")
            print("=" * 80)
            print(f"{'ID':<8} {'State':<12} {'Title'}")
            print("-" * 80)
            
            # Get full details for each test case
            for item in work_items:
                test_case_id = item.get('id')
                test_case_url = f"{organization_url}/{requests.utils.quote(project)}/_apis/wit/workitems/{test_case_id}?api-version=7.0"
                test_case_response = requests.get(test_case_url, auth=auth, headers=headers)
                
                if test_case_response.status_code == 200:
                    test_case_item = test_case_response.json()
                    title = test_case_item.get('fields', {}).get('System.Title', 'Unknown')
                    state = test_case_item.get('fields', {}).get('System.State', 'Unknown')
                    area_path = test_case_item.get('fields', {}).get('System.AreaPath', 'Unknown')
                    
                    print(f"{test_case_id:<8} {state:<12} {title}")
                    print(f"        Area Path: {area_path}")
                else:
                    print(f"{test_case_id:<8} {'Error':<12} Could not retrieve details")
            
            print("=" * 80)
            print(f"Total test cases in DataVis area path: {len(work_items)}")
            
            # Show summary by state
            state_counts = {}
            for item in work_items:
                test_case_id = item.get('id')
                test_case_url = f"{organization_url}/{requests.utils.quote(project)}/_apis/wit/workitems/{test_case_id}?api-version=7.0"
                test_case_response = requests.get(test_case_url, auth=auth, headers=headers)
                
                if test_case_response.status_code == 200:
                    test_case_item = test_case_response.json()
                    state = test_case_item.get('fields', {}).get('System.State', 'Unknown')
                    state_counts[state] = state_counts.get(state, 0) + 1
                else:
                    state_counts['Error'] = state_counts.get('Error', 0) + 1
            
            print(f"\n📊 SUMMARY BY STATE:")
            print("-" * 30)
            for state, count in sorted(state_counts.items()):
                print(f"{state}: {count}")
            
            return work_items
        else:
            print("✅ No test cases found in DataVis area path")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return []

if __name__ == "__main__":
    check_datavis_test_cases() 