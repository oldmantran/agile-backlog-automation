#!/usr/bin/env python3
"""
Diagnose Azure DevOps configuration issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote

def diagnose_ado_config():
    """Diagnose Azure DevOps configuration step by step."""
    print("🔍 Diagnosing Azure DevOps Configuration")
    print("=" * 50)
    
    # Check environment variables
    ado_org = os.getenv('AZURE_DEVOPS_ORG')
    ado_project = os.getenv('AZURE_DEVOPS_PROJECT') 
    ado_pat = os.getenv('AZURE_DEVOPS_PAT')
    
    print(f"🔗 Organization: {ado_org}")
    print(f"📋 Project: {ado_project}")
    print(f"🔑 PAT: {'*' * (len(ado_pat) - 4) + ado_pat[-4:] if ado_pat else 'Not set'}")
    
    if not all([ado_org, ado_project, ado_pat]):
        print("\n❌ Configuration incomplete - check your .env file")
        return False
    
    print("\n" + "=" * 50)
    print("Step 1: Testing Organization Access")
    print("=" * 50)
    
    # Test organization access
    org_url = f"https://dev.azure.com/{ado_org}/_apis/projects?api-version=7.0"
    auth = HTTPBasicAuth('', ado_pat)
    
    try:
        response = requests.get(org_url, auth=auth)
        print(f"Organization API call: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Organization access successful!")
            print(f"   Found {len(projects.get('value', []))} projects")
            
            project_names = [p.get('name') for p in projects.get('value', [])]
            print(f"   Available projects: {', '.join(project_names)}")
            
            if ado_project in project_names:
                print(f"✅ Target project '{ado_project}' found!")
            else:
                print(f"❌ Target project '{ado_project}' not found!")
                print(f"💡 Available projects: {', '.join(project_names)}")
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication failed (401)")
            print("💡 Check if your PAT is valid and not expired")
            print("💡 Ensure PAT has 'Project and Team (read)' permissions")
            return False
        elif response.status_code == 403:
            print("❌ Access forbidden (403)")
            print("💡 PAT may not have sufficient permissions")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing organization: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("Step 2: Testing Project-Specific Access")
    print("=" * 50)
    
    # Test project-specific access
    project_url = f"https://dev.azure.com/{ado_org}/{quote(ado_project)}/_apis/wit/workitems?api-version=7.0&$top=1"
    
    try:
        response = requests.get(project_url, auth=auth)
        print(f"Work Items API call: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Work Items API accessible")
        elif response.status_code == 401:
            print("❌ Authentication failed for work items")
            print("💡 PAT may need 'Work Items (read)' permissions")
        elif response.status_code == 403:
            print("❌ Access forbidden for work items")
            print("💡 PAT may need 'Work Items (read)' permissions")
        else:
            print(f"❌ Work Items API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing work items: {e}")
    
    print("\n" + "=" * 50)
    print("Step 3: Testing Test Management Access")
    print("=" * 50)
    
    # Test test management access
    test_url = f"https://dev.azure.com/{ado_org}/{quote(ado_project)}/_apis/testplan/plans?api-version=7.0"
    
    try:
        response = requests.get(test_url, auth=auth)
        print(f"Test Management API call: {response.status_code}")
        
        if response.status_code == 200:
            test_data = response.json()
            print(f"✅ Test Management API accessible")
            print(f"   Found {len(test_data.get('value', []))} test plans")
        elif response.status_code == 401:
            print("❌ Authentication failed for test management")
            print("💡 PAT may need 'Test Management (read/write)' permissions")
        elif response.status_code == 403:
            print("❌ Access forbidden for test management")
            print("💡 PAT may need 'Test Management (read/write)' permissions")
        else:
            print(f"❌ Test Management API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing test management: {e}")
    
    print("\n" + "=" * 50)
    print("PAT Permission Requirements")
    print("=" * 50)
    print("Your PAT should have these permissions:")
    print("✓ Project and Team (read)")
    print("✓ Work Items (read/write)")
    print("✓ Test Management (read/write)")
    print("\nTo check/update PAT permissions:")
    print(f"1. Go to: https://dev.azure.com/{ado_org}/_usersSettings/tokens")
    print("2. Find your PAT and click 'Edit'")
    print("3. Ensure the above permissions are selected")
    
    return True

if __name__ == "__main__":
    diagnose_ado_config()
