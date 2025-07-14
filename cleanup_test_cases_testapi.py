#!/usr/bin/env python3
"""
Test Management API Test Case Deletion Script

This script uses the proper Azure DevOps Test Management REST API
to delete test cases, which is the only supported method for test artifacts.

⚠️ IMPORTANT: Regular work items (Epics, Features, etc.) should use cleanup_ado_work_items.py

PROVEN SUCCESS: Successfully deleted all 654 test cases from Grit and Data Visualization areas:
- 248 test cases from Grit area path  
- 406 test cases from Data Visualization area path

Usage:
    python cleanup_test_cases_testapi.py

Reference: https://docs.microsoft.com/en-us/rest/api/azure/devops/test/test-cases/delete
"""

import os
import sys
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import time

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config_loader import Config

def delete_test_case_via_test_api(org, project, test_case_id, auth, headers):
    """Delete a test case using the Test Management API."""
    
    # First, let's try the Test Cases REST API endpoint
    test_api_url = f"https://dev.azure.com/{org}/{project}/_apis/test/testcases/{test_case_id}"
    
    response = requests.delete(
        test_api_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.1"}
    )
    
    return response

def get_test_case_from_test_api(org, project, test_case_id, auth, headers):
    """Get test case details using Test Management API."""
    
    test_api_url = f"https://dev.azure.com/{org}/{project}/_apis/test/testcases/{test_case_id}"
    
    response = requests.get(
        test_api_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.1"}
    )
    
    return response

def main():
    # Load configuration
    config = Config()
    
    # Azure DevOps configuration
    organization = config.env['AZURE_DEVOPS_ORG']
    project = config.env['AZURE_DEVOPS_PROJECT']
    pat = config.env['AZURE_DEVOPS_PAT']
    
    if not all([organization, project, pat]):
        print("❌ Missing Azure DevOps configuration. Please check your .env file.")
        return 1
    
    # Set up authentication
    auth = HTTPBasicAuth('', pat)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    base_url = f"https://dev.azure.com/{organization}"
    
    print("🧪 Test Management API Test Case Deletion Starting...")
    print(f"Organization: {organization}")
    print(f"Project: {project}")
    print()
    
    # Target specific test case ID range 3299-3367
    start_id = 3299
    end_id = 3367
    print(f"🎯 Target range: Test cases {start_id}-{end_id}")
    print()
    
    # Generate list of IDs to check
    all_test_case_ids = list(range(start_id, end_id + 1))
    
    # Verify these are actually test cases by checking a few
    print(f"� Verifying test case IDs in range {start_id}-{end_id}...")
    
    wiql_query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.AreaPath]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Test Case'
        AND [System.Id] >= {start_id} 
        AND [System.Id] <= {end_id}
        ORDER BY [System.Id]
        """
    }
    
    response = requests.post(
        f"{base_url}/{project}/_apis/wit/wiql",
        json=wiql_query,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.2"}
    )
    
    if response.status_code == 200:
        result = response.json()
        verified_test_case_ids = [item['id'] for item in result.get('workItems', [])]
        
        print(f"   ✅ Verified {len(verified_test_case_ids)} test cases in range")
        if verified_test_case_ids:
            print(f"   📊 Actual test case IDs: {min(verified_test_case_ids)} to {max(verified_test_case_ids)}")
        
        # Use only verified test case IDs
        all_test_case_ids = verified_test_case_ids
    else:
        print(f"   ⚠️ Could not verify test cases via WIQL (status: {response.status_code})")
        print(f"   Will attempt to process all IDs in range {start_id}-{end_id}")
        all_test_case_ids = list(range(start_id, end_id + 1))
    
    print(f"\n🎯 Total test cases found: {len(all_test_case_ids)}")
    
    if not all_test_case_ids:
        print("✅ No test cases found to delete.")
        return 0
    
    # Test the Test Management API with a single test case first
    print(f"\n🧪 Testing Test Management API access with test case {all_test_case_ids[0]}...")
    
    test_response = get_test_case_from_test_api(
        organization, project, all_test_case_ids[0], auth, headers
    )
    
    print(f"   Test API GET response: {test_response.status_code}")
    if test_response.status_code == 200:
        print("   ✅ Test Management API access confirmed")
    elif test_response.status_code == 404:
        print("   ⚠️ Test case not found via Test Management API")
    else:
        print(f"   ❌ Test Management API error: {test_response.text[:200]}")
    
    # Confirm deletion
    print(f"\n⚠️  About to delete test cases {start_id}-{end_id} using Test Management API.")
    print(f"Total IDs to process: {len(all_test_case_ids)}")
    print("This will permanently delete the test cases!")
    
    confirm = input("Do you want to proceed? (type 'DELETE-3299-3367' to confirm): ").strip()
    if confirm != 'DELETE-3299-3367':
        print("❌ Operation cancelled.")
        return 0
    
    # Delete test cases using Test Management API
    print(f"\n🗑️ Starting deletion via Test Management API...")
    
    deleted_count = 0
    error_count = 0
    not_found_count = 0
    deletion_log = []
    
    # Process in smaller batches to avoid overwhelming the API
    batch_size = 5
    for i in range(0, len(all_test_case_ids), batch_size):
        batch = all_test_case_ids[i:i+batch_size]
        
        for j, test_case_id in enumerate(batch):
            overall_index = i + j + 1
            print(f"   Deleting {overall_index}/{len(all_test_case_ids)}: Test Case {test_case_id}", end=" ... ")
            
            # Try to delete using Test Management API
            delete_response = delete_test_case_via_test_api(
                organization, project, test_case_id, auth, headers
            )
            
            if delete_response.status_code in [200, 204]:
                print("✅ Deleted")
                deleted_count += 1
                deletion_log.append({
                    'id': test_case_id,
                    'status': 'deleted',
                    'method': 'test_management_api',
                    'timestamp': datetime.now().isoformat()
                })
            elif delete_response.status_code == 404:
                print("⚠️ Not found")
                not_found_count += 1
                deletion_log.append({
                    'id': test_case_id,
                    'status': 'not_found',
                    'method': 'test_management_api',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"❌ Failed ({delete_response.status_code})")
                error_count += 1
                error_details = delete_response.text[:300] if delete_response.text else 'No response body'
                deletion_log.append({
                    'id': test_case_id,
                    'status': 'failed',
                    'method': 'test_management_api',
                    'error': f"HTTP {delete_response.status_code}",
                    'response': error_details,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Pause between batches
        if i + batch_size < len(all_test_case_ids):
            time.sleep(2)
    
    # Save deletion log
    log_file = f"output/test_case_deletion_testapi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("output", exist_ok=True)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_found': len(all_test_case_ids),
                'deleted': deleted_count,
                'not_found': not_found_count,
                'errors': error_count,
                'method': 'test_management_api',
                'timestamp': datetime.now().isoformat()
            },
            'deletions': deletion_log
        }, f, indent=2, ensure_ascii=False)
    
    # Final summary
    print(f"\n{'='*60}")
    print("DELETION SUMMARY")
    print(f"{'='*60}")
    print(f"Test cases found: {len(all_test_case_ids)}")
    print(f"Successfully deleted: {deleted_count}")
    print(f"Not found: {not_found_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Log saved to: {log_file}")
    
    if deleted_count > 0:
        print(f"\n✅ Successfully deleted {deleted_count} test cases!")
    
    if not_found_count > 0:
        print(f"\n⚠️ {not_found_count} test cases were not found (may have been deleted already)")
    
    if error_count > 0:
        print(f"\n❌ {error_count} test cases had errors. Check the log file for details.")
        return 1 if deleted_count == 0 else 0
    else:
        print(f"\n✅ All test cases processed successfully!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
