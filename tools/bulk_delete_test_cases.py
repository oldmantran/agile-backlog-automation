#!/usr/bin/env python3
"""
Bulk Test Case Deletion Script for Grit Project (Final)

This script deletes test cases that belong to the Grit project but are linked to
work items in the Backlog Automation project. Uses the Grit project's Test Management API.
"""

import os
import sys
import json
import requests
from typing import List, Dict, Any
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config

class BulkTestCaseDeleterBacklogProject:
    """Handles bulk deletion of test cases from the Backlog Automation project."""
    
    def __init__(self, organization_url: str, personal_access_token: str = None):
        """Initialize the bulk deleter with Azure DevOps connection details."""
        self.organization_url = organization_url.rstrip('/')
        
        # Use provided PAT or load from config
        if personal_access_token:
            self.pat = personal_access_token
        else:
            config = Config()
            self.pat = config.env.get('AZURE_DEVOPS_PAT')
        
        if not self.pat:
            raise ValueError("Personal Access Token is required")
        
        # Set up authentication and headers
        self.auth = requests.auth.HTTPBasicAuth('', self.pat)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Projects
        self.backlog_automation_project = "Backlog Automation"
        
        # API endpoints
        self.backlog_wiql_url = f"{self.organization_url}/{requests.utils.quote(self.backlog_automation_project)}/_apis/wit/wiql?api-version=7.0"
        self.backlog_test_management_url = f"{self.organization_url}/{requests.utils.quote(self.backlog_automation_project)}/_apis/test"
        
        print(f"🔧 Initialized Bulk Test Case Deleter (Backlog Automation Project)")
        print(f"   Organization: {self.organization_url}")
        print(f"   Backlog Automation Project: {self.backlog_automation_project}")
        print(f"   Backlog WIQL URL: {self.backlog_wiql_url}")
        print(f"   Backlog Test Management URL: {self.backlog_test_management_url}")
    
    def query_test_cases_via_wiql(self) -> List[int]:
        """
        Query test cases using WIQL from Backlog Automation project.
        
        Returns:
            List of test case IDs
        """
        print("🔍 Querying test cases via WIQL from Backlog Automation project...")
        
        # Build WIQL query - search for all test cases in Backlog Automation project
        query_parts = [
            "SELECT [System.Id] FROM WorkItems",
            "WHERE [System.WorkItemType] = 'Test Case'"
        ]
        
        wiql_query = " ".join(query_parts)
        
        payload = {
            "query": wiql_query
        }
        
        print(f"📋 WIQL Query: {wiql_query}")
        
        try:
            response = requests.post(
                self.backlog_wiql_url,
                json=payload,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            work_items = result.get('workItems', [])
            test_case_ids = [item['id'] for item in work_items]
            
            print(f"✅ Found {len(test_case_ids)} test cases")
            
            # Show the original test case IDs found
            if test_case_ids:
                print(f"\n📋 ORIGINAL TEST CASE IDs FOUND:")
                print("=" * 50)
                for i, test_case_id in enumerate(sorted(test_case_ids), 1):
                    print(f"  {i}. Test Case ID: {test_case_id}")
                print("=" * 50)
            
            return test_case_ids
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying test cases: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise
    
    def delete_test_case_from_backlog(self, test_case_id: int) -> bool:
        """
        Delete a test case using the Backlog Automation project's Test Management REST API.
        
        Args:
            test_case_id: The test case ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        print(f"🗑️ Deleting test case {test_case_id} from Backlog Automation project...")
        
        try:
            # Use the Backlog Automation project's Test Management API to delete the test case
            url = f"{self.backlog_test_management_url}/testcases/{test_case_id}?api-version=7.0"
            response = requests.delete(url, auth=self.auth, headers=self.headers)
            
            if response.status_code == 204:  # No Content - successful deletion
                print(f"  ✅ Successfully deleted test case {test_case_id} from Backlog Automation project")
                return True
            else:
                print(f"  ❌ Error deleting test case {test_case_id}: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error deleting test case {test_case_id}: {e}")
            return False
    
    def bulk_delete_test_cases(self, test_case_ids: List[int]) -> Dict[str, Any]:
        """
        Perform bulk deletion of test cases from Grit project.
        
        Args:
            test_case_ids: List of test case IDs to delete
            
        Returns:
            Dictionary with deletion statistics
        """
        print(f"🚀 Starting bulk deletion of {len(test_case_ids)} test cases from Grit project...")
        print("=" * 80)
        
        stats = {
            'total': len(test_case_ids),
            'successful_deletions': 0,
            'failed_deletions': 0,
            'errors': []
        }
        
        for i, test_case_id in enumerate(test_case_ids, 1):
            print(f"\n📋 Processing {i}/{len(test_case_ids)}: Test Case {test_case_id}")
            
            try:
                # Delete the test case from Backlog Automation project
                if self.delete_test_case_from_backlog(test_case_id):
                    stats['successful_deletions'] += 1
                else:
                    stats['failed_deletions'] += 1
                    stats['errors'].append(f"Failed to delete test case {test_case_id}")
                
            except Exception as e:
                stats['failed_deletions'] += 1
                stats['errors'].append(f"Exception processing test case {test_case_id}: {e}")
                print(f"  ❌ Exception: {e}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 BULK DELETION SUMMARY (Backlog Automation Project)")
        print("=" * 80)
        print(f"Total test cases processed: {stats['total']}")
        print(f"Successful deletions: {stats['successful_deletions']}")
        print(f"Failed deletions: {stats['failed_deletions']}")
        
        if stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")
        
        return stats

def main():
    """Main function to run the bulk test case deletion from Backlog Automation project."""
    print("🗑️ Bulk Test Case Deletion Script (Backlog Automation Project)")
    print("=" * 70)
    
    try:
        # Configuration
        organization_url = "https://dev.azure.com/c4workx"
        
        # Initialize deleter
        deleter = BulkTestCaseDeleterBacklogProject(organization_url)
        
        # Query test cases from Backlog Automation project
        test_case_ids = deleter.query_test_cases_via_wiql()
        
        if not test_case_ids:
            print("✅ No test cases found to delete")
            return
        
        # Filter out test cases with IDs less than 4859
        min_id = 4859
        original_count = len(test_case_ids)
        test_case_ids = [id for id in test_case_ids if id >= min_id]
        
        print(f"🔍 Filtered out {original_count - len(test_case_ids)} test cases with ID < {min_id}")
        print(f"📋 Remaining test cases to delete: {len(test_case_ids)}")
        
        # Show the top 5 work item IDs that would be deleted
        if test_case_ids:
            print(f"\n🔍 TOP 5 WORK ITEM IDs FOR DELETION:")
            print("=" * 50)
            for i, test_case_id in enumerate(sorted(test_case_ids)[:5], 1):
                print(f"  {i}. Test Case ID: {test_case_id}")
            if len(test_case_ids) > 5:
                print(f"  ... and {len(test_case_ids) - 5} more test cases")
            print("=" * 50)
        
        if not test_case_ids:
            print("✅ No test cases found to delete after filtering")
            return
        
        # Confirm deletion
        print(f"\n⚠️ WARNING: About to delete {len(test_case_ids)} test cases from Backlog Automation project!")
        print("This action cannot be undone.")
        print("Note: Test cases will be deleted from the Backlog Automation project.")
        
        confirm = input("\nDo you want to proceed? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y']:
            print("❌ Deletion cancelled")
            return
        
        # Perform bulk deletion
        stats = deleter.bulk_delete_test_cases(test_case_ids)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"bulk_deletion_backlog_project_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        if stats['successful_deletions'] == stats['total']:
            print("🎉 All test cases deleted successfully from Backlog Automation project!")
        else:
            print(f"⚠️ {stats['failed_deletions']} test cases failed to delete")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 