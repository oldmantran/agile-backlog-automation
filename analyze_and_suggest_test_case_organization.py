# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Script to analyze test cases and organize them with User Stories:
1. Find the parent Feature for each test case
2. Examine User Stories under that Feature
3. Move test case to appropriate User Story if found
4. Suggest new User Story groupings for orphaned test cases

Target Area Path: Backlog Automation\Data Visualization
"""

import os
import sys
import re
import requests
import base64
import json
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

def log(msg):
    print(f"[LOG] {msg}")

class TestCaseAnalyzer:
    def __init__(self):
        """Initialize the test case analyzer."""
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
        
        # Target area path from settings
        self.target_area_path = f"{self.project}\\Data Visualization"
        
        # Statistics
        self.test_cases_analyzed = 0
        self.test_cases_moved = 0
        self.test_cases_suggested = 0
        self.features_analyzed = 0
        
        log(f"🔧 Initialized Test Case Analyzer")
        log(f"   Organization: {self.organization}")
        log(f"   Project: {self.project}")
        log(f"   Target Area Path: {self.target_area_path}")
    
    def query_work_items(self, work_item_type: str, area_path: str = None) -> List[int]:
        """Query work items of a specific type in the target area path."""
        log(f"Querying {work_item_type} work items...")
        
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
            return work_item_ids
            
        except requests.exceptions.RequestException as e:
            log(f"❌ Error querying {work_item_type}: {e}")
            return []
    
    def get_work_item_details(self, work_item_ids: List[int], fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get detailed information for work items in batches."""
        if not work_item_ids:
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
    
    def get_work_item_children(self, work_item_id: int, work_item_type: str = None) -> List[Dict[str, Any]]:
        """Get child work items of a specific type using relations."""
        try:
            # Get all relations for the work item
            relations = self.get_work_item_relations(work_item_id)
            
            # Extract child IDs from Hierarchy-Forward relations
            child_ids = []
            for relation in relations:
                if relation.get('rel') == 'System.LinkTypes.Hierarchy-Forward':
                    url = relation.get('url', '')
                    child_id = self._extract_work_item_id_from_url(url)
                    if child_id:
                        child_ids.append(child_id)
            
            if not child_ids:
                return []
            
            # Get details for all children
            all_children = self.get_work_item_details(child_ids)
            
            # Filter by work item type if specified
            if work_item_type:
                filtered_children = [
                    child for child in all_children 
                    if child.get('fields', {}).get('System.WorkItemType') == work_item_type
                ]
                return filtered_children
            
            return all_children
            
        except requests.exceptions.RequestException as e:
            log(f"Error getting children for work item {work_item_id}: {e}")
            return []
    
    def find_parent_feature(self, test_case_id: int) -> Optional[Dict[str, Any]]:
        """Find the parent Feature for a test case."""
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
                            f"{self.wit_url}/workitems/{parent_id}?fields=System.WorkItemType,System.Title&api-version=7.1",
                            headers=self.headers
                        )
                        response.raise_for_status()
                        data = response.json()
                        work_item_type = data.get('fields', {}).get('System.WorkItemType', '')
                        
                        if work_item_type == 'Feature':
                            return {
                                'id': parent_id,
                                'title': data.get('fields', {}).get('System.Title', 'Unknown Feature'),
                                'type': work_item_type
                            }
                        elif work_item_type == 'Epic':
                            # Look for Features under this Epic
                            features = self.get_work_item_children(parent_id, 'Feature')
                            if features:
                                # For now, return the first feature (could be enhanced to find the most relevant)
                                feature = features[0]
                                return {
                                    'id': feature.get('id'),
                                    'title': feature.get('fields', {}).get('System.Title', 'Unknown Feature'),
                                    'type': 'Feature'
                                }
                            
                    except requests.exceptions.RequestException as e:
                        log(f"Error getting parent work item {parent_id}: {e}")
                        continue
        
        return None
    
    def _extract_work_item_id_from_url(self, url: str) -> Optional[int]:
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
    
    def calculate_similarity_score(self, test_case_title: str, user_story_title: str) -> float:
        """Calculate similarity between test case and user story titles."""
        # Convert to lowercase for comparison
        tc_words = set(test_case_title.lower().split())
        us_words = set(user_story_title.lower().split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must', 'shall'}
        tc_words = tc_words - common_words
        us_words = us_words - common_words
        
        if not tc_words or not us_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(tc_words.intersection(us_words))
        union = len(tc_words.union(us_words))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def find_best_user_story_match(self, test_case_title: str, user_stories: List[Dict[str, Any]], threshold: float = 0.3) -> Tuple[Optional[Dict[str, Any]], float]:
        """Find the best matching User Story for a test case."""
        best_match = None
        best_score = 0.0
        
        for user_story in user_stories:
            user_story_title = user_story.get('fields', {}).get('System.Title', '')
            score = self.calculate_similarity_score(test_case_title, user_story_title)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = user_story
        
        return best_match, best_score
    
    def move_test_case_to_user_story(self, test_case_id: int, user_story_id: int, dry_run: bool = True) -> bool:
        """Move a test case to be a child of a User Story."""
        log(f"  Moving test case {test_case_id} to User Story {user_story_id}")
        
        if dry_run:
            log(f"    DRY RUN - Would update parent relationship")
            return True
        
        # Create patch document to update parent relationship
        patch_document = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": f"{self.base_url}/wit/workitems/{user_story_id}"
                }
            }
        ]
        
        try:
            response = requests.patch(
                f"{self.wit_url}/workitems/{test_case_id}?api-version=7.1",
                headers=self.patch_headers,
                json=patch_document
            )
            
            response.raise_for_status()
            log(f"    Successfully moved test case to User Story")
            return True
            
        except requests.exceptions.RequestException as e:
            log(f"    Error moving test case {test_case_id}: {e}")
            return False
    
    def suggest_user_story_grouping(self, test_cases: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Suggest User Story groupings for test cases based on functionality."""
        suggestions = defaultdict(list)
        
        # Define functional areas based on test case titles
        functional_areas = {
            'dashboard': ['dashboard', 'visualization', 'chart', 'metric', 'efficiency'],
            'alerts': ['alert', 'notification', 'threshold', 'breach', 'warning'],
            'data_ingestion': ['ingestion', 'sensor', 'data', 'upload', 'validation'],
            'ai_prediction': ['ai', 'prediction', 'model', 'optimization', 'recommendation'],
            'security': ['security', 'unauthorized', 'access', 'authentication', 'authorization'],
            'performance': ['performance', 'latency', 'load', 'concurrent', 'scaling'],
            'historical_data': ['historical', 'trend', 'analysis', 'report', 'export'],
            'job_design': ['job', 'design', 'scenario', 'template', 'parameter'],
            'scheduling': ['schedule', 'timeline', 'planning', 'operation'],
            'integration': ['integration', 'connection', 'api', 'protocol', 'compatibility']
        }
        
        for test_case in test_cases:
            test_case_id = test_case.get('id')
            title = test_case.get('fields', {}).get('System.Title', '').lower()
            
            # Find the best matching functional area
            best_area = 'general'
            best_score = 0
            
            for area, keywords in functional_areas.items():
                score = sum(1 for keyword in keywords if keyword in title)
                if score > best_score:
                    best_score = score
                    best_area = area
            
            suggestions[best_area].append(test_case)
        
        return dict(suggestions)
    
    def analyze_and_organize_test_cases(self, dry_run: bool = True):
        """Main method to analyze and organize test cases."""
        try:
            log("=" * 80)
            log("ANALYZING AND ORGANIZING TEST CASES")
            log(f"Target Area Path: {self.target_area_path}")
            log(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
            log("=" * 80)
            
            # Step 1: Get all test cases
            test_case_ids = self.query_work_items("Test Case", self.target_area_path)
            if not test_case_ids:
                log("No test cases found in target area path.")
                return
            
            test_cases = self.get_work_item_details(test_case_ids)
            if not test_cases:
                log("No test case details found.")
                return
            
            self.test_cases_analyzed = len(test_cases)
            
            log(f"\nProcessing {len(test_cases)} test cases...")
            log("-" * 80)
            
            # Step 2: Analyze each test case
            moved_test_cases = []
            suggested_test_cases = []
            features_processed = set()
            
            for test_case in test_cases:
                test_case_id = test_case.get('id')
                title = test_case.get('fields', {}).get('System.Title', 'Unknown')
                
                log(f"\nAnalyzing Test Case {test_case_id}: {title}")
                
                # Find parent Feature
                parent_feature = self.find_parent_feature(test_case_id)
                
                if parent_feature:
                    feature_id = parent_feature['id']
                    feature_title = parent_feature['title']
                    
                    log(f"  -> Found parent Feature: {feature_id} - {feature_title}")
                    
                    # Get User Stories under this Feature
                    if feature_id not in features_processed:
                        user_stories = self.get_work_item_children(feature_id, 'User Story')
                        features_processed.add(feature_id)
                        self.features_analyzed += 1
                        
                        log(f"  -> Found {len(user_stories)} User Stories under Feature")
                        
                        # Find best matching User Story
                        best_match, score = self.find_best_user_story_match(title, user_stories)
                        
                        if best_match:
                            user_story_id = best_match.get('id')
                            user_story_title = best_match.get('fields', {}).get('System.Title', 'Unknown')
                            
                            log(f"  -> Best match: User Story {user_story_id} - {user_story_title} (score: {score:.2f})")
                            
                            # Move test case to User Story
                            if self.move_test_case_to_user_story(test_case_id, user_story_id, dry_run):
                                moved_test_cases.append({
                                    'test_case_id': test_case_id,
                                    'test_case_title': title,
                                    'user_story_id': user_story_id,
                                    'user_story_title': user_story_title,
                                    'feature_id': feature_id,
                                    'feature_title': feature_title,
                                    'similarity_score': score
                                })
                                self.test_cases_moved += 1
                        else:
                            log(f"  -> No suitable User Story found (best score: {score:.2f})")
                            suggested_test_cases.append(test_case)
                            self.test_cases_suggested += 1
                    else:
                        log(f"  -> Feature already processed, skipping")
                        suggested_test_cases.append(test_case)
                        self.test_cases_suggested += 1
                else:
                    log(f"  -> No parent Feature found")
                    suggested_test_cases.append(test_case)
                    self.test_cases_suggested += 1
            
            # Step 3: Generate suggestions for remaining test cases
            if suggested_test_cases:
                log(f"\n📋 Generating User Story suggestions for {len(suggested_test_cases)} test cases...")
                suggestions = self.suggest_user_story_grouping(suggested_test_cases)
                
                log(f"\n🎯 Suggested User Story Groupings:")
                for area, test_cases in suggestions.items():
                    log(f"\n  {area.upper().replace('_', ' ')} ({len(test_cases)} test cases):")
                    for test_case in test_cases[:5]:  # Show first 5 examples
                        test_case_id = test_case.get('id')
                        title = test_case.get('fields', {}).get('System.Title', 'Unknown')
                        log(f"    - {test_case_id}: {title}")
                    if len(test_cases) > 5:
                        log(f"    ... and {len(test_cases) - 5} more")
            
            # Step 4: Print summary
            log(f"\n" + "=" * 80)
            log(f"ANALYSIS SUMMARY")
            log(f"=" * 80)
            log(f"Test cases analyzed: {self.test_cases_analyzed}")
            log(f"Features analyzed: {self.features_analyzed}")
            log(f"Test cases moved to User Stories: {self.test_cases_moved}")
            log(f"Test cases needing User Story suggestions: {self.test_cases_suggested}")
            
            if moved_test_cases:
                log(f"\n✅ Successfully moved test cases:")
                for move in moved_test_cases[:10]:  # Show first 10
                    log(f"   - {move['test_case_id']} -> User Story {move['user_story_id']} (score: {move['similarity_score']:.2f})")
                if len(moved_test_cases) > 10:
                    log(f"   ... and {len(moved_test_cases) - 10} more")
            
            log(f"\n✅ Analysis {'simulation' if dry_run else 'completed'} successfully!")
            
        except Exception as e:
            log(f"❌ Error during analysis: {e}")
            raise

def main():
    """Main function to run the test case analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze test cases and organize them with User Stories")
    parser.add_argument("--live", action="store_true", help="Execute live updates (default is dry run)")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = TestCaseAnalyzer()
        
        # Confirm before live execution
        if args.live and not args.confirm:
            log("\n⚠️  WARNING: This will make live changes to Azure DevOps!")
            log(f"   Target Area Path: {analyzer.target_area_path}")
            response = input("   Do you want to continue? (y/N): ")
            if response.lower() != 'y':
                log("Operation cancelled.")
                return
        
        # Run analysis
        analyzer.analyze_and_organize_test_cases(dry_run=not args.live)
        
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
