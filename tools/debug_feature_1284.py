# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Debug script to examine Feature 1284 - Real-Time Data Collection from Field Sensors
and verify its User Story children (1285, 1297) and Test Case children (1298-1306).
"""

import os
import sys
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

def log(msg):
    print(f"[LOG] {msg}")

class FeatureDebugger:
    def __init__(self):
        """Initialize the feature debugger."""
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
        
        self.base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis"
        self.wit_url = f"{self.base_url}/wit"
        
        log(f"🔧 Initialized Feature Debugger")
        log(f"   Organization: {self.organization}")
        log(f"   Project: {self.project}")
    
    def get_work_item_details(self, work_item_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific work item."""
        try:
            response = requests.get(
                f"{self.wit_url}/workitems/{work_item_id}?api-version=7.1",
                headers=self.headers
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error getting work item {work_item_id}: {e}")
            return {}
    
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
            log(f"❌ Error getting relations for work item {work_item_id}: {e}")
            return []
    
    def query_children_by_wiql(self, parent_id: int, work_item_type: str = None) -> List[Dict[str, Any]]:
        """Query child work items using WIQL."""
        log(f"Querying children of work item {parent_id} using WIQL...")
        
        # Build WIQL query
        type_filter = f"AND [System.WorkItemType] = '{work_item_type}'" if work_item_type else ""
        wiql_query = {
            "query": f"""SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State]
                        FROM WorkItems 
                        WHERE [System.TeamProject] = '{self.project}' 
                        AND [System.Links.LinkType] = 'Child'
                        AND [System.Links.SourceId] = {parent_id}
                        {type_filter}
                        ORDER BY [System.Id]"""
        }
        
        try:
            response = requests.post(
                f"{self.wit_url}/wiql?api-version=7.1",
                headers=self.headers,
                json=wiql_query
            )
            
            response.raise_for_status()
            data = response.json()
            
            work_items = data.get('workItems', [])
            log(f"WIQL found {len(work_items)} children")
            
            # Get details for each child
            if work_items:
                child_ids = [item['id'] for item in work_items]
                return self.get_work_items_batch(child_ids)
            
            return []
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error querying children with WIQL: {e}")
            return []
    
    def get_work_items_batch(self, work_item_ids: List[int]) -> List[Dict[str, Any]]:
        """Get details for multiple work items in a batch."""
        if not work_item_ids:
            return []
        
        ids_param = ','.join(map(str, work_item_ids))
        fields = "System.Id,System.Title,System.WorkItemType,System.State,System.AreaPath"
        
        try:
            response = requests.get(
                f"{self.wit_url}/workitems?ids={ids_param}&fields={fields}&api-version=7.1",
                headers=self.headers
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get('value', [])
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error getting work items batch: {e}")
            return []
    
    def query_children_by_links_api(self, parent_id: int) -> List[Dict[str, Any]]:
        """Query child work items using the Links API."""
        log(f"Querying children of work item {parent_id} using Links API...")
        
        try:
            response = requests.get(
                f"{self.wit_url}/workitems/{parent_id}/links?api-version=7.1",
                headers=self.headers
            )
            
            response.raise_for_status()
            data = response.json()
            
            links = data.get('value', [])
            child_links = [link for link in links if link.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
            
            log(f"Links API found {len(child_links)} child links")
            
            # Extract child IDs from links
            child_ids = []
            for link in child_links:
                url = link.get('url', '')
                if '/workitems/' in url:
                    child_id = url.split('/workitems/')[-1]
                    try:
                        child_ids.append(int(child_id))
                    except ValueError:
                        continue
            
            if child_ids:
                return self.get_work_items_batch(child_ids)
            
            return []
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error querying children with Links API: {e}")
            return []
    
    def debug_feature_1284(self):
        """Debug Feature 1284 and verify its structure."""
        log("=" * 80)
        log("DEBUGGING FEATURE 1284 - Real-Time Data Collection from Field Sensors")
        log("=" * 80)
        
        # Step 1: Get Feature 1284 details
        log(f"\n📋 Step 1: Getting Feature 1284 details...")
        feature_details = self.get_work_item_details(1284)
        
        if not feature_details:
            log("❌ Could not retrieve Feature 1284")
            return
        
        feature_title = feature_details.get('fields', {}).get('System.Title', 'Unknown')
        feature_type = feature_details.get('fields', {}).get('System.WorkItemType', 'Unknown')
        feature_state = feature_details.get('fields', {}).get('System.State', 'Unknown')
        feature_area = feature_details.get('fields', {}).get('System.AreaPath', 'Unknown')
        
        log(f"✅ Feature 1284 found:")
        log(f"   Title: {feature_title}")
        log(f"   Type: {feature_type}")
        log(f"   State: {feature_state}")
        log(f"   Area Path: {feature_area}")
        
        # Step 2: Get all relations
        log(f"\n🔗 Step 2: Getting all relations for Feature 1284...")
        relations = self.get_work_item_relations(1284)
        
        log(f"Found {len(relations)} total relations:")
        for i, relation in enumerate(relations, 1):
            rel_type = relation.get('rel', 'Unknown')
            url = relation.get('url', '')
            log(f"   {i}. Type: {rel_type}, URL: {url}")
        
        # Step 3: Query children using WIQL
        log(f"\n👶 Step 3: Querying children using WIQL...")
        all_children_wiql = self.query_children_by_wiql(1284)
        
        log(f"WIQL found {len(all_children_wiql)} total children:")
        for child in all_children_wiql:
            child_id = child.get('id')
            child_title = child.get('fields', {}).get('System.Title', 'Unknown')
            child_type = child.get('fields', {}).get('System.WorkItemType', 'Unknown')
            log(f"   - {child_id}: {child_title} ({child_type})")
        
        # Step 4: Query User Story children specifically
        log(f"\n📖 Step 4: Querying User Story children specifically...")
        user_story_children = self.query_children_by_wiql(1284, 'User Story')
        
        log(f"Found {len(user_story_children)} User Story children:")
        for child in user_story_children:
            child_id = child.get('id')
            child_title = child.get('fields', {}).get('System.Title', 'Unknown')
            log(f"   - {child_id}: {child_title}")
        
        # Step 5: Query Test Case children specifically
        log(f"\n🧪 Step 5: Querying Test Case children specifically...")
        test_case_children = self.query_children_by_wiql(1284, 'Test Case')
        
        log(f"Found {len(test_case_children)} Test Case children:")
        for child in test_case_children:
            child_id = child.get('id')
            child_title = child.get('fields', {}).get('System.Title', 'Unknown')
            log(f"   - {child_id}: {child_title}")
        
        # Step 6: Query children using Links API
        log(f"\n🔗 Step 6: Querying children using Links API...")
        all_children_links = self.query_children_by_links_api(1284)
        
        log(f"Links API found {len(all_children_links)} total children:")
        for child in all_children_links:
            child_id = child.get('id')
            child_title = child.get('fields', {}).get('System.Title', 'Unknown')
            child_type = child.get('fields', {}).get('System.WorkItemType', 'Unknown')
            log(f"   - {child_id}: {child_title} ({child_type})")
        
        # Step 7: Summary and verification
        log(f"\n" + "=" * 80)
        log(f"SUMMARY AND VERIFICATION")
        log(f"=" * 80)
        
        expected_user_stories = [1285, 1297]
        expected_test_cases = list(range(1298, 1307))  # 1298 to 1306
        
        found_user_story_ids = [child.get('id') for child in user_story_children]
        found_test_case_ids = [child.get('id') for child in test_case_children]
        
        log(f"Expected User Stories: {expected_user_stories}")
        log(f"Found User Stories: {found_user_story_ids}")
        log(f"User Stories match: {set(expected_user_stories) == set(found_user_story_ids)}")
        
        log(f"Expected Test Cases: {expected_test_cases}")
        log(f"Found Test Cases: {found_test_case_ids}")
        log(f"Test Cases match: {set(expected_test_cases) == set(found_test_case_ids)}")
        
        # Check for missing items
        missing_user_stories = set(expected_user_stories) - set(found_user_story_ids)
        missing_test_cases = set(expected_test_cases) - set(found_test_case_ids)
        
        if missing_user_stories:
            log(f"❌ Missing User Stories: {missing_user_stories}")
        else:
            log(f"✅ All expected User Stories found")
            
        if missing_test_cases:
            log(f"❌ Missing Test Cases: {missing_test_cases}")
        else:
            log(f"✅ All expected Test Cases found")
        
        log(f"\n🔍 Analysis complete!")

def main():
    """Main function to run the feature debugger."""
    try:
        debugger = FeatureDebugger()
        debugger.debug_feature_1284()
        
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 