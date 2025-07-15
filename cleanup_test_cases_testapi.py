#!/usr/bin/env python3
"""
Comprehensive Test Management Deletion Script

This script performs complete deletion of all test-related artifacts in Azure DevOps:
- Test Plans
- Test Suites  
- Test Cases
- Shared Steps (if any)

The script is designed to completely clean a project's test artifacts within a specific area path.

⚠️ IMPORTANT: This performs COMPLETE deletion of all test artifacts in the specified area path.

Usage:
    python cleanup_test_cases_testapi.py

Reference: https://docs.microsoft.com/en-us/rest/api/azure/devops/test/
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

def get_test_plans_by_area_path(org, project, area_path, auth, headers):
    """Get all test plans that belong to a specific area path."""
    
    # Get all test plans
    plans_url = f"https://dev.azure.com/{org}/{project}/_apis/test/plans"
    
    response = requests.get(
        plans_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.3"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get test plans: {response.status_code}")
        return []
    
    all_plans = response.json().get('value', [])
    
    # Filter plans by area path
    filtered_plans = []
    for plan in all_plans:
        if plan.get('areaPath', '').startswith(area_path):
            filtered_plans.append(plan)
    
    return filtered_plans

def get_test_suites_for_plan(org, project, plan_id, auth, headers):
    """Get all test suites for a specific test plan."""
    
    suites_url = f"https://dev.azure.com/{org}/{project}/_apis/test/Plans/{plan_id}/suites"
    
    response = requests.get(
        suites_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.1"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get test suites for plan {plan_id}: {response.status_code}")
        return []
    
    return response.json().get('value', [])

def get_test_cases_by_area_path(org, project, area_path, auth, headers):
    """Get all test cases that belong to a specific area path using WIQL."""
    
    wiql_query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.AreaPath]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Test Case'
        AND [System.AreaPath] UNDER '{area_path}'
        ORDER BY [System.Id]
        """
    }
    
    response = requests.post(
        f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql",
        json=wiql_query,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.2"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to query test cases: {response.status_code}")
        return []
    
    result = response.json()
    return [item['id'] for item in result.get('workItems', [])]

def get_shared_steps_by_area_path(org, project, area_path, auth, headers):
    """Get all shared steps that belong to a specific area path using WIQL."""
    
    wiql_query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.AreaPath]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Shared Steps'
        AND [System.AreaPath] UNDER '{area_path}'
        ORDER BY [System.Id]
        """
    }
    
    response = requests.post(
        f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql",
        json=wiql_query,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.2"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to query shared steps: {response.status_code}")
        return []
    
    result = response.json()
    return [item['id'] for item in result.get('workItems', [])]

def delete_test_case_via_test_api(org, project, test_case_id, auth, headers):
    """Delete a test case using the Test Management API."""
    
    test_api_url = f"https://dev.azure.com/{org}/{project}/_apis/test/testcases/{test_case_id}"
    
    response = requests.delete(
        test_api_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.1"}
    )
    
    return response

def delete_test_suite(org, project, plan_id, suite_id, auth, headers):
    """Delete a test suite using the Test Management API."""
    
    suite_url = f"https://dev.azure.com/{org}/{project}/_apis/test/Plans/{plan_id}/suites/{suite_id}"
    
    response = requests.delete(
        suite_url,
        auth=auth,
        headers=headers,
        params={"api-version": "7.1-preview.1"}
    )
    
    return response

def delete_test_plan(org, project, plan_id, auth, headers):
    """Delete a test plan using the Test Management API."""
    
    plan_url = f"https://dev.azure.com/{org}/{project}/_apis/test/plans/{plan_id}"
    
    response = requests.delete(
        plan_url,
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
    
    # Get area path from config or use default
    area_path = config.env.get('AZURE_DEVOPS_AREA_PATH', 'Backlog Automation')
    
    if not all([organization, project, pat]):
        print("❌ Missing Azure DevOps configuration. Please check your .env file.")
        return 1
    
    # Set up authentication
    auth = HTTPBasicAuth('', pat)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print("🧪 Complete Test Management Deletion Starting...")
    print(f"Organization: {organization}")
    print(f"Project: {project}")
    print(f"Area Path: {area_path}")
    print()
    
    # Gather all test artifacts in the area path
    print("🔍 Discovering test artifacts in area path...")
    
    # Get test plans
    test_plans = get_test_plans_by_area_path(organization, project, area_path, auth, headers)
    print(f"   📋 Found {len(test_plans)} test plans")
    
    # Get test suites for all plans
    all_test_suites = []
    for plan in test_plans:
        suites = get_test_suites_for_plan(organization, project, plan['id'], auth, headers)
        # Filter out root suites (they're deleted with the plan)
        non_root_suites = [s for s in suites if s.get('suiteType') != 'StaticTestSuite' or s.get('parentSuite', {}).get('id') != s.get('id')]
        all_test_suites.extend([(plan['id'], suite) for suite in non_root_suites])
    
    print(f"   📁 Found {len(all_test_suites)} test suites")
    
    # Get test cases
    test_cases = get_test_cases_by_area_path(organization, project, area_path, auth, headers)
    print(f"   🧪 Found {len(test_cases)} test cases")
    
    # Get shared steps
    shared_steps = get_shared_steps_by_area_path(organization, project, area_path, auth, headers)
    print(f"   🔄 Found {len(shared_steps)} shared steps")
    
    total_items = len(test_plans) + len(all_test_suites) + len(test_cases) + len(shared_steps)
    
    if total_items == 0:
        print("✅ No test artifacts found in the specified area path.")
        return 0
    
    # Display summary
    print(f"\n{'='*60}")
    print("TEST ARTIFACTS DISCOVERY SUMMARY")
    print(f"{'='*60}")
    print(f"Test Plans: {len(test_plans)}")
    print(f"Test Suites: {len(all_test_suites)}")
    print(f"Test Cases: {len(test_cases)}")
    print(f"Shared Steps: {len(shared_steps)}")
    print(f"Total Items: {total_items}")
    print()
    
    # List test plans for user review
    if test_plans:
        print("📋 Test Plans to be deleted:")
        for plan in test_plans:
            print(f"   - {plan['name']} (ID: {plan['id']})")
    
    # Confirm deletion
    print(f"\n⚠️  About to delete ALL test artifacts in area path: {area_path}")
    print("This will permanently delete:")
    print(f"   - {len(test_plans)} test plans")
    print(f"   - {len(all_test_suites)} test suites")
    print(f"   - {len(test_cases)} test cases")
    print(f"   - {len(shared_steps)} shared steps")
    print("\nThis action cannot be undone!")
    
    confirm = input(f"Type 'DELETE-{area_path}' to confirm: ").strip()
    if confirm != f'DELETE-{area_path}':
        print("❌ Operation cancelled.")
        return 0
    
    # Start deletion process
    print(f"\n🗑️ Starting comprehensive test artifact deletion...")
    
    deletion_log = {
        'summary': {
            'area_path': area_path,
            'started_at': datetime.now().isoformat(),
            'total_plans': len(test_plans),
            'total_suites': len(all_test_suites),
            'total_test_cases': len(test_cases),
            'total_shared_steps': len(shared_steps)
        },
        'deletions': []
    }
    
    deleted_counts = {
        'test_plans': 0,
        'test_suites': 0,
        'test_cases': 0,
        'shared_steps': 0
    }
    
    error_counts = {
        'test_plans': 0,
        'test_suites': 0,
        'test_cases': 0,
        'shared_steps': 0
    }
    
    # Step 1: Delete test cases first (they reference suites)
    if test_cases:
        print(f"\n🧪 Deleting {len(test_cases)} test cases...")
        for i, test_case_id in enumerate(test_cases):
            print(f"   Deleting {i+1}/{len(test_cases)}: Test Case {test_case_id}", end=" ... ")
            
            response = delete_test_case_via_test_api(organization, project, test_case_id, auth, headers)
            
            if response.status_code in [200, 204]:
                print("✅")
                deleted_counts['test_cases'] += 1
                deletion_log['deletions'].append({
                    'type': 'test_case',
                    'id': test_case_id,
                    'status': 'deleted',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"❌ ({response.status_code})")
                error_counts['test_cases'] += 1
                deletion_log['deletions'].append({
                    'type': 'test_case',
                    'id': test_case_id,
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Rate limiting
            if i % 10 == 0:
                time.sleep(1)
    
    # Step 2: Delete shared steps
    if shared_steps:
        print(f"\n🔄 Deleting {len(shared_steps)} shared steps...")
        for i, shared_step_id in enumerate(shared_steps):
            print(f"   Deleting {i+1}/{len(shared_steps)}: Shared Step {shared_step_id}", end=" ... ")
            
            response = delete_test_case_via_test_api(organization, project, shared_step_id, auth, headers)
            
            if response.status_code in [200, 204]:
                print("✅")
                deleted_counts['shared_steps'] += 1
                deletion_log['deletions'].append({
                    'type': 'shared_step',
                    'id': shared_step_id,
                    'status': 'deleted',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"❌ ({response.status_code})")
                error_counts['shared_steps'] += 1
                deletion_log['deletions'].append({
                    'type': 'shared_step',
                    'id': shared_step_id,
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.now().isoformat()
                })
    
    # Step 3: Delete test suites (they reference test cases)
    if all_test_suites:
        print(f"\n📁 Deleting {len(all_test_suites)} test suites...")
        for i, (plan_id, suite) in enumerate(all_test_suites):
            suite_id = suite['id']
            suite_name = suite.get('name', f'Suite {suite_id}')
            print(f"   Deleting {i+1}/{len(all_test_suites)}: {suite_name} (ID: {suite_id})", end=" ... ")
            
            response = delete_test_suite(organization, project, plan_id, suite_id, auth, headers)
            
            if response.status_code in [200, 204]:
                print("✅")
                deleted_counts['test_suites'] += 1
                deletion_log['deletions'].append({
                    'type': 'test_suite',
                    'id': suite_id,
                    'plan_id': plan_id,
                    'name': suite_name,
                    'status': 'deleted',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"❌ ({response.status_code})")
                error_counts['test_suites'] += 1
                deletion_log['deletions'].append({
                    'type': 'test_suite',
                    'id': suite_id,
                    'plan_id': plan_id,
                    'name': suite_name,
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.now().isoformat()
                })
    
    # Step 4: Delete test plans (they contain suites)
    if test_plans:
        print(f"\n📋 Deleting {len(test_plans)} test plans...")
        for i, plan in enumerate(test_plans):
            plan_id = plan['id']
            plan_name = plan['name']
            print(f"   Deleting {i+1}/{len(test_plans)}: {plan_name} (ID: {plan_id})", end=" ... ")
            
            response = delete_test_plan(organization, project, plan_id, auth, headers)
            
            if response.status_code in [200, 204]:
                print("✅")
                deleted_counts['test_plans'] += 1
                deletion_log['deletions'].append({
                    'type': 'test_plan',
                    'id': plan_id,
                    'name': plan_name,
                    'status': 'deleted',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"❌ ({response.status_code})")
                error_counts['test_plans'] += 1
                deletion_log['deletions'].append({
                    'type': 'test_plan',
                    'id': plan_id,
                    'name': plan_name,
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.now().isoformat()
                })
    
    # Update deletion log summary
    deletion_log['summary'].update({
        'completed_at': datetime.now().isoformat(),
        'deleted_plans': deleted_counts['test_plans'],
        'deleted_suites': deleted_counts['test_suites'],
        'deleted_test_cases': deleted_counts['test_cases'],
        'deleted_shared_steps': deleted_counts['shared_steps'],
        'error_plans': error_counts['test_plans'],
        'error_suites': error_counts['test_suites'],
        'error_test_cases': error_counts['test_cases'],
        'error_shared_steps': error_counts['shared_steps']
    })
    
    # Save deletion log
    safe_area_path = area_path.replace(' ', '_').replace('\\', '_')
    log_file = f"output/test_deletion_complete_{safe_area_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("output", exist_ok=True)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(deletion_log, f, indent=2, ensure_ascii=False)
    
    # Final summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE DELETION SUMMARY")
    print(f"{'='*60}")
    print(f"Area Path: {area_path}")
    print(f"Test Plans: {deleted_counts['test_plans']}/{len(test_plans)} deleted")
    print(f"Test Suites: {deleted_counts['test_suites']}/{len(all_test_suites)} deleted")
    print(f"Test Cases: {deleted_counts['test_cases']}/{len(test_cases)} deleted")
    print(f"Shared Steps: {deleted_counts['shared_steps']}/{len(shared_steps)} deleted")
    print(f"Log saved to: {log_file}")
    
    total_deleted = sum(deleted_counts.values())
    total_errors = sum(error_counts.values())
    
    if total_deleted > 0:
        print(f"\n✅ Successfully deleted {total_deleted} test artifacts!")
    
    if total_errors > 0:
        print(f"\n❌ {total_errors} items had errors. Check the log file for details.")
        return 1 if total_deleted == 0 else 0
    else:
        print(f"\n✅ All test artifacts processed successfully!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
