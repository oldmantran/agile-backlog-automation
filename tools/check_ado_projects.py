#!/usr/bin/env python3
"""
Check what projects exist in the Azure DevOps organization.
"""

import os
import sys
import requests
from requests.auth import HTTPBasicAuth

# Add parent directory to path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config_loader import Config


def check_projects():
    """Check what projects exist in the ADO organization."""
    
    # Load configuration
    config = Config()
    
    organization = config.get_env("AZURE_DEVOPS_ORG")
    pat = config.get_env("AZURE_DEVOPS_PAT")
    
    # Handle both full URL and organization name formats
    if organization and organization.startswith("https://dev.azure.com/"):
        organization = organization.replace("https://dev.azure.com/", "")
    
    if not all([organization, pat]):
        print("ERROR: Azure DevOps credentials not configured")
        return False
    
    print(f"Checking projects in organization: {organization}")
    
    # Test connection to organization (list projects)
    url = f"https://dev.azure.com/{organization}/_apis/projects?api-version=7.0"
    auth = HTTPBasicAuth('', pat)
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        projects_data = response.json()
        projects = projects_data.get('value', [])
        
        print(f"\nFound {len(projects)} projects in organization '{organization}':")
        
        if projects:
            for project in projects:
                print(f"  - {project['name']} (ID: {project['id']})")
        else:
            print("  No projects found.")
        
        # Check if our target project exists
        target_project = config.get_env("AZURE_DEVOPS_PROJECT")
        project_exists = any(p['name'] == target_project for p in projects)
        
        print(f"\nTarget project '{target_project}' exists: {project_exists}")
        
        if not project_exists:
            print(f"\nThis explains the 401 error! The project '{target_project}' doesn't exist.")
            print("You need to either:")
            print(f"  1. Create a project named '{target_project}' in Azure DevOps")
            print("  2. Update your .env file to use an existing project name")
        
        return project_exists
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to Azure DevOps: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return False


if __name__ == "__main__":
    check_projects()
