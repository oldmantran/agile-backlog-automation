#!/usr/bin/env python3
"""
Simple Azure DevOps connectivity test without area/iteration path creation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.auth import HTTPBasicAuth

def test_ado_connectivity():
    """Test basic Azure DevOps API connectivity."""
    print("🔍 Testing Azure DevOps API Connectivity")
    print("=" * 50)
    
    try:
        # Check environment variables
        ado_org = os.getenv('AZURE_DEVOPS_ORG')
        ado_project = os.getenv('AZURE_DEVOPS_PROJECT') 
        ado_pat = os.getenv('AZURE_DEVOPS_PAT')
        
        print(f"🔗 AZURE_DEVOPS_ORG: {'✅ Set' if ado_org else '❌ Not set'}")
        print(f"📋 AZURE_DEVOPS_PROJECT: {'✅ Set' if ado_project else '❌ Not set'}")
        print(f"🔑 AZURE_DEVOPS_PAT: {'✅ Set' if ado_pat else '❌ Not set'}")
        
        if not all([ado_org, ado_project, ado_pat]):
            print("\n❌ Azure DevOps not fully configured")
            print("💡 Configure .env file with your Azure DevOps settings")
            return False
        
        # Test basic API connectivity with a simple call
        url = f"https://dev.azure.com/{ado_org}/{ado_project}/_apis/projects/{ado_project}?api-version=7.0"
        auth = HTTPBasicAuth('', ado_pat)
        
        print(f"\n🌐 Testing API connectivity to: {ado_org}/{ado_project}")
        response = requests.get(url, auth=auth)
        
        if response.status_code == 200:
            project_info = response.json()
            print(f"✅ API connectivity successful!")
            print(f"   Project: {project_info.get('name')}")
            print(f"   State: {project_info.get('state')}")
            print(f"   Visibility: {project_info.get('visibility')}")
            
            # Test work item API
            wi_url = f"https://dev.azure.com/{ado_org}/{ado_project}/_apis/wit/workitems?api-version=7.0&$top=1"
            wi_response = requests.get(wi_url, auth=auth)
            
            if wi_response.status_code == 200:
                print("✅ Work Items API accessible")
            else:
                print(f"⚠️  Work Items API returned: {wi_response.status_code}")
            
            # Test test management API
            test_url = f"https://dev.azure.com/{ado_org}/{ado_project}/_apis/testplan/plans?api-version=7.0"
            test_response = requests.get(test_url, auth=auth)
            
            if test_response.status_code == 200:
                test_plans = test_response.json()
                print(f"✅ Test Management API accessible - {len(test_plans.get('value', []))} test plans found")
            else:
                print(f"⚠️  Test Management API returned: {test_response.status_code}")
            
            return True
            
        else:
            print(f"❌ API connectivity failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ado_connectivity()
    if success:
        print("\n🎉 Azure DevOps API connectivity is working!")
        print("✅ Basic integration is possible")
        print("💡 Note: Full integration may require proper area/iteration path configuration")
    else:
        print("\n⚠️  Azure DevOps API connectivity failed")
        print("❌ Check your credentials and project settings")
    
    exit(0 if success else 1)
