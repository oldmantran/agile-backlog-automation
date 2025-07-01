#!/usr/bin/env python3
"""
Clean up all work items from the Backlog Automation ADO project
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.auth import HTTPBasicAuth
from config.config_loader import Config

def main():
    print("🧹 Cleaning up ADO Project Work Items...")
    
    # Load config
    config = Config()
    
    org = config.get_env("AZURE_DEVOPS_ORG")
    project = config.get_env("AZURE_DEVOPS_PROJECT")
    pat = config.get_env("AZURE_DEVOPS_PAT")
    
    if org and org.startswith("https://dev.azure.com/"):
        org = org.replace("https://dev.azure.com/", "")
    
    project_base_url = f"https://dev.azure.com/{org}/{project}/_apis"
    auth = HTTPBasicAuth('', pat)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Get all work items in the project
    print(f"\n1. Getting all work items in project '{project}'...")
    
    # Use WIQL (Work Item Query Language) to get all work items
    wiql_query = {
        "query": f"SELECT [System.Id], [System.Title], [System.WorkItemType] FROM WorkItems WHERE [System.TeamProject] = '{project}'"
    }
    
    wiql_url = f"{project_base_url}/wit/wiql?api-version=7.0"
    
    try:
        print(f"📡 Querying work items from: {wiql_url}")
        response = requests.post(wiql_url, json=wiql_query, auth=auth, headers=headers, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        response.raise_for_status()
        
        wiql_result = response.json()
        work_items = wiql_result.get('workItems', [])
        
        print(f"✅ Found {len(work_items)} work items to delete")
        
        if len(work_items) == 0:
            print("🎉 Project is already clean!")
            return
        
        # Get detailed information about work items
        if work_items:
            work_item_ids = [str(wi['id']) for wi in work_items]
            ids_param = ','.join(work_item_ids)
            
            details_url = f"{project_base_url}/wit/workitems?ids={ids_param}&api-version=7.0"
            
            print(f"📡 Getting details from: {details_url}")
            response = requests.get(details_url, auth=auth, headers=headers, timeout=30)
            print(f"📡 Details response status: {response.status_code}")
            response.raise_for_status()
            
            details_result = response.json()
            detailed_items = details_result.get('value', [])
            
            print(f"\n📋 Work items to delete:")
            for item in detailed_items:
                work_item_type = item['fields']['System.WorkItemType']
                title = item['fields']['System.Title']
                work_item_id = item['id']
                print(f"   - {work_item_type} #{work_item_id}: {title}")
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will permanently delete {len(work_items)} work items!")
        confirm = input("Are you sure you want to proceed? (type 'DELETE' to confirm): ")
        
        if confirm != 'DELETE':
            print("❌ Deletion cancelled.")
            return
        
        # Delete work items one by one
        print(f"\n🗑️  Deleting work items...")
        deleted_count = 0
        failed_count = 0
        
        for work_item in work_items:
            work_item_id = work_item['id']
            delete_url = f"{project_base_url}/wit/workitems/{work_item_id}?api-version=7.0"
            
            try:
                print(f"🗑️  Deleting work item #{work_item_id}...")
                response = requests.delete(delete_url, auth=auth, headers=headers, timeout=15)
                if response.status_code == 200:
                    deleted_count += 1
                    print(f"   ✅ Deleted work item #{work_item_id}")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed to delete work item #{work_item_id}: {response.status_code} - {response.text}")
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Exception deleting work item #{work_item_id}: {e}")
        
        print(f"\n🎉 Cleanup completed!")
        print(f"   Deleted: {deleted_count}")
        print(f"   Failed: {failed_count}")
        print(f"   Total: {len(work_items)}")
        
    except Exception as e:
        print(f"❌ Failed to cleanup work items: {e}")

if __name__ == "__main__":
    main()
