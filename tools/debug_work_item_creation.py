#!/usr/bin/env python3
"""
Debug work item types and creation in Azure DevOps
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.auth import HTTPBasicAuth
import urllib.parse
from config.config_loader import Config

def main():
    print("🔍 Debugging Azure DevOps Work Item Types...")
    
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
        'Content-Type': 'application/json-patch+json'
    }
    
    # 1. Check available work item types
    print(f"\n1. Checking work item types...")
    wit_url = f"{project_base_url}/wit/workitemtypes?api-version=7.0"
    
    try:
        response = requests.get(wit_url, auth=auth, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        work_item_types = data.get('value', [])
        print(f"✅ Found {len(work_item_types)} work item types:")
        
        for wit in work_item_types:
            print(f"  - {wit.get('name', 'Unknown')} (Reference: {wit.get('referenceName', 'Unknown')})")
            
    except Exception as e:
        print(f"❌ Failed to get work item types: {e}")
        return
    
    # 2. Test creating an Epic with proper URL
    print(f"\n2. Testing Epic creation...")
    
    # Try different URL formats
    test_urls = [
        f"{project_base_url}/wit/workitems/$Epic?api-version=7.0",
        f"{project_base_url}/wit/workitems/%24Epic?api-version=7.0",  # URL encoded $
        f"https://dev.azure.com/{org}/{urllib.parse.quote(project)}/_apis/wit/workitems/$Epic?api-version=7.0"
    ]
    
    test_data = [{
        'op': 'add',
        'path': '/fields/System.Title',
        'value': 'Test Epic - Debug'
    }]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n  Testing URL {i}: {url}")
        try:
            response = requests.post(url, json=test_data, auth=auth, headers=headers)
            print(f"    Status: {response.status_code}")
            if response.status_code >= 400:
                print(f"    Error: {response.text}")
            else:
                print(f"    ✅ Success!")
                work_item = response.json()
                print(f"    Created work item ID: {work_item.get('id')}")
                break
        except Exception as e:
            print(f"    Exception: {e}")

if __name__ == "__main__":
    main()
