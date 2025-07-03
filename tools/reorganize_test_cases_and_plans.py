# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Script to reorganize test cases in Azure DevOps:
1. Move test cases from Features to User Stories (where they belong)
2. Create proper test plans and test suites
3. Organize test cases according to ADO best practices

Target Area Path: Backlog Automation\Data Visualization
"""

import os
import sys
import re
import requests
import base64
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

def log(msg):
    print(f"[LOG] {msg}")

class TestCaseReorganizer:
    def __init__(self):
        """Initialize the test case reorganizer."""
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
        
        self.base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis"
        self.wit_url = f"{self.base_url}/wit"
        self.test_plans_url = f"{self.base_url}/testplan"
        
        # Target area path from settings
        self.target_area_path = f"{self.project}\\Data Visualization"
        
        # Statistics
        self.test_cases_found = 0
        self.test_cases_reorganized = 0
        self.test_cases_failed = 0
        self.test_plans_created = 0
        self.test_suites_created = 0
        
        log(f"🔧 Initialized Test Case Reorganizer")
        log(f"   Organization: {self.organization}")
        log(f"   Project: {self.project}")
        log(f"   Target Area Path: {self.target_area_path}")
    
    def query_work_items(self, work_item_type: str, area_path: str = None) -> List[int]:
        """Query work items of a specific type in the target area path."""
        log(f"Querying {work_item_type} work items...")
        log(f"Area path used in WIQL: '{self.target_area_path}'")
        
        # Build WIQL query
        area_filter = f"AND [System.AreaPath] UNDER '{self.target_area_path}'" if area_path else ""
        wiql_query = {
            "query": f"""SELECT [System.Id], [System.Title], [System.AreaPath] 
                        FROM WorkItems 
                        WHERE [System.TeamProject] = '{self.project}' 
                        AND [System.WorkItemType] = '{work_item_type}'
                        {area_filter}
                        ORDER BY [System.Id] DESC"""
        }
        log(f"WIQL Query: {wiql_query['query']}")
        
        try:
            response = requests.post(
                f"{self.wit_url}/wiql?api-version=7.1",
                headers=self.headers,
                json=wiql_query
            )
            
            response.raise_for_status()
            data = response.json()
            
            work_item_ids = [item['id'] for item in data.get('workItems', [])]
            log(f"Found {len(work_item_ids)} {work_item_type} work items")
            if not work_item_ids:
                log(f"Raw WIQL response: {json.dumps(data, indent=2)}")
            return work_item_ids
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error querying {work_item_type}: {e}")
            return []
    
    def get_work_item_details(self, work_item_ids: List[int], fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get detailed information for work items in batches."""
        if not work_item_ids:
            log("No work item IDs provided to get_work_item_details.")
            return []
        
        # Default fields to retrieve
        if fields is None:
            fields = [
                "System.Id", "System.Title", "System.WorkItemType", 
                "System.AreaPath", "System.State", "System.CreatedDate"
            ]
        
        all_work_items = []
        batch_size = 200  # Azure DevOps API limit
        
        log(f"Fetching work item details in batches of {batch_size}...")
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            
            ids_param = ','.join(map(str, batch_ids))
            fields_param = ','.join(fields)
            
            log(f"Fetching batch {batch_number}: IDs {ids_param}")
            
            try:
                response = requests.get(
                    f"{self.wit_url}/workitems?ids={ids_param}&fields={fields_param}&api-version=7.1",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                work_items = data.get('value', [])
                all_work_items.extend(work_items)
                
                log(f"Fetched {len(work_items)} work items in batch {batch_number}")
                
            except requests.exceptions.RequestException as e:
                log(f"Error fetching work items batch {batch_number}: {e}")
                continue
        
        log(f"Total work items fetched: {len(all_work_items)}")
        return all_work_items
    
    def get_work_item_relations(self, work_item_id: int) -> List[Dict[str, Any]]:
        """Get all relations for a work item."""
        try:
            response = requests.get(
                f"{self.wit_url}/workitems/{work_item_id}?$expand=relations&api-version=7.1",
                headers=self.headers
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get('relations', [])
            
        except requests.exceptions.RequestException as e:
            log(f"Error getting relations for work item {work_item_id}: {e}")
            return []
    
    def find_parent_user_story(self, test_case_id: int) -> Optional[int]:
        """Find the parent User Story for a test case by traversing the hierarchy."""
        relations = self.get_work_item_relations(test_case_id)
        
        for relation in relations:
            if relation.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
                # This is a parent link
                parent_url = relation.get('url', '')
                parent_id = self._extract_work_item_id_from_url(parent_url)
                
                if parent_id:
                    # Get the parent work item type
                    try:
                        response = requests.get(
                            f"{self.wit_url}/workitems/{parent_id}?fields=System.WorkItemType&api-version=7.1",
                            headers=self.headers
                        )
                        response.raise_for_status()
                        data = response.json()
                        work_item_type = data.get('fields', {}).get('System.WorkItemType', '')
                        
                        if work_item_type == 'User Story':
                            return parent_id
                        elif work_item_type == 'Feature':
                            # Recursively look for User Story parent
                            return self.find_parent_user_story(parent_id)
                            
                    except requests.exceptions.RequestException as e:
                        log(f"Error getting parent work item {parent_id}: {e}")
                        continue
        
        return None
    
    def _extract_work_item_id_from_url(self, url: str) -> Optional[int]:
        """Extract work item ID from Azure DevOps URL."""
        match = re.search(r'/workitems/(\d+)', url)
        return int(match.group(1)) if match else None
    
    def create_test_plan(self, plan_name: str, description: str = '') -> Optional[Dict[str, Any]]:
        """Create a test plan in Azure DevOps."""
        try:
            plan_data = {
                "name": plan_name,
                "description": description,
                "areaPath": self.target_area_path,
                "startDate": datetime.now().isoformat(),
                "endDate": datetime.now().isoformat(),  # Will be updated when we have actual dates
                "owner": {
                    "displayName": "QA Team"
                }
            }
            
            response = requests.post(
                f"{self.test_plans_url}/plans?api-version=7.1",
                headers=self.headers,
                json=plan_data
            )
            
            response.raise_for_status()
            plan = response.json()
            
            log(f"✅ Created test plan: {plan_name} (ID: {plan['id']})")
            return plan
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error creating test plan {plan_name}: {e}")
            return None
    
    def create_test_suite(self, suite_name: str, plan_id: int, parent_suite_id: int = None) -> Optional[Dict[str, Any]]:
        """Create a test suite in Azure DevOps."""
        try:
            suite_data = {
                "name": suite_name,
                "parentSuite": {
                    "id": parent_suite_id
                } if parent_suite_id else None
            }
            
            response = requests.post(
                f"{self.test_plans_url}/plans/{plan_id}/suites?api-version=7.1",
                headers=self.headers,
                json=suite_data
            )
            
            response.raise_for_status()
            suite = response.json()
            
            log(f"✅ Created test suite: {suite_name} (ID: {suite['id']})")
            return suite
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error creating test suite {suite_name}: {e}")
            return None
    
    def add_test_case_to_suite(self, suite_id: int, test_case_id: int) -> bool:
        """Add a test case to a test suite."""
        try:
            test_case_data = {
                "workItem": {
                    "id": test_case_id
                }
            }
            
            response = requests.post(
                f"{self.test_plans_url}/suites/{suite_id}/testcases?api-version=7.1",
                headers=self.headers,
                json=test_case_data
            )
            
            response.raise_for_status()
            log(f"✅ Added test case {test_case_id} to suite {suite_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error adding test case {test_case_id} to suite {suite_id}: {e}")
            return False
    
    def reorganize_test_cases(self, dry_run: bool = True):
        """Main method to reorganize test cases and create test plans."""
        try:
            log("=" * 80)
            log("REORGANIZING TEST CASES AND CREATING TEST PLANS")
            log(f"Target Area Path: {self.target_area_path}")
            log(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
            log("=" * 80)
            
            # Step 1: Get all test cases in the target area path
            test_case_ids = self.query_work_items("Test Case", self.target_area_path)
            if not test_case_ids:
                log("No test cases found in target area path.")
                return
            
            # Step 2: Get test case details
            test_cases = self.get_work_item_details(test_case_ids)
            if not test_cases:
                log("No test case details found.")
                return
            
            self.test_cases_found = len(test_cases)
            
            log(f"\nProcessing {len(test_cases)} test cases...")
            log("-" * 80)
            
            # Step 3: Group test cases by their current parent
            test_cases_by_parent = {}
            orphaned_test_cases = []
            
            for test_case in test_cases:
                test_case_id = test_case.get('id')
                title = test_case.get('fields', {}).get('System.Title', 'Unknown')
                
                log(f"\nAnalyzing Test Case {test_case_id}: {title}")
                
                # Find the parent User Story
                parent_user_story_id = self.find_parent_user_story(test_case_id)
                
                if parent_user_story_id:
                    if parent_user_story_id not in test_cases_by_parent:
                        test_cases_by_parent[parent_user_story_id] = []
                    test_cases_by_parent[parent_user_story_id].append(test_case)
                    log(f"  -> Found parent User Story: {parent_user_story_id}")
                else:
                    orphaned_test_cases.append(test_case)
                    log(f"  -> No User Story parent found (orphaned)")
            
            log(f"\n📊 Analysis Results:")
            log(f"   Test cases with User Story parents: {sum(len(cases) for cases in test_cases_by_parent.values())}")
            log(f"   Orphaned test cases: {len(orphaned_test_cases)}")
            log(f"   User Stories with test cases: {len(test_cases_by_parent)}")
            
            # Step 4: Create test plans and suites for each User Story
            if not dry_run:
                log(f"\n🔧 Creating test plans and suites...")
                
                for user_story_id, test_cases in test_cases_by_parent.items():
                    # Get User Story details
                    try:
                        response = requests.get(
                            f"{self.wit_url}/workitems/{user_story_id}?fields=System.Title&api-version=7.1",
                            headers=self.headers
                        )
                        response.raise_for_status()
                        user_story_data = response.json()
                        user_story_title = user_story_data.get('fields', {}).get('System.Title', 'Unknown User Story')
                        
                        # Create test plan for this User Story
                        plan_name = f"Test Plan - {user_story_title}"
                        test_plan = self.create_test_plan(plan_name, f"Test plan for User Story: {user_story_title}")
                        
                        if test_plan:
                            self.test_plans_created += 1
                            
                            # Create test suite for this User Story
                            suite_name = f"User Story: {user_story_title}"
                            test_suite = self.create_test_suite(suite_name, test_plan['id'])
                            
                            if test_suite:
                                self.test_suites_created += 1
                                
                                # Add test cases to the suite
                                for test_case in test_cases:
                                    test_case_id = test_case.get('id')
                                    if self.add_test_case_to_suite(test_suite['id'], test_case_id):
                                        self.test_cases_reorganized += 1
                        
                    except requests.exceptions.RequestException as e:
                        log(f"Error processing User Story {user_story_id}: {e}")
                        continue
            
            # Step 5: Print summary
            log(f"\n" + "=" * 80)
            log(f"REORGANIZATION SUMMARY")
            log(f"=" * 80)
            log(f"Test cases found: {self.test_cases_found}")
            log(f"Test cases reorganized: {self.test_cases_reorganized}")
            log(f"Test plans created: {self.test_plans_created}")
            log(f"Test suites created: {self.test_suites_created}")
            log(f"Orphaned test cases: {len(orphaned_test_cases)}")
            
            if orphaned_test_cases:
                log(f"\n⚠️  Orphaned test cases (no User Story parent found):")
                for test_case in orphaned_test_cases:
                    test_case_id = test_case.get('id')
                    title = test_case.get('fields', {}).get('System.Title', 'Unknown')
                    log(f"   - {test_case_id}: {title}")
            
            log(f"\n✅ Reorganization {'simulation' if dry_run else 'completed'} successfully!")
            
        except Exception as e:
            log(f"❌ Error during reorganization: {e}")
            raise

def main():
    """Main function to run the test case reorganization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reorganize test cases and create test plans in Azure DevOps")
    parser.add_argument("--live", action="store_true", help="Execute live updates (default is dry run)")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    try:
        # Initialize reorganizer
        reorganizer = TestCaseReorganizer()
        
        # Confirm before live execution
        if args.live and not args.confirm:
            log("\n⚠️  WARNING: This will make live changes to Azure DevOps!")
            log(f"   Target Area Path: {reorganizer.target_area_path}")
            response = input("   Do you want to continue? (y/N): ")
            if response.lower() != 'y':
                log("Operation cancelled.")
                return
        
        # Run reorganization
        reorganizer.reorganize_test_cases(dry_run=not args.live)
        
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
