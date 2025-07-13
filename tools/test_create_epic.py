import requests
from requests.auth import HTTPBasicAuth
import os
import urllib.parse

org = os.getenv("AZURE_DEVOPS_ORG", "c4workx")
project = os.getenv("AZURE_DEVOPS_PROJECT", "Backlog Automation")
pat = os.getenv("AZURE_DEVOPS_PAT", "qMUS1Z1ZD20Y1boUpAOvznZwo5aAwgjeJsImMtZeTVomJCCZx6fgJQQJ99BGACAAAAAlpST6AAASAZDO1jgn")

# URL-encode the project name
project_encoded = urllib.parse.quote(project)

# Try both Epic and $Epic
for epic_type in ["Epic", "$Epic"]:
    url = f"https://dev.azure.com/{org}/{project_encoded}/_apis/wit/workitems/{epic_type}?api-version=7.0"
    headers = {
        "Content-Type": "application/json-patch+json"
    }
    data = [
        {"op": "add", "path": "/fields/System.Title", "value": f"Test Epic from API ({epic_type})"}
    ]
    print(f"\nTesting Epic creation with type: {epic_type}")
    print("URL:", url)
    response = requests.post(
        url,
        json=data,
        auth=HTTPBasicAuth('', pat),
        headers=headers
    )
    print("Status:", response.status_code)
    print("Response:", response.text)
