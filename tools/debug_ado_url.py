#!/usr/bin/env python3
"""
Debug script to check Azure DevOps URL construction and authentication
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import base64

def main():
    # Load environment variables
    load_dotenv()
    
    org = os.getenv("AZURE_DEVOPS_ORG")
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    pat = os.getenv("AZURE_DEVOPS_PAT")
    
    print(f"🔧 Debug ADO Configuration")
    print(f"Organization: {org}")
    print(f"Project: {project}")
    print(f"PAT exists: {'Yes' if pat else 'No'}")
    print(f"PAT length: {len(pat) if pat else 0}")
    
    # Handle URL format
    if org and org.startswith("https://dev.azure.com/"):
        org = org.replace("https://dev.azure.com/", "")
        print(f"Cleaned org: {org}")
    
    # Test different URL patterns
    urls_to_test = [
        f"https://dev.azure.com/{org}/_apis/projects?api-version=7.0",  # Organization level
        f"https://dev.azure.com/{org}/{project}/_apis/projects?api-version=7.0",  # Project level (incorrect)
        f"https://dev.azure.com/{org}/_apis/projects/{project}?api-version=7.0",  # Specific project
    ]
    
    auth = HTTPBasicAuth('', pat)
    headers = {
        'Accept': 'application/json'
    }
    
    print(f"\n🌐 Testing URLs...")
    
    for i, url in enumerate(urls_to_test, 1):
        print(f"\n{i}. Testing: {url}")
        try:
            response = requests.get(url, auth=auth, headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if 'value' in data:
                    print(f"   Projects found: {len(data['value'])}")
                    for project_info in data['value']:
                        print(f"     - {project_info.get('name', 'Unknown')}")
                elif 'name' in data:
                    print(f"   Project: {data['name']}")
                else:
                    print(f"   Response keys: {list(data.keys())}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
    
    # Test basic auth format
    print(f"\n🔐 Testing authentication format...")
    if pat:
        # Test the base64 encoding that Azure DevOps expects
        credentials = base64.b64encode(f":{pat}".encode()).decode()
        headers_with_auth = {
            'Authorization': f'Basic {credentials}',
            'Accept': 'application/json'
        }
        
        url = f"https://dev.azure.com/{org}/_apis/projects?api-version=7.0"
        print(f"Testing with explicit Basic auth header: {url}")
        try:
            response = requests.get(url, headers=headers_with_auth)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Projects found: {len(data.get('value', []))}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    main()
