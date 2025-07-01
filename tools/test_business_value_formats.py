#!/usr/bin/env python3
"""
Test different field values for Epic work items to determine proper formats.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
import requests

def test_epic_creation(integrator, title, fields_to_test):
    """Test creating an Epic with specific field values."""
    
    base_fields = {
        '/fields/System.Title': title,
        '/fields/Microsoft.VSTS.Common.Priority': 2,
        '/fields/Microsoft.VSTS.Common.ValueArea': 'Business',
    }
    
    # Add test fields
    all_fields = {**base_fields, **fields_to_test}
    
    url = f"{integrator.project_base_url}/wit/workitems/$Epic?api-version=7.0"
    
    patch_document = []
    for field_path, value in all_fields.items():
        patch_document.append({
            'op': 'add',
            'path': field_path,
            'value': value
        })
    
    try:
        response = requests.post(
            url,
            json=patch_document,
            auth=integrator.auth,
            headers=integrator.headers
        )
        
        if response.status_code == 200:
            work_item = response.json()
            print(f"✅ SUCCESS: {title}")
            print(f"   ID: {work_item['id']}")
            return True
        else:
            print(f"❌ FAILED: {title}")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {title} - {e}")
        return False

def main():
    print("🔍 Testing Epic field value formats...")
    
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    if not integrator.enabled:
        print("❌ Integration not enabled")
        return
    
    # Test different BusinessValue formats
    tests = [
        {
            'title': 'Test Epic - No BusinessValue',
            'fields': {}
        },
        {
            'title': 'Test Epic - BusinessValue as Integer',
            'fields': {'/fields/Microsoft.VSTS.Common.BusinessValue': 100}
        },
        {
            'title': 'Test Epic - BusinessValue as String Number',
            'fields': {'/fields/Microsoft.VSTS.Common.BusinessValue': "100"}
        },
        {
            'title': 'Test Epic - BusinessValue as Float',
            'fields': {'/fields/Microsoft.VSTS.Common.BusinessValue': 100.0}
        },
        {
            'title': 'Test Epic - BusinessValue as Empty String',
            'fields': {'/fields/Microsoft.VSTS.Common.BusinessValue': ""}
        },
        {
            'title': 'Test Epic - BusinessValue as Short Text',
            'fields': {'/fields/Microsoft.VSTS.Common.BusinessValue': "High"}
        }
    ]
    
    for test in tests:
        print(f"\n📝 Testing: {test['title']}")
        success = test_epic_creation(integrator, test['title'], test['fields'])
        
        if success:
            print("   This format works! ✅")
        else:
            print("   This format failed ❌")

if __name__ == "__main__":
    main()
