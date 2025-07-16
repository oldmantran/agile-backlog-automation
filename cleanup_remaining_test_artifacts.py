#!/usr/bin/env python3
"""
Targeted Test Artifact Cleanup Script

This script removes specific remaining test artifacts by ID.
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

# Specific remaining test artifact IDs to clean up
# Format: [(suite_id, plan_id), (suite_id, plan_id), ...] for test suites
# Format: [plan_id, plan_id, ...] for test plans
REMAINING_TEST_ARTIFACTS = [
    3312, 3317, 3331, 3332, 3337, 3350, 3351, 3356, 3529, 3530, 
    3535, 3548, 3549, 3554, 3567, 3568, 3573, 3586, 3587, 3592, 
    3605, 3606, 3611, 3624, 3625, 3630, 3643, 3644, 3649, 3663
]

# TODO: Replace with plan ID and suite ID pairs from ADO Copilot
# Format: [(suite_id, plan_id), (suite_id, plan_id), ...]
TEST_SUITE_PLAN_PAIRS = [
    # Will be populated with (suite_id, plan_id) tuples
]

def get_work_item_details(org, project, work_item_id, auth, headers):
    """Get work item details."""
    response = requests.get(
        f"https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{work_item_id}",
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
    )
    
    if response.status_code == 200:
        return response.json()
    return None

def delete_test_plan(org, project, plan_id, auth, headers):
    """Delete a test plan using the Test Management API."""
    plan_url = f"https://dev.azure.com/{org}/{project}/_apis/testplan/Plans/{plan_id}"
    
    response = requests.delete(
        plan_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
    )
    
    return response

def get_all_test_plans(org, project, auth, headers):
    """Get all test plans in the project."""
    plans_url = f"https://dev.azure.com/{org}/{project}/_apis/testplan/Plans"
    
    response = requests.get(
        plans_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
    )
    
    if response.status_code == 200:
        return response.json().get('value', [])
    return []

def get_test_suites_for_plan(org, project, plan_id, auth, headers):
    """Get all test suites for a specific test plan."""
    suites_url = f"https://dev.azure.com/{org}/{project}/_apis/testplan/Plans/{plan_id}/suites"
    
    response = requests.get(
        suites_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
    )
    
    if response.status_code == 200:
        return response.json().get('value', [])
    return []

def build_suite_plan_mapping(org, project, target_suite_ids, auth, headers):
    """Build a mapping of suite IDs to their parent plan IDs."""
    suite_to_plan = {}
    
    # Get all test plans
    plans = get_all_test_plans(org, project, auth, headers)
    
    print(f"   🔍 Found {len(plans)} test plans to search...")
    
    for plan in plans:
        plan_id = plan['id']
        plan_name = plan.get('name', f'Plan {plan_id}')
        
        # Get all suites for this plan
        suites = get_test_suites_for_plan(org, project, plan_id, auth, headers)
        
        for suite in suites:
            suite_id = suite['id']
            if suite_id in target_suite_ids:
                suite_to_plan[suite_id] = plan_id
                print(f"      ✅ Found Suite {suite_id} in Plan {plan_id} ({plan_name})")
    
    return suite_to_plan

def delete_test_suite_with_plan(org, project, suite_id, plan_id, auth, headers):
    """Delete a test suite when we know both the suite ID and plan ID."""
    suite_url = f"https://dev.azure.com/{org}/{project}/_apis/testplan/Plans/{plan_id}/suites/{suite_id}"
    
    response = requests.delete(
        suite_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
    )
    
    return response

def delete_test_suite(org, project, suite_id, auth, headers):
    """Delete a test suite. We need to find the plan it belongs to first."""
    
    # Get all test plans to find which one contains this suite
    plans_url = f"https://dev.azure.com/{org}/{project}/_apis/testplan/Plans"
    
    plans_response = requests.get(
        plans_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
    )
    
    if plans_response.status_code == 200:
        plans = plans_response.json().get('value', [])
        
        # Check each plan for this suite
        for plan in plans:
            plan_id = plan['id']
            
            # Get suites for this plan
            suites_url = f"https://dev.azure.com/{org}/{project}/_apis/testplan/Plans/{plan_id}/suites"
            
            suites_response = requests.get(
                suites_url,
                auth=auth,
                headers=headers,
                params={"api-version": "7.1-preview.3"}
            )
            
            if suites_response.status_code == 200:
                suites = suites_response.json().get('value', [])
                
                # Check if our suite is in this plan
                for suite in suites:
                    if suite['id'] == suite_id:
                        # Found the suite, now delete it using the correct API
                        return delete_test_suite_with_plan(org, project, suite_id, plan_id, auth, headers)
    
    # If we can't find the plan, return a 404-like response
    from requests import Response
    response = Response()
    response.status_code = 404
    response._content = b'{"message": "Suite not found in any test plan"}'
    return response

def delete_work_item(org, project, work_item_id, auth, headers):
    """Delete a work item using the Work Item Tracking API (ADO Copilot recommended approach)."""
    work_item_url = f"https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{work_item_id}"
    
    response = requests.delete(
        work_item_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
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
    
    print("🧪 Targeted Test Artifact Cleanup Starting...")
    print(f"Organization: {organization}")
    print(f"Project: {project}")
    print(f"Items to Clean: {len(REMAINING_TEST_ARTIFACTS)}")
    print(f"Suite-Plan Pairs: {len(TEST_SUITE_PLAN_PAIRS)}")
    print()
    
    # First, let's analyze what we have and build suite-to-plan mapping
    print("🔍 Analyzing remaining test artifacts...")
    test_plans = []
    test_suites = []
    unknown_items = []
    
    for item_id in REMAINING_TEST_ARTIFACTS:
        item_details = get_work_item_details(organization, project, item_id, auth, headers)
        if item_details:
            work_item_type = item_details['fields']['System.WorkItemType']
            title = item_details['fields']['System.Title']
            area_path = item_details['fields']['System.AreaPath']
            state = item_details['fields']['System.State']
            
            if work_item_type == 'Test Plan':
                test_plans.append((item_id, title, area_path, state))
            elif work_item_type == 'Test Suite':
                test_suites.append((item_id, title, area_path, state))
            else:
                unknown_items.append((item_id, work_item_type, title, area_path, state))
        else:
            print(f"   ❌ Could not find item {item_id}")
    
    print(f"   📋 Found {len(test_plans)} test plans")
    print(f"   📁 Found {len(test_suites)} test suites")
    print(f"   ❓ Found {len(unknown_items)} unknown items")
    
    # Build suite-to-plan mapping for test suites
    suite_to_plan_mapping = {}
    if test_suites:
        print(f"\n🔍 Building suite-to-plan mapping for {len(test_suites)} test suites...")
        suite_ids = [suite_id for suite_id, _, _, _ in test_suites]
        suite_to_plan_mapping = build_suite_plan_mapping(organization, project, suite_ids, auth, headers)
        
        unmapped_suites = [suite_id for suite_id in suite_ids if suite_id not in suite_to_plan_mapping]
        if unmapped_suites:
            print(f"   ⚠️  Could not find parent plans for {len(unmapped_suites)} suites: {unmapped_suites}")
    
    if test_plans:
        print("   📋 Test Plans:")
        for item_id, title, area_path, state in test_plans:
            print(f"      - {item_id}: {title} ({state}) - {area_path}")
    
    if test_suites:
        print("   📁 Test Suites:")
        for item_id, title, area_path, state in test_suites:
            parent_plan = suite_to_plan_mapping.get(item_id, "Unknown")
            print(f"      - {item_id}: {title} ({state}) - {area_path} [Plan: {parent_plan}]")
    
    if unknown_items:
        print("   ❓ Unknown Items:")
        for item_id, work_item_type, title, area_path, state in unknown_items:
            print(f"      - {item_id}: {work_item_type} - {title} ({state}) - {area_path}")
    
    total_items = len(test_plans) + len(test_suites) + len(unknown_items)
    if total_items == 0:
        print("✅ No test artifacts found to delete.")
        return 0
    
    print(f"\n⚠️  About to delete {total_items} remaining test artifacts!")
    print("This will permanently delete the items listed above.")
    print("⚠️  This action cannot be undone!")
    
    confirm = input("Type 'DELETE-REMAINING-ARTIFACTS' to confirm: ").strip()
    if confirm != 'DELETE-REMAINING-ARTIFACTS':
        print("❌ Operation cancelled.")
        return 0
    
    print(f"\n🗑️ Starting targeted test artifact deletion...")
    print("� Using Work Item Tracking API to delete all items (recommended by ADO Copilot)")
    
    deleted_count = 0
    error_count = 0
    
    # Delete ALL items using Work Item Tracking API (test suites, test plans, and unknown items)
    all_items = test_suites + test_plans + unknown_items
    
    print(f"\n�️ Deleting {len(all_items)} items using Work Item Tracking API...")
    for item_id, title, area_path, state in all_items:
        # Determine item type from the lists
        item_type = "Test Suite" if (item_id, title, area_path, state) in test_suites else \
                   "Test Plan" if (item_id, title, area_path, state) in test_plans else \
                   "Unknown Item"
        
        print(f"   Deleting {item_type} {item_id}: {title}", end=" ... ")
        
        response = delete_work_item(organization, project, item_id, auth, headers)
        
        if response.status_code in [200, 204]:
            print("✅")
            deleted_count += 1
        else:
            print(f"❌ ({response.status_code})")
            error_count += 1
            try:
                error_details = response.json()
                if 'message' in error_details:
                    print(f"      Error: {error_details['message']}")
            except:
                pass
        
        time.sleep(0.5)  # Rate limiting
    
    # Save log
    cleanup_log = {
        'summary': {
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'total_items_processed': total_items,
            'deleted_count': deleted_count,
            'error_count': error_count,
            'target_items': REMAINING_TEST_ARTIFACTS
        },
        'results': {
            'test_plans': test_plans,
            'test_suites': test_suites,
            'unknown_items': unknown_items
        }
    }
    
    log_file = f"output/targeted_test_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("output", exist_ok=True)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(cleanup_log, f, indent=2, ensure_ascii=False)
    
    # Final summary
    print(f"\n{'='*60}")
    print("TARGETED CLEANUP SUMMARY")
    print(f"{'='*60}")
    print(f"Total Items Processed: {total_items}")
    print(f"Successfully Deleted: {deleted_count}")
    print(f"Errors: {error_count}")
    print(f"Log saved to: {log_file}")
    
    if deleted_count > 0:
        print(f"\n✅ Successfully deleted {deleted_count} remaining test artifacts!")
    
    if error_count > 0:
        print(f"\n❌ {error_count} items had errors. Check the log file for details.")
        return 1 if deleted_count == 0 else 0
    else:
        print(f"\n✅ All remaining test artifacts processed successfully!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
