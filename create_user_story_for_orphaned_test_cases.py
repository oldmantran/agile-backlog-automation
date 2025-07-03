import os
from dotenv import load_dotenv
import base64

# Always load .env from the project root
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=dotenv_path)

import requests
import time

# --- CONFIGURATION ---
AZURE_DEVOPS_ORG = os.environ.get('AZURE_DEVOPS_ORG')
AZURE_DEVOPS_PROJECT = os.environ.get('AZURE_DEVOPS_PROJECT')
AZURE_DEVOPS_PAT = os.environ.get('AZURE_DEVOPS_PAT')
DRY_RUN = True  # Set to False to make changes

API_VERSION = '7.1'
BASE_URL = f'https://dev.azure.com/{AZURE_DEVOPS_ORG}/{AZURE_DEVOPS_PROJECT}/_apis/wit'

# Create authentication header using base64 encoding for PAT
pat_string = f":{AZURE_DEVOPS_PAT}"
auth_bytes = pat_string.encode('ascii')
auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Basic {auth_b64}'
}

def log(msg):
    print(f'[LOG] {msg}')

def get_all_test_cases():
    # Query all test cases in the project
    wiql = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State]
        FROM WorkItems
        WHERE [System.TeamProject] = '{AZURE_DEVOPS_PROJECT}'
        AND [System.WorkItemType] = 'Test Case'
        ORDER BY [System.Id]
        """
    }
    resp = requests.post(f'{BASE_URL}/wiql?api-version={API_VERSION}', headers=HEADERS, json=wiql)
    resp.raise_for_status()
    ids = [item['id'] for item in resp.json().get('workItems', [])]
    return ids

def get_work_item(wi_id):
    resp = requests.get(f'{BASE_URL}/workitems/{wi_id}?$expand=relations&api-version={API_VERSION}', headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def get_parent_id_and_type(wi):
    for rel in wi.get('relations', []):
        if rel.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
            url = rel['url']
            parent_id = int(url.rstrip('/').split('/')[-1])
            # Get parent type
            parent = get_work_item(parent_id)
            parent_type = parent['fields']['System.WorkItemType']
            return parent_id, parent_type
    return None, None

def create_user_story(feature_id, test_case):
    title = f"[Auto] {test_case['fields']['System.Title']}"
    desc = f"Auto-generated User Story to parent Test Case {test_case['id']}: {test_case['fields']['System.Title']}\n\nThis User Story was created automatically because the test case did not fit under any existing User Story."
    data = {
        "fields": {
            "System.Title": title,
            "System.Description": desc,
            "System.WorkItemType": "User Story",
            "System.Parent": feature_id
        },
        "relations": [
            {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"{BASE_URL}/workitems/{feature_id}"
            }
        ]
    }
    patch = [
        {"op": "add", "path": "/fields/System.Title", "value": title},
        {"op": "add", "path": "/fields/System.Description", "value": desc},
        {"op": "add", "path": "/relations/-", "value": {
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"{BASE_URL}/workitems/{feature_id}"
        }}
    ]
    if DRY_RUN:
        log(f"[DRY RUN] Would create User Story under Feature {feature_id} with title: {title}")
        return None
    resp = requests.post(f'{BASE_URL}/workitems/$User%20Story?api-version={API_VERSION}',
                        headers={**HEADERS, 'Content-Type': 'application/json-patch+json'},
                        json=patch)
    resp.raise_for_status()
    us = resp.json()
    log(f"Created User Story {us['id']} for Test Case {test_case['id']}")
    return us['id']

def move_test_case_to_user_story(test_case_id, user_story_id):
    patch = [
        {"op": "add", "path": "/relations/-", "value": {
            "rel": "System.LinkTypes.Hierarchy-Reverse",
            "url": f"{BASE_URL}/workitems/{user_story_id}"
        }}
    ]
    if DRY_RUN:
        log(f"[DRY RUN] Would move Test Case {test_case_id} under User Story {user_story_id}")
        return
    resp = requests.patch(f'{BASE_URL}/workitems/{test_case_id}?api-version={API_VERSION}',
                        headers={**HEADERS, 'Content-Type': 'application/json-patch+json'},
                        json=patch)
    resp.raise_for_status()
    log(f"Moved Test Case {test_case_id} under User Story {user_story_id}")

def main():
    log("Finding all test cases whose parent is a Feature...")
    test_case_ids = get_all_test_cases()
    for tc_id in test_case_ids:
        tc = get_work_item(tc_id)
        parent_id, parent_type = get_parent_id_and_type(tc)
        if parent_type == 'Feature':
            log(f"Test Case {tc_id} is a child of Feature {parent_id}")
            # Create a new User Story under the Feature
            us_id = create_user_story(parent_id, tc)
            if us_id:
                # Move the test case under the new User Story
                move_test_case_to_user_story(tc_id, us_id)
            time.sleep(0.5)  # avoid rate limits
    log("Done.")

if __name__ == '__main__':
    main() 