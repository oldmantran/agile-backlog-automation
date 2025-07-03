import os
from dotenv import load_dotenv
import base64
import requests
import time

# Always load .env from the project root
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=dotenv_path)

def log(msg):
    print(f'[LOG] {msg}')

def log_error(msg):
    print(f'[ERROR] {msg}')

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

def get_all_test_cases():
    log('Querying all test cases in the project...')
    wiql = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State]
        FROM WorkItems
        WHERE [System.TeamProject] = '{AZURE_DEVOPS_PROJECT}'
        AND [System.WorkItemType] = 'Test Case'
        ORDER BY [System.Id]
        """
    }
    try:
        resp = requests.post(f'{BASE_URL}/wiql?api-version={API_VERSION}', headers=HEADERS, json=wiql)
        log(f'WIQL query sent. Status code: {resp.status_code}')
        resp.raise_for_status()
        ids = [item['id'] for item in resp.json().get('workItems', [])]
        log(f'Found {len(ids)} test cases.')
        return ids
    except Exception as e:
        log_error(f'Failed to query test cases: {e}')
        raise

def get_work_item(wi_id):
    log(f'Fetching work item {wi_id}...')
    try:
        resp = requests.get(f'{BASE_URL}/workitems/{wi_id}?$expand=relations&api-version={API_VERSION}', headers=HEADERS)
        log(f'GET work item {wi_id} status: {resp.status_code}')
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log_error(f'Failed to fetch work item {wi_id}: {e}')
        raise

def get_parent_id_and_type(wi):
    for rel in wi.get('relations', []):
        if rel.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
            url = rel['url']
            parent_id = int(url.rstrip('/').split('/')[-1])
            try:
                parent = get_work_item(parent_id)
                parent_type = parent['fields']['System.WorkItemType']
                log(f'Work item {wi["id"]} parent is {parent_id} ({parent_type})')
                return parent_id, parent_type
            except Exception as e:
                log_error(f'Failed to get parent for work item {wi["id"]}: {e}')
                return None, None
    log(f'No parent found for work item {wi["id"]}')
    return None, None

def create_user_story(feature_id, test_case):
    title = f"[Auto] {test_case['fields']['System.Title']}"
    desc = f"Auto-generated User Story to parent Test Case {test_case['id']}: {test_case['fields']['System.Title']}\n\nThis User Story was created automatically because the test case did not fit under any existing User Story."
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
    try:
        resp = requests.post(f'{BASE_URL}/workitems/$User%20Story?api-version={API_VERSION}',
                            headers={**HEADERS, 'Content-Type': 'application/json-patch+json'},
                            json=patch)
        log(f'Create User Story response status: {resp.status_code}')
        resp.raise_for_status()
        us = resp.json()
        log(f"Created User Story {us['id']} for Test Case {test_case['id']}")
        return us['id']
    except Exception as e:
        log_error(f'Failed to create User Story for Feature {feature_id}: {e}')
        return None

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
    try:
        resp = requests.patch(f'{BASE_URL}/workitems/{test_case_id}?api-version={API_VERSION}',
                            headers={**HEADERS, 'Content-Type': 'application/json-patch+json'},
                            json=patch)
        log(f'Move Test Case response status: {resp.status_code}')
        resp.raise_for_status()
        log(f"Moved Test Case {test_case_id} under User Story {user_story_id}")
    except Exception as e:
        log_error(f'Failed to move Test Case {test_case_id} to User Story {user_story_id}: {e}')

def main():
    log("Finding all test cases whose parent is a Feature...")
    try:
        test_case_ids = get_all_test_cases()
    except Exception as e:
        log_error(f'Aborting: Could not get test cases: {e}')
        return
    total = 0
    parented_by_user_story = 0
    parented_by_feature = 0
    for tc_id in test_case_ids:
        total += 1
        try:
            tc = get_work_item(tc_id)
            parent_id, parent_type = get_parent_id_and_type(tc)
            if parent_type == 'Feature':
                parented_by_feature += 1
                log(f"Test Case {tc_id} is a child of Feature {parent_id}")
                # Create a new User Story under the Feature
                us_id = create_user_story(parent_id, tc)
                if us_id:
                    # Move the test case under the new User Story
                    move_test_case_to_user_story(tc_id, us_id)
                time.sleep(0.5)  # avoid rate limits
            elif parent_type == 'User Story':
                parented_by_user_story += 1
        except Exception as e:
            log_error(f'Error processing Test Case {tc_id}: {e}')
    log(f"SUMMARY: Total test cases: {total}")
    log(f"SUMMARY: Test cases parented by User Stories: {parented_by_user_story}")
    log(f"SUMMARY: Test cases parented by Features: {parented_by_feature}")
    log("Done.")

if __name__ == '__main__':
    main() 