#!/usr/bin/env python3
"""
Debug version of ADO cleanup script - runs non-interactively to test the issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.auth import HTTPBasicAuth
from config.config_loader import Config
import time

def main():
    print("🔍 Debug ADO Cleanup - Non-Interactive Mode")
    print("=" * 50)
    
    # Load config
    try:
        config = Config()
        print("✅ Config loaded successfully")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return
    
    org = config.get_env("AZURE_DEVOPS_ORG")
    project = config.get_env("AZURE_DEVOPS_PROJECT")
    pat = config.get_env("AZURE_DEVOPS_PAT")
    
    print(f"Organization: {org}")
    print(f"Project: {project}")
    print(f"PAT: {'Set' if pat else 'Missing'}")
    
    if org and org.startswith("https://dev.azure.com/"):
        org = org.replace("https://dev.azure.com/", "")
        print(f"Cleaned org name: {org}")
    
    project_base_url = f"https://dev.azure.com/{org}/{project}/_apis"
    auth = HTTPBasicAuth('', pat)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    print(f"\\nBase URL: {project_base_url}")
    
    # Test 1: Basic connectivity
    print("\\n🧪 Test 1: Basic API connectivity")
    try:
        test_url = f"https://dev.azure.com/{org}/_apis/projects/{project}?api-version=7.0"
        print(f"Testing: {test_url}")
        
        start_time = time.time()
        response = requests.get(test_url, auth=auth, headers=headers, timeout=10)
        elapsed = time.time() - start_time
        
        print(f"Response time: {elapsed:.2f}s")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Basic connectivity works")
        else:
            print(f"❌ Basic connectivity failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Basic connectivity exception: {e}")
        return
    
    # Test 2: WIQL Query
    print("\\n🧪 Test 2: WIQL Query for work items")
    wiql_query = {
        "query": f"SELECT [System.Id], [System.Title], [System.WorkItemType] FROM WorkItems WHERE [System.TeamProject] = '{project}'"
    }
    
    wiql_url = f"{project_base_url}/wit/wiql?api-version=7.0"
    print(f"WIQL URL: {wiql_url}")
    print(f"Query: {wiql_query['query']}")
    
    try:
        start_time = time.time()
        print("📡 Sending WIQL request...")
        response = requests.post(wiql_url, json=wiql_query, auth=auth, headers=headers, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"WIQL Response time: {elapsed:.2f}s")
        print(f"WIQL Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ WIQL query failed: {response.text}")
            return
        
        wiql_result = response.json()
        work_items = wiql_result.get('workItems', [])
        
        print(f"✅ Found {len(work_items)} work items")
        
        # Show first few work item IDs
        if work_items:
            print("Work item IDs:")
            for i, wi in enumerate(work_items[:5]):
                print(f"  {i+1}. ID: {wi['id']}")
            if len(work_items) > 5:
                print(f"  ... and {len(work_items) - 5} more")
        
        # Test 3: Get details for first work item (if any)
        if work_items:
            print("\\n🧪 Test 3: Get work item details")
            first_id = work_items[0]['id']
            details_url = f"{project_base_url}/wit/workitems/{first_id}?api-version=7.0"
            print(f"Details URL: {details_url}")
            
            try:
                start_time = time.time()
                response = requests.get(details_url, auth=auth, headers=headers, timeout=15)
                elapsed = time.time() - start_time
                
                print(f"Details response time: {elapsed:.2f}s")
                print(f"Details status code: {response.status_code}")
                
                if response.status_code == 200:
                    item_data = response.json()
                    title = item_data['fields'].get('System.Title', 'No title')
                    work_type = item_data['fields'].get('System.WorkItemType', 'Unknown')
                    print(f"✅ Sample work item: {work_type} - {title}")
                else:
                    print(f"❌ Failed to get details: {response.text}")
                    
            except Exception as e:
                print(f"❌ Details request exception: {e}")
        
        print(f"\\n🎯 Summary:")
        print(f"  - Connection: ✅ Working")
        print(f"  - WIQL Query: ✅ Working") 
        print(f"  - Work Items Found: {len(work_items)}")
        
        if len(work_items) == 0:
            print("  - Status: 🎉 Project is already clean!")
        else:
            print(f"  - Status: ⚠️  {len(work_items)} work items need cleanup")
            print("  - To clean up, run the interactive cleanup script")
        
    except Exception as e:
        print(f"❌ WIQL query exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
