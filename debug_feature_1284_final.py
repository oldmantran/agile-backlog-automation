# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Final debug script with corrected URL parsing to examine Feature 1284.
"""

import os
import sys
import requests
import base64
import json
import re
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

class FeatureDebuggerFinal:
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
        
        log(f"🔧 Initialized Feature Debugger (Final)")
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
    
    def extract_work_item_id_from_url(self, url: str) -> int:
        """Extract work item ID from Azure DevOps URL using regex."""
        # Pattern to match work item ID at the end of the URL
        pattern = r'/workItems/(\d+)$'
        match = re.search(pattern, url)
        
        if match:
            return int(match.group(1))
        
        # Fallback: try to extract from the last part of the URL
        parts = url.split('/')
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        
        return None
    
    def extract_children_from_relations(self, relations: List[Dict[str, Any]]) -> List[int]:
        """Extract child IDs from relations with improved URL parsing."""
        child_ids = []
        
        for relation in relations:
            if relation.get('rel') == 'System.LinkTypes.Hierarchy-Forward':
                url = relation.get('url', '')
                log(f"Processing URL: {url}")
                
                child_id = self.extract_work_item_id_from_url(url)
                if child_id:
                    child_ids.append(child_id)
                    log(f"Extracted child ID: {child_id}")
                else:
                    log(f"Failed to extract ID from URL: {url}")
        
        return child_ids
    
    def debug_feature_1284_final(self):
        """Debug Feature 1284 with corrected URL parsing."""
        log("=" * 80)
        log("DEBUGGING FEATURE 1284 - FINAL APPROACH")
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
        
        # Step 2: Get all relations and extract children
        log(f"\n🔗 Step 2: Getting all relations and extracting children...")
        relations = self.get_work_item_relations(1284)
        
        log(f"Found {len(relations)} total relations:")
        for i, relation in enumerate(relations, 1):
            rel_type = relation.get('rel', 'Unknown')
            url = relation.get('url', '')
            log(f"   {i}. Type: {rel_type}, URL: {url}")
        
        # Extract child IDs from relations with improved parsing
        log(f"\n🔍 Step 2.5: Extracting child IDs with improved parsing...")
        child_ids = self.extract_children_from_relations(relations)
        log(f"Extracted {len(child_ids)} child IDs from relations: {sorted(child_ids)}")
        
        # Step 3: Get details for all children
        log(f"\n👶 Step 3: Getting details for all children...")
        all_children = self.get_work_items_batch(child_ids)
        
        log(f"Retrieved details for {len(all_children)} children:")
        for child in all_children:
            child_id = child.get('id')
            child_title = child.get('fields', {}).get('System.Title', 'Unknown')
            child_type = child.get('fields', {}).get('System.WorkItemType', 'Unknown')
            log(f"   - {child_id}: {child_title} ({child_type})")
        
        # Step 4: Categorize children
        log(f"\n📊 Step 4: Categorizing children...")
        user_stories = [child for child in all_children if child.get('fields', {}).get('System.WorkItemType') == 'User Story']
        test_cases = [child for child in all_children if child.get('fields', {}).get('System.WorkItemType') == 'Test Case']
        other_types = [child for child in all_children if child.get('fields', {}).get('System.WorkItemType') not in ['User Story', 'Test Case']]
        
        log(f"User Stories ({len(user_stories)}):")
        for child in user_stories:
            child_id = child.get('id')
            child_title = child.get('fields', {}).get('System.Title', 'Unknown')
            log(f"   - {child_id}: {child_title}")
        
        log(f"Test Cases ({len(test_cases)}):")
        for child in test_cases:
            child_id = child.get('id')
            child_title = child.get('fields', {}).get('System.Title', 'Unknown')
            log(f"   - {child_id}: {child_title}")
        
        if other_types:
            log(f"Other types ({len(other_types)}):")
            for child in other_types:
                child_id = child.get('id')
                child_title = child.get('fields', {}).get('System.Title', 'Unknown')
                child_type = child.get('fields', {}).get('System.WorkItemType', 'Unknown')
                log(f"   - {child_id}: {child_title} ({child_type})")
        
        # Step 5: Summary and verification
        log(f"\n" + "=" * 80)
        log(f"SUMMARY AND VERIFICATION")
        log(f"=" * 80)
        
        expected_user_stories = [1285, 1297]
        expected_test_cases = list(range(1298, 1307))  # 1298 to 1306
        
        found_user_story_ids = [child.get('id') for child in user_stories]
        found_test_case_ids = [child.get('id') for child in test_cases]
        
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
        debugger = FeatureDebuggerFinal()
        debugger.debug_feature_1284_final()
        
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 