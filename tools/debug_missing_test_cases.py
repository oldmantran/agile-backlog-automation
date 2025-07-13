"""
Debug script to understand why only 38/53 user stories are being flagged as missing test cases.
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
from agents.backlog_sweeper_agent import BacklogSweeperAgent
from utils.logger import setup_logger

def debug_missing_test_cases():
    """
    Debug why only 38/53 user stories are being flagged as missing test cases.
    """
    print("=== DEBUG: Missing Test Cases Detection ===")
    
    # Load configuration
    config = Config()
    logger = setup_logger('debug_missing_test_cases', 'logs/debug_missing_test_cases.log')
    
    # Initialize Azure DevOps client
    ado_client = AzureDevOpsIntegrator(config)
    
    # Query all user stories in the Data Visualization area path
    area_path = "Backlog Automation\\Data Visualization"
    print(f"Querying user stories in area path: {area_path}")
    
    user_story_ids = ado_client.query_work_items("User Story", area_path=area_path)
    print(f"Found {len(user_story_ids)} user stories total")
    
    missing_test_cases = []
    has_test_cases = []
    processing_errors = []
    
    for i, story_id in enumerate(user_story_ids):
        try:
            print(f"Processing {i+1}/{len(user_story_ids)}: User Story ID {story_id}")
            
            # Get story details
            story_details = ado_client.get_work_item_details([story_id])
            if not story_details:
                print(f"  ERROR: Could not get details for story {story_id}")
                processing_errors.append(story_id)
                continue
                
            story_title = story_details[0].get('fields', {}).get('System.Title', 'No Title')
            story_state = story_details[0].get('fields', {}).get('System.State', 'Unknown')
            print(f"  Title: {story_title}")
            print(f"  State: {story_state}")
            
            # Get relations
            relations = ado_client.get_work_item_relations(story_id)
            children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
            print(f"  Total children: {len(children)}")
            
            # Check each child to see if any are test cases
            test_case_children = []
            other_children = []
            
            for child in children:
                try:
                    child_id = int(child['url'].split('/')[-1])
                    child_details = ado_client.get_work_item_details([child_id])
                    
                    if child_details:
                        child_type = child_details[0].get('fields', {}).get('System.WorkItemType', '')
                        child_title = child_details[0].get('fields', {}).get('System.Title', '')
                        
                        if child_type == 'Test Case':
                            test_case_children.append({
                                'id': child_id,
                                'title': child_title,
                                'type': child_type
                            })
                        else:
                            other_children.append({
                                'id': child_id,
                                'title': child_title,
                                'type': child_type
                            })
                except Exception as e:
                    print(f"    ERROR processing child {child.get('url', 'unknown')}: {e}")
            
            print(f"  Test Case children: {len(test_case_children)}")
            for tc in test_case_children:
                print(f"    - {tc['id']}: {tc['title']}")
                
            print(f"  Other children: {len(other_children)}")
            for oc in other_children:
                print(f"    - {oc['id']} ({oc['type']}): {oc['title']}")
            
            # Determine if this story is missing test cases
            if len(test_case_children) == 0:
                missing_test_cases.append({
                    'id': story_id,
                    'title': story_title,
                    'state': story_state,
                    'total_children': len(children),
                    'other_children': len(other_children)
                })
                print(f"  RESULT: MISSING TEST CASES")
            else:
                has_test_cases.append({
                    'id': story_id,
                    'title': story_title,
                    'state': story_state,
                    'test_cases': len(test_case_children),
                    'total_children': len(children)
                })
                print(f"  RESULT: HAS TEST CASES ({len(test_case_children)})")
            
            print()
            
        except Exception as e:
            print(f"  EXCEPTION processing story {story_id}: {e}")
            processing_errors.append(story_id)
            print()
    
    # Summary
    print("=== SUMMARY ===")
    print(f"Total user stories found: {len(user_story_ids)}")
    print(f"Stories missing test cases: {len(missing_test_cases)}")
    print(f"Stories with test cases: {len(has_test_cases)}")
    print(f"Processing errors: {len(processing_errors)}")
    print()
    
    print("=== STORIES MISSING TEST CASES ===")
    for story in missing_test_cases:
        print(f"ID {story['id']}: {story['title']} (State: {story['state']}, Children: {story['total_children']})")
    print()
    
    print("=== STORIES WITH TEST CASES ===")
    for story in has_test_cases:
        print(f"ID {story['id']}: {story['title']} (State: {story['state']}, Test Cases: {story['test_cases']})")
    print()
    
    if processing_errors:
        print("=== PROCESSING ERRORS ===")
        for error_id in processing_errors:
            print(f"Story ID {error_id}")
        print()
    
    # Save detailed results
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_user_stories': len(user_story_ids),
        'missing_test_cases_count': len(missing_test_cases),
        'has_test_cases_count': len(has_test_cases),
        'processing_errors_count': len(processing_errors),
        'missing_test_cases': missing_test_cases,
        'has_test_cases': has_test_cases,
        'processing_errors': processing_errors
    }
    
    output_file = f"output/debug_missing_test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    debug_missing_test_cases()
