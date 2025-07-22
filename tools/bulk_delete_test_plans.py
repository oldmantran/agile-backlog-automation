#!/usr/bin/env python3
"""
Bulk Test Plan Deletion Script

This script deletes test plans from the Backlog Automation project.
By deleting test plans, all their child test suites are automatically deleted.
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_loader import Config
import requests

class BulkTestPlanDeleterBacklogProject:
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
        
        # Project
        self.project = "Backlog Automation"
        
        # API endpoints
        self.wiql_url = f"{self.organization_url}/{requests.utils.quote(self.project)}/_apis/wit/wiql?api-version=7.0"
        
        print(f"🔧 Initialized Bulk Test Plan Deleter (Backlog Automation Project)")
        print(f"   Organization: {self.organization_url}")
        print(f"   Project: {self.project}")
        print(f"   WIQL URL: {self.wiql_url}")

    def query_test_plans_via_wiql(self) -> list:
        """
        Query test plans using WIQL from Backlog Automation project.
        
        Returns:
            List of test plan IDs
        """
        print("🔍 Querying test plans via WIQL from Backlog Automation project...")
        
        # Build WIQL query - search for all test plans in Backlog Automation project
        query = "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Test Plan' AND [System.TeamProject] = 'Backlog Automation' ORDER BY [System.Id]"
        
        payload = {"query": query}
        
        print(f"📋 WIQL Query: {query}")
        
        try:
            response = requests.post(
                self.wiql_url,
                json=payload,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            work_items = result.get('workItems', [])
            test_plan_ids = [item['id'] for item in work_items]
            
            print(f"✅ Found {len(test_plan_ids)} test plans")
            
            # Show the original test plan IDs found
            if test_plan_ids:
                print(f"\n📋 ORIGINAL TEST PLAN IDs FOUND:")
                print("=" * 50)
                for i, test_plan_id in enumerate(test_plan_ids, 1):
                    print(f"  {i}. Test Plan ID: {test_plan_id}")
                print("=" * 50)
            
            return test_plan_ids
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying test plans: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

    def delete_test_plan_from_backlog(self, test_plan_id: int) -> bool:
        """
        Delete a test plan using the Test Management REST API.
        
        Args:
            test_plan_id: The test plan ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        print(f"🗑️ Deleting test plan {test_plan_id} from Backlog Automation project...")
        
        try:
            # Use the Test Management API to delete the test plan
            url = f"{self.organization_url}/{requests.utils.quote(self.project)}/_apis/testplan/Plans/{test_plan_id}?api-version=7.0"
            response = requests.delete(url, auth=self.auth, headers=self.headers)
            
            if response.status_code == 204:  # No Content - successful deletion
                print(f"  ✅ Successfully deleted test plan {test_plan_id} from Backlog Automation project")
                return True
            elif response.status_code == 404:
                print(f"  ⚠️ Test plan {test_plan_id} not found or no permissions - may have been already deleted")
                return True  # Consider this a success since the goal is achieved
            else:
                print(f"  ❌ Error deleting test plan {test_plan_id}: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error deleting test plan {test_plan_id}: {e}")
            return False

    def bulk_delete_test_plans(self, test_plan_ids: list) -> dict:
        """
        Perform bulk deletion of test plans from Backlog Automation project.
        
        Args:
            test_plan_ids: List of test plan IDs to delete
            
        Returns:
            Dictionary with deletion statistics
        """
        print(f"🚀 Starting bulk deletion of {len(test_plan_ids)} test plans from Backlog Automation project...")
        print("=" * 80)
        
        stats = {
            'total': len(test_plan_ids),
            'successful_deletions': 0,
            'failed_deletions': 0,
            'errors': []
        }
        
        for i, test_plan_id in enumerate(test_plan_ids, 1):
            print(f"\n📋 Processing {i}/{len(test_plan_ids)}: Test Plan {test_plan_id}")
            
            try:
                if self.delete_test_plan_from_backlog(test_plan_id):
                    stats['successful_deletions'] += 1
                else:
                    stats['failed_deletions'] += 1
                    stats['errors'].append(f"Failed to delete test plan {test_plan_id}")
                
            except Exception as e:
                stats['failed_deletions'] += 1
                stats['errors'].append(f"Exception processing test plan {test_plan_id}: {e}")
                print(f"  ❌ Exception: {e}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 BULK DELETION SUMMARY (Backlog Automation Project)")
        print("=" * 80)
        print(f"Total test plans processed: {stats['total']}")
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
    """Main function to run the bulk test plan deletion from Backlog Automation project."""
    print("🗑️ Bulk Test Plan Deletion Script (Backlog Automation Project)")
    print("=" * 70)
    
    try:
        # Configuration
        organization_url = "https://dev.azure.com/c4workx"
        
        # Initialize deleter
        deleter = BulkTestPlanDeleterBacklogProject(organization_url)
        
        # Query test plans from Backlog Automation project
        test_plan_ids = deleter.query_test_plans_via_wiql()
        
        if not test_plan_ids:
            print("✅ No test plans found to delete")
            return
        
        # All test plans will be deleted
        print(f"📋 All test plans will be deleted: {len(test_plan_ids)}")
        
        # Show the top 5 work item IDs that would be deleted
        if test_plan_ids:
            print(f"\n🔍 TOP 5 WORK ITEM IDs FOR DELETION:")
            print("=" * 50)
            for i, test_plan_id in enumerate(sorted(test_plan_ids)[:5], 1):
                print(f"  {i}. Test Plan ID: {test_plan_id}")
            if len(test_plan_ids) > 5:
                print(f"  ... and {len(test_plan_ids) - 5} more test plans")
            print("=" * 50)
        
        # Confirm deletion
        confirm = input("\n⚠️ WARNING: About to delete all test plans from Backlog Automation project!\nThis will also delete ALL child test suites automatically.\nThis action cannot be undone.\n\nDo you want to proceed? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y']:
            print("❌ Deletion cancelled")
            return
        
        # Perform bulk deletion
        stats = deleter.bulk_delete_test_plans(test_plan_ids)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_plan_deletion_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'project': 'Backlog Automation',
                'stats': stats,
                'deleted_test_plan_ids': test_plan_ids[:stats['successful_deletions']] if stats['successful_deletions'] > 0 else []
            }, f, indent=2)
        
        print(f"\n💾 Results saved to {results_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 