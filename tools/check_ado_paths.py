#!/usr/bin/env python3
"""
Check available area and iteration paths in Azure DevOps project.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
import requests

def main():
    print("🔍 Checking Azure DevOps Area and Iteration Paths...")
    
    config = Config()
    
    # Get config values from environment
    org_url = config.env.get('AZURE_DEVOPS_ORG')
    project = config.env.get('AZURE_DEVOPS_PROJECT')
    pat = config.env.get('AZURE_DEVOPS_PAT')
    
    if not all([org_url, project, pat]):
        print("❌ Azure DevOps configuration incomplete")
        print(f"   Organization: {'✅' if org_url else '❌'}")
        print(f"   Project: {'✅' if project else '❌'}")
        print(f"   PAT: {'✅' if pat else '❌'}")
        return
    
    integrator = AzureDevOpsIntegrator(
        organization_url=f"https://dev.azure.com/{org_url}",
        project=project,
        personal_access_token=pat,
        area_path="temp",  # Required but we're just checking paths
        iteration_path="temp"  # Required but we're just checking paths
    )
    
    if not integrator.enabled:
        print("❌ Integration not enabled")
        return
    
    # Check Area Paths
    print("\n🏗️ Area Paths:")
    area_url = f"{integrator.org_base_url}/wit/classificationnodes/Areas?$depth=10&api-version=7.0"
    
    try:
        response = requests.get(area_url, auth=integrator.auth)
        response.raise_for_status()
        
        areas = response.json()
        print(f"Root Area: {areas.get('name', 'Unknown')}")
        
        def print_areas(node, prefix=""):
            if 'children' in node:
                for child in node['children']:
                    path = f"{prefix}\\{child['name']}" if prefix else child['name']
                    print(f"  - {path}")
                    print_areas(child, path)
        
        print_areas(areas, integrator.project)
        
    except Exception as e:
        print(f"❌ Failed to get area paths: {e}")
    
    # Check Iteration Paths
    print("\n📅 Iteration Paths:")
    iteration_url = f"{integrator.org_base_url}/wit/classificationnodes/Iterations?$depth=10&api-version=7.0"
    
    try:
        response = requests.get(iteration_url, auth=integrator.auth)
        response.raise_for_status()
        
        iterations = response.json()
        print(f"Root Iteration: {iterations.get('name', 'Unknown')}")
        
        def print_iterations(node, prefix=""):
            if 'children' in node:
                for child in node['children']:
                    path = f"{prefix}\\{child['name']}" if prefix else child['name']
                    print(f"  - {path}")
                    print_iterations(child, path)
        
        print_iterations(iterations, integrator.project)
        
    except Exception as e:
        print(f"❌ Failed to get iteration paths: {e}")
    
    # Test creating Epic without area/iteration paths
    print("\n📝 Testing Epic creation without custom paths...")
    
    minimal_fields = {
        '/fields/System.Title': 'Test Epic - No Custom Paths',
        '/fields/Microsoft.VSTS.Common.Priority': 2,
        '/fields/Microsoft.VSTS.Common.ValueArea': 'Business',
        '/fields/Microsoft.VSTS.Common.BusinessValue': 100
    }
    
    url = f"{integrator.project_base_url}/wit/workitems/$Epic?api-version=7.0"
    
    patch_document = []
    for field_path, value in minimal_fields.items():
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
            print(f"✅ Epic created successfully without custom paths!")
            print(f"   ID: {work_item['id']}")
            print(f"   Area Path: {work_item['fields'].get('System.AreaPath', 'Not set')}")
            print(f"   Iteration Path: {work_item['fields'].get('System.IterationPath', 'Not set')}")
        else:
            print(f"❌ Epic creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Epic creation error: {e}")

if __name__ == "__main__":
    main()
