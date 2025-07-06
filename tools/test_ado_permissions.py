#!/usr/bin/env python3
"""
Test different Azure DevOps API permissions to debug 401 errors.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
import requests

def test_api_endpoints():
    print("🔍 Testing various Azure DevOps API endpoints...")
    
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    if not integrator.enabled:
        print("❌ Integration not enabled")
        return
    
    # Test different API endpoints to see which permissions work
    tests = [
        {
            "name": "Work Items Query (WIQL)",
            "url": f"{integrator.project_base_url}/wit/wiql?api-version=7.0",
            "method": "POST",
            "data": {
                "query": "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Epic'"
            }
        },
        {
            "name": "Work Item Details (by ID)",
            "url": f"{integrator.project_base_url}/wit/workitems/1707?api-version=7.0",
            "method": "GET"
        },
        {
            "name": "Classification Nodes - Areas",
            "url": f"{integrator.org_base_url}/wit/classificationnodes/Areas?$depth=1&api-version=7.0",
            "method": "GET"
        },
        {
            "name": "Classification Nodes - Iterations", 
            "url": f"{integrator.org_base_url}/wit/classificationnodes/Iterations?$depth=1&api-version=7.0",
            "method": "GET"
        },
        {
            "name": "Project Areas (different endpoint)",
            "url": f"{integrator.project_base_url}/wit/classificationnodes/Areas?$depth=1&api-version=7.0",
            "method": "GET"
        },
        {
            "name": "Project Iterations (different endpoint)",
            "url": f"{integrator.project_base_url}/wit/classificationnodes/Iterations?$depth=1&api-version=7.0", 
            "method": "GET"
        },
        {
            "name": "Teams List",
            "url": f"{integrator.project_base_url}/teams?api-version=7.0",
            "method": "GET"
        },
        {
            "name": "Project Properties",
            "url": f"{integrator.org_base_url}/projects/{integrator.project}?api-version=7.0",
            "method": "GET"
        }
    ]
    
    for test in tests:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            if test['method'] == 'GET':
                response = requests.get(test['url'], auth=integrator.auth)
            elif test['method'] == 'POST':
                response = requests.post(
                    test['url'], 
                    json=test.get('data', {}),
                    auth=integrator.auth,
                    headers=integrator.headers
                )
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS ({response.status_code})")
                # Show some data if it's a small response
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if 'count' in data:
                            print(f"      Count: {data['count']}")
                        if 'value' in data and isinstance(data['value'], list):
                            print(f"      Items: {len(data['value'])}")
                        if 'name' in data:
                            print(f"      Name: {data['name']}")
                except:
                    pass
            else:
                print(f"   ❌ FAILED ({response.status_code})")
                if response.status_code == 401:
                    print(f"      UNAUTHORIZED - Missing permissions")
                elif response.status_code == 403:
                    print(f"      FORBIDDEN - Insufficient permissions")
                else:
                    print(f"      Error: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def test_work_item_query_without_area_filter():
    """Test if we can query work items without area path filtering as a workaround."""
    print(f"\n" + "="*60)
    print("TESTING WORKAROUND: Query work items without area filtering")
    print("="*60)
    
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    # Test WIQL query for all User Stories
    wiql_query = {
        "query": """
        SELECT [System.Id], [System.Title], [System.AreaPath], [System.WorkItemType]
        FROM WorkItems 
        WHERE [System.WorkItemType] = 'User Story'
        AND [System.State] <> 'Removed'
        ORDER BY [System.Id]
        """
    }
    
    try:
        url = f"{integrator.project_base_url}/wit/wiql?api-version=7.0"
        response = requests.post(
            url,
            json=wiql_query,
            auth=integrator.auth,
            headers=integrator.headers
        )
        
        if response.status_code == 200:
            result = response.json()
            work_items = result.get('workItems', [])
            print(f"✅ Found {len(work_items)} User Stories")
            
            if work_items:
                # Get details for first few work items
                ids = [str(wi['id']) for wi in work_items[:5]]
                details_url = f"{integrator.project_base_url}/wit/workitems?ids={','.join(ids)}&api-version=7.0"
                
                details_response = requests.get(details_url, auth=integrator.auth)
                if details_response.status_code == 200:
                    details = details_response.json()
                    print(f"✅ Retrieved details for {len(details.get('value', []))} work items")
                    
                    # Show area paths we can access
                    area_paths = set()
                    for wi in details.get('value', []):
                        area_path = wi.get('fields', {}).get('System.AreaPath', '')
                        if area_path:
                            area_paths.add(area_path)
                    
                    print(f"\n📍 Area paths found in work items:")
                    for area in sorted(area_paths):
                        print(f"   - {area}")
                        if "Data Visualization" in area:
                            print(f"     ⭐ This matches our target area!")
                else:
                    print(f"❌ Failed to get work item details: {details_response.status_code}")
        else:
            print(f"❌ WIQL query failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Query test failed: {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_work_item_query_without_area_filter()
