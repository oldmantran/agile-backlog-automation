#!/usr/bin/env python3
"""
Test specific PAT permissions to identify what's missing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
import requests

def main():
    print("🔍 Testing PAT Permissions...")
    
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    if not integrator.enabled:
        print("❌ Integration not enabled")
        return
    
    # Test 1: Work Items (we know this works)
    print("\n📝 Test 1: Work Items API (should work)")
    wiql_url = f"{integrator.project_base_url}/wit/wiql?api-version=7.0"
    wiql_query = {
        "query": "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Epic' ORDER BY [System.Id] DESC"
    }
    
    try:
        response = requests.post(wiql_url, json=wiql_query, auth=integrator.auth, headers=integrator.headers)
        if response.status_code == 200:
            print("✅ Work Items API: SUCCESS")
            work_items = response.json().get('workItems', [])
            print(f"   Found {len(work_items)} epics")
        else:
            print(f"❌ Work Items API: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Work Items API: ERROR - {e}")
    
    # Test 2: Classification Nodes (we know this fails)
    print("\n🏗️ Test 2: Classification Nodes API (expected to fail)")
    area_url = f"{integrator.org_base_url}/wit/classificationnodes/Areas?api-version=7.0"
    
    try:
        response = requests.get(area_url, auth=integrator.auth)
        if response.status_code == 200:
            print("✅ Classification Nodes API: SUCCESS")
        else:
            print(f"❌ Classification Nodes API: FAILED ({response.status_code})")
            print(f"   This requires 'Project and team (read)' permission")
    except Exception as e:
        print(f"❌ Classification Nodes API: ERROR - {e}")
    
    # Test 3: Project Info (basic project read)
    print("\n📋 Test 3: Project API (basic read)")
    project_url = f"{integrator.org_base_url}/projects/{integrator.project}?api-version=7.0"
    
    try:
        response = requests.get(project_url, auth=integrator.auth)
        if response.status_code == 200:
            print("✅ Project API: SUCCESS")
            project_info = response.json()
            print(f"   Project: {project_info.get('name')}")
        else:
            print(f"❌ Project API: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Project API: ERROR - {e}")
    
    # Test 4: Alternative - Query work items with area path in results
    print("\n🔍 Test 4: Work Items with Area Path (workaround)")
    wiql_url = f"{integrator.project_base_url}/wit/wiql?api-version=7.0"
    wiql_query = {
        "query": """
        SELECT [System.Id], [System.AreaPath] 
        FROM WorkItems 
        WHERE [System.WorkItemType] IN ('Epic', 'Feature', 'User Story') 
        ORDER BY [System.Id] DESC
        """
    }
    
    try:
        response = requests.post(wiql_url, json=wiql_query, auth=integrator.auth, headers=integrator.headers)
        if response.status_code == 200:
            print("✅ Work Items with Area Path: SUCCESS")
            work_items = response.json().get('workItems', [])
            print(f"   Found {len(work_items)} work items")
            
            # Get details to see area paths
            if work_items:
                ids = [str(wi['id']) for wi in work_items[:5]]  # Just first 5
                details_url = f"{integrator.project_base_url}/wit/workitems?ids={','.join(ids)}&api-version=7.0"
                
                details_response = requests.get(details_url, auth=integrator.auth)
                if details_response.status_code == 200:
                    details = details_response.json().get('value', [])
                    print("   Sample area paths found:")
                    for item in details[:3]:
                        area_path = item.get('fields', {}).get('System.AreaPath', 'Unknown')
                        print(f"     - Work Item {item['id']}: {area_path}")
                else:
                    print(f"   Failed to get work item details: {details_response.status_code}")
        else:
            print(f"❌ Work Items with Area Path: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Work Items with Area Path: ERROR - {e}")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    print("• Work Items API: Should work (proves PAT is valid)")
    print("• Classification Nodes API: Needs 'Project and team (read)' permission")
    print("• Workaround: Query work items and filter by area path in code")
    print("\nTo fix the 401 error:")
    print("1. Edit your PAT in Azure DevOps")
    print("2. Add 'Project and team (read)' permission")
    print("3. Or use the workaround approach")

if __name__ == "__main__":
    main()
