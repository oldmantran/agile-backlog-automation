"""
Update Work Item Area and Iteration Paths

This script updates all Features, User Stories, Tasks, and Test Cases
to use the correct area path and iteration path in Azure DevOps.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any
import requests
from requests.auth import HTTPBasicAuth

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config


class WorkItemPathUpdater:
    """Updates area and iteration paths for existing work items."""
    
    def __init__(self, config: Config):
        """Initialize with Azure DevOps configuration."""
        self.config = config
        self.logger = logging.getLogger("work_item_updater")
        
        # Azure DevOps connection settings
        self.organization = config.get_env("AZURE_DEVOPS_ORG")
        self.project = config.get_env("AZURE_DEVOPS_PROJECT")
        self.pat = config.get_env("AZURE_DEVOPS_PAT")
        
        # Handle both full URL and organization name formats
        if self.organization and self.organization.startswith("https://dev.azure.com/"):
            self.organization = self.organization.replace("https://dev.azure.com/", "")
        
        if not all([self.organization, self.project, self.pat]):
            raise ValueError("Azure DevOps credentials not configured")
            
        # API setup
        self.project_base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis"
        self.auth = HTTPBasicAuth('', self.pat)
        self.headers = {
            'Content-Type': 'application/json-patch+json',
            'Accept': 'application/json'
        }
        
        # New paths to set
        self.new_area_path = "Backlog Automation"
        self.new_iteration_path = "Backlog Automation"
    
    def get_work_items_by_type(self, work_item_types: List[str]) -> List[Dict[str, Any]]:
        """Get all work items of specified types."""
        # Build WIQL query to find work items by type
        types_filter = "', '".join(work_item_types)
        wiql_query = f"""
        SELECT [System.Id], [System.Title], [System.WorkItemType], [System.AreaPath], [System.IterationPath]
        FROM WorkItems
        WHERE [System.TeamProject] = '{self.project}'
        AND [System.WorkItemType] IN ('{types_filter}')
        """
        
        url = f"{self.project_base_url}/wit/wiql?api-version=7.0"
        
        query_data = {
            "query": wiql_query
        }
        
        try:
            response = requests.post(
                url,
                json=query_data,
                auth=self.auth,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            result = response.json()
            work_items = result.get('workItems', [])
            
            if not work_items:
                self.logger.info(f"No work items found for types: {work_item_types}")
                return []
            
            # Get detailed work item information
            work_item_ids = [str(wi['id']) for wi in work_items]
            return self.get_work_items_details(work_item_ids)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to query work items: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def get_work_items_details(self, work_item_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information for work items."""
        if not work_item_ids:
            return []
        
        # Azure DevOps limits batch requests to 200 items
        batch_size = 200
        all_work_items = []
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            ids_param = ','.join(batch_ids)
            
            url = f"{self.project_base_url}/wit/workitems?ids={ids_param}&fields=System.Id,System.Title,System.WorkItemType,System.AreaPath,System.IterationPath,System.State&api-version=7.0"
            
            try:
                response = requests.get(url, auth=self.auth)
                response.raise_for_status()
                
                result = response.json()
                all_work_items.extend(result.get('value', []))
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to get work item details for batch: {e}")
                raise
        
        return all_work_items
    
    def update_work_item_paths(self, work_item_id: int, current_area: str, current_iteration: str) -> bool:
        """Update area and iteration paths for a work item."""
        url = f"{self.project_base_url}/wit/workitems/{work_item_id}?api-version=7.0"
        
        # Build patch document
        patch_document = []
        
        # Update area path if different
        if current_area != self.new_area_path:
            patch_document.append({
                'op': 'replace',
                'path': '/fields/System.AreaPath',
                'value': self.new_area_path
            })
        
        # Update iteration path if different
        if current_iteration != self.new_iteration_path:
            patch_document.append({
                'op': 'replace',
                'path': '/fields/System.IterationPath',
                'value': self.new_iteration_path
            })
        
        # Skip if no updates needed
        if not patch_document:
            return True
        
        try:
            response = requests.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update work item {work_item_id}: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            return False
    
    def update_all_work_items(self) -> Dict[str, Any]:
        """Update paths for all Features, User Stories, Tasks, and Test Cases."""
        work_item_types = ['Feature', 'User Story', 'Task', 'Test Case']
        
        self.logger.info(f"Fetching work items of types: {work_item_types}")
        work_items = self.get_work_items_by_type(work_item_types)
        
        if not work_items:
            self.logger.info("No work items found to update")
            return {
                'total_found': 0,
                'updated': 0,
                'skipped': 0,
                'failed': 0,
                'details': []
            }
        
        results = {
            'total_found': len(work_items),
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }
        
        self.logger.info(f"Found {len(work_items)} work items to process")
        
        for work_item in work_items:
            fields = work_item.get('fields', {})
            work_item_id = work_item['id']
            title = fields.get('System.Title', 'Unknown')
            work_item_type = fields.get('System.WorkItemType', 'Unknown')
            current_area = fields.get('System.AreaPath', '')
            current_iteration = fields.get('System.IterationPath', '')
            
            # Check if update is needed
            needs_area_update = current_area != self.new_area_path
            needs_iteration_update = current_iteration != self.new_iteration_path
            
            if not needs_area_update and not needs_iteration_update:
                self.logger.info(f"Skipping {work_item_type} {work_item_id}: {title} (paths already correct)")
                results['skipped'] += 1
                results['details'].append({
                    'id': work_item_id,
                    'type': work_item_type,
                    'title': title,
                    'status': 'skipped',
                    'reason': 'paths already correct'
                })
                continue
            
            self.logger.info(f"Updating {work_item_type} {work_item_id}: {title}")
            self.logger.info(f"  Area: '{current_area}' -> '{self.new_area_path}'")
            self.logger.info(f"  Iteration: '{current_iteration}' -> '{self.new_iteration_path}'")
            
            success = self.update_work_item_paths(work_item_id, current_area, current_iteration)
            
            if success:
                results['updated'] += 1
                results['details'].append({
                    'id': work_item_id,
                    'type': work_item_type,
                    'title': title,
                    'status': 'updated',
                    'old_area': current_area,
                    'new_area': self.new_area_path,
                    'old_iteration': current_iteration,
                    'new_iteration': self.new_iteration_path
                })
                self.logger.info(f"  Successfully updated")
            else:
                results['failed'] += 1
                results['details'].append({
                    'id': work_item_id,
                    'type': work_item_type,
                    'title': title,
                    'status': 'failed'
                })
                self.logger.error(f"  Failed to update")
        
        return results


def main():
    """Main execution function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("update_paths")
    
    try:
        # Load configuration
        config = Config()
        
        # Create updater
        updater = WorkItemPathUpdater(config)
        
        # Confirm with user
        print("\n🔄 Work Item Path Updater")
        print("=" * 50)
        print(f"📍 New Area Path: {updater.new_area_path}")
        print(f"📅 New Iteration Path: {updater.new_iteration_path}")
        print(f"🎯 Target Types: Feature, User Story, Task, Test Case")
        print(f"🏢 Organization: {updater.organization}")
        print(f"📂 Project: {updater.project}")
        print()
        
        confirm = input("Do you want to proceed with updating work item paths? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Operation cancelled")
            return
        
        # Update work items
        print("\n🚀 Starting work item updates...")
        results = updater.update_all_work_items()
        
        # Display results
        print("\n📊 Update Results:")
        print("=" * 50)
        print(f"📈 Total Found: {results['total_found']}")
        print(f"✅ Updated: {results['updated']}")
        print(f"⏭️ Skipped: {results['skipped']}")
        print(f"❌ Failed: {results['failed']}")
        
        if results['details']:
            print("\n📋 Detailed Results:")
            for detail in results['details']:
                status_icon = {'updated': '✅', 'skipped': '⏭️', 'failed': '❌'}[detail['status']]
                print(f"{status_icon} {detail['type']} {detail['id']}: {detail['title']}")
                if detail['status'] == 'updated':
                    print(f"    Area: '{detail['old_area']}' -> '{detail['new_area']}'")
                    print(f"    Iteration: '{detail['old_iteration']}' -> '{detail['new_iteration']}'")
                elif detail['status'] == 'skipped':
                    print(f"    Reason: {detail.get('reason', 'unknown')}")
        
        # Save results to file
        results_file = f"output/path_update_results_{config.get_timestamp()}.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        if results['updated'] > 0:
            print("\n🎉 Work item paths updated successfully!")
            print("🔍 Check your Azure DevOps Backlog and Sprint views - work items should now be visible.")
        else:
            print("\n ℹ️ No work items needed updating.")
        
    except Exception as e:
        logger.error(f"Failed to update work item paths: {e}")
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
