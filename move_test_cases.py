#!/usr/bin/env python3
"""
Script to move all test case work items to the Area Path "Backlog Automation\\Grit"
"""

import os
import sys
import re
import requests
import base64
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

class TestCaseMover:
    def __init__(self):
        """Initialize the test case mover."""
        self.organization = os.getenv("AZURE_DEVOPS_ORG")
        self.project = os.getenv("AZURE_DEVOPS_PROJECT") 
        self.pat = os.getenv("AZURE_DEVOPS_PAT")
        
        # Handle both full URL and organization name formats
        if self.organization and self.organization.startswith("https://dev.azure.com/"):
            self.organization = self.organization.replace("https://dev.azure.com/", "")
        
        if not all([self.organization, self.project, self.pat]):
            raise ValueError("Azure DevOps credentials not configured. Please check your .env file.")
        
        # Create authentication header
        auth_string = f":{self.pat}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        self.patch_headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json-patch+json',
            'Accept': 'application/json'
        }
        
        self.base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit"
        
        # Target area path
        self.target_area_path = f"{self.project}\\Grit"
        
        # Statistics
        self.test_cases_found = 0
        self.test_cases_moved = 0
        self.test_cases_failed = 0
    
    def query_test_cases(self) -> List[int]:
        """Query all test case work items in the project."""
        print("Querying test case work items...")
        
        # WIQL query to get all test cases
        wiql_query = {
            "query": f"""SELECT [System.Id], [System.Title], [System.AreaPath] FROM WorkItems WHERE [System.TeamProject] = '{self.project}' AND [System.WorkItemType] = 'Test Case' ORDER BY [System.Id] DESC"""
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/wiql?api-version=7.1",
                headers=self.headers,
                json=wiql_query
            )
            
            response.raise_for_status()
            data = response.json()
            
            work_item_ids = [item['id'] for item in data.get('workItems', [])]
            print(f"Found {len(work_item_ids)} test case work items")
            return work_item_ids
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying test cases: {e}")
            return []
    
    def get_test_case_details(self, work_item_ids: List[int]) -> List[Dict[str, Any]]:
        """Get detailed information for test cases in batches."""
        if not work_item_ids:
            return []
        
        all_test_cases = []
        batch_size = 200  # Azure DevOps API limit
        
        print("Fetching test case details...")
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            
            ids_param = ','.join(map(str, batch_ids))
            
            try:
                response = requests.get(
                    f"{self.base_url}/workitems?ids={ids_param}&fields=System.Id,System.Title,System.WorkItemType,System.AreaPath&api-version=7.1",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                test_cases = data.get('value', [])
                all_test_cases.extend(test_cases)
                
                print(f"Fetched {len(test_cases)} test cases (batch {batch_number})")
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching test cases batch {batch_number}: {e}")
                continue
        
        print(f"Total test cases fetched: {len(all_test_cases)}")
        return all_test_cases
    
    def update_area_path(self, work_item_id: int, current_area_path: str, dry_run: bool = True) -> bool:
        """Update the area path of a single work item."""
        if current_area_path == self.target_area_path:
            print(f"  -> Work item {work_item_id} already in target area path")
            return True
        
        print(f"  Moving work item {work_item_id} from '{current_area_path}' to '{self.target_area_path}'")
        
        if dry_run:
            print(f"    DRY RUN - Would update area path")
            return True
        
        # Create patch document to update area path
        patch_document = [
            {
                "op": "replace",
                "path": "/fields/System.AreaPath",
                "value": self.target_area_path
            }
        ]
        
        try:
            response = requests.patch(
                f"{self.base_url}/workitems/{work_item_id}?api-version=7.1",
                headers=self.patch_headers,
                json=patch_document
            )
            
            response.raise_for_status()
            print(f"    Successfully updated area path")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"    Error updating work item {work_item_id}: {e}")
            return False
    
    def move_test_cases(self, dry_run: bool = True):
        """Main method to move all test cases to the target area path."""
        try:
            print("=" * 70)
            print("MOVING TEST CASES TO AREA PATH")
            print(f"Target Area Path: {self.target_area_path}")
            print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
            print("=" * 70)
            
            # Get test case IDs
            test_case_ids = self.query_test_cases()
            if not test_case_ids:
                print("No test cases found.")
                return
            
            # Get test case details
            test_cases = self.get_test_case_details(test_case_ids)
            if not test_cases:
                print("No test case details found.")
                return
            
            self.test_cases_found = len(test_cases)
            
            print(f"\nProcessing {len(test_cases)} test cases...")
            print("-" * 70)
            
            # Update each test case
            for test_case in test_cases:
                fields = test_case.get('fields', {})
                work_item_id = test_case.get('id')
                title = fields.get('System.Title', 'Unknown')
                current_area_path = fields.get('System.AreaPath', '')
                
                print(f"\nTest Case {work_item_id}: {title}")
                print(f"   Current Area Path: {current_area_path}")
                
                success = self.update_area_path(work_item_id, current_area_path, dry_run)
                
                if success:
                    self.test_cases_moved += 1
                else:
                    self.test_cases_failed += 1
            
            # Print summary
            print("\n" + "=" * 70)
            print("SUMMARY:")
            print(f"   Test cases found: {self.test_cases_found}")
            print(f"   Test cases moved: {self.test_cases_moved}")
            print(f"   Test cases failed: {self.test_cases_failed}")
            
            if dry_run:
                print(f"\nThis was a DRY RUN. Use --live to actually move the test cases.")
            else:
                print(f"\nTest case area path update completed!")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"Error during test case move: {e}")

def main():
    """Main entry point."""
    import sys
    
    # Check for live mode flag
    dry_run = True
    if "--live" in sys.argv:
        dry_run = False
        print("LIVE MODE ENABLED - Changes will be made to Azure DevOps!")
        
        # Ask for confirmation in live mode
        if "--confirm" not in sys.argv:
            response = input("Are you sure you want to proceed? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
    
    mover = TestCaseMover()
    mover.move_test_cases(dry_run=dry_run)

if __name__ == "__main__":
    main()
