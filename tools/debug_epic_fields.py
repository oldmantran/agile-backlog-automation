#!/usr/bin/env python3
"""
Debug Epic work item fields to see what's available
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.auth import HTTPBasicAuth
from config.config_loader import Config

def main():
    print("🔍 Debugging Epic Work Item Fields...")
    
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
        'Accept': 'application/json'
    }
    
    # Get Epic work item type definition with fields
    print(f"\n1. Getting Epic work item type definition...")
    wit_url = f"{project_base_url}/wit/workitemtypes/Epic?api-version=7.0"
    
    try:
        response = requests.get(wit_url, auth=auth, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Epic work item type found")
        print(f"Name: {data.get('name')}")
        print(f"Reference Name: {data.get('referenceName')}")
        
        # Show available fields
        fields = data.get('fields', [])
        print(f"\n📋 Available fields ({len(fields)}):")
        
        for field in fields:
            field_name = field.get('referenceName', 'Unknown')
            field_type = field.get('type', 'Unknown')
            is_required = field.get('alwaysRequired', False)
            
            # Show business value related fields
            if 'business' in field_name.lower() or 'value' in field_name.lower():
                print(f"  🔸 {field_name} (Type: {field_type}, Required: {is_required})")
            # Show other commonly used fields
            elif any(key in field_name.lower() for key in ['title', 'description', 'priority', 'state', 'reason']):
                print(f"  - {field_name} (Type: {field_type}, Required: {is_required})")
                
    except Exception as e:
        print(f"❌ Failed to get Epic work item type: {e}")
        return
        
    # Test a minimal Epic creation
    print(f"\n2. Testing minimal Epic creation...")
    
    create_url = f"{project_base_url}/wit/workitems/$Epic?api-version=7.0"
    
    # Try with just the required fields
    minimal_data = [{
        'op': 'add',
        'path': '/fields/System.Title',
        'value': 'Minimal Test Epic'
    }]
    
    headers_create = {
        'Accept': 'application/json',
        'Content-Type': 'application/json-patch+json'
    }
    
    try:
        response = requests.post(create_url, json=minimal_data, auth=auth, headers=headers_create)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            work_item = response.json()
            print(f"✅ Minimal Epic created successfully!")
            print(f"   ID: {work_item.get('id')}")
            print(f"   Title: {work_item['fields']['System.Title']}")
            print(f"   State: {work_item['fields']['System.State']}")
            
            # Show all fields in the created work item
            print(f"\n📋 Fields in created Epic:")
            for field_name, field_value in work_item['fields'].items():
                if isinstance(field_value, str) and len(str(field_value)) > 50:
                    field_value = str(field_value)[:50] + "..."
                print(f"   - {field_name}: {field_value}")
                
        else:
            print(f"❌ Failed to create Epic: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during Epic creation: {e}")

if __name__ == "__main__":
    main()
