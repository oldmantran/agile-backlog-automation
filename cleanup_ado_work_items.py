#!/usr/bin/env python3
"""
Azure DevOps Work Item Cleanup Script

This script deletes all work items in specified area paths using the Azure DevOps API.
Particularly useful for cleaning up test cases and other work items that can't be 
bulk deleted through the ADO UI.

Usage:
    python cleanup_ado_work_items.py

Features:
- Queries work items by area path
- Shows preview of items to be deleted
- Supports dry-run mode for safety
- Handles all work item types (including test cases)
- Provides detailed logging and progress tracking
- Respects API rate limits
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from integrators.azure_devops_api import AzureDevOpsIntegrator
from config.config_loader import Config
from utils.logger import setup_logger

# Configure logging
logger = setup_logger(__name__)

class ADOWorkItemCleaner:
    """Handles Azure DevOps work item cleanup operations."""
    
    def __init__(self, ado_client: AzureDevOpsIntegrator):
        self.ado_client = ado_client
        self.deleted_count = 0
        self.error_count = 0
        self.deletion_log = []
        
    def find_work_items_by_area_paths(self, area_paths: List[str]) -> List[Dict[str, Any]]:
        """Find all work items in the specified area paths."""
        logger.info(f"Searching for work items in area paths: {area_paths}")
        
        all_work_items = []
        
        for area_path in area_paths:
            try:
                # Construct WIQL query to find all work items in this area path
                # Using UNDER operator to include all sub-areas
                query = f"""
                SELECT [System.Id], [System.WorkItemType], [System.Title], [System.AreaPath], [System.State]
                FROM WorkItems 
                WHERE [System.TeamProject] = @project
                AND [System.AreaPath] UNDER '{area_path}'
                ORDER BY [System.WorkItemType], [System.Id]
                """
                
                logger.info(f"Querying work items in area path: {area_path}")
                work_item_ids = self.ado_client.run_wiql(query)
                
                if work_item_ids:
                    logger.info(f"Found {len(work_item_ids)} work items in '{area_path}'")
                    
                    # Get detailed information for these work items
                    work_items = self.ado_client.get_work_item_details(work_item_ids)
                    
                    for wi in work_items:
                        all_work_items.append({
                            'id': wi['id'],
                            'type': wi['fields'].get('System.WorkItemType', 'Unknown'),
                            'title': wi['fields'].get('System.Title', 'No Title'),
                            'area_path': wi['fields'].get('System.AreaPath', 'Unknown'),
                            'state': wi['fields'].get('System.State', 'Unknown'),
                            'url': wi.get('url', '')
                        })
                else:
                    logger.info(f"No work items found in area path: {area_path}")
                    
            except Exception as e:
                logger.error(f"Error querying area path '{area_path}': {e}")
        
        return all_work_items
    
    def preview_deletion(self, work_items: List[Dict[str, Any]]) -> None:
        """Show a preview of what will be deleted."""
        if not work_items:
            print("❌ No work items found to delete.")
            return
            
        print(f"\n📋 DELETION PREVIEW")
        print("=" * 60)
        print(f"Total work items to delete: {len(work_items)}")
        
        # Group by work item type
        by_type = {}
        by_area = {}
        
        for wi in work_items:
            wi_type = wi['type']
            area_path = wi['area_path']
            
            if wi_type not in by_type:
                by_type[wi_type] = 0
            by_type[wi_type] += 1
            
            if area_path not in by_area:
                by_area[area_path] = 0
            by_area[area_path] += 1
        
        print(f"\n📊 Breakdown by Work Item Type:")
        for wi_type, count in sorted(by_type.items()):
            print(f"   {wi_type}: {count} items")
        
        print(f"\n📁 Breakdown by Area Path:")
        for area_path, count in sorted(by_area.items()):
            print(f"   {area_path}: {count} items")
        
        print(f"\n📝 First 10 items to be deleted:")
        for i, wi in enumerate(work_items[:10]):
            print(f"   {i+1:2d}. [{wi['type']}] ID {wi['id']}: {wi['title'][:50]}...")
            print(f"       Area: {wi['area_path']}")
        
        if len(work_items) > 10:
            print(f"   ... and {len(work_items) - 10} more items")
    
    def delete_work_items(self, work_items: List[Dict[str, Any]], dry_run: bool = True) -> bool:
        """Delete the specified work items."""
        if not work_items:
            print("❌ No work items to delete.")
            return True
        
        if dry_run:
            print(f"\n🧪 DRY RUN MODE - No actual deletions will occur")
            print(f"   Would delete {len(work_items)} work items")
            return True
        
        print(f"\n🗑️  STARTING DELETION of {len(work_items)} work items...")
        print("=" * 60)
        
        # Sort by ID to delete in order (often helpful for dependencies)
        work_items_sorted = sorted(work_items, key=lambda x: x['id'])
        
        self.deleted_count = 0
        self.error_count = 0
        start_time = time.time()
        
        for i, wi in enumerate(work_items_sorted, 1):
            try:
                print(f"[{i:3d}/{len(work_items)}] Deleting {wi['type']} {wi['id']}: {wi['title'][:40]}...")
                
                # Delete the work item
                success = self.ado_client.delete_work_item(wi['id'])
                
                if success:
                    self.deleted_count += 1
                    self.deletion_log.append({
                        'id': wi['id'],
                        'type': wi['type'],
                        'title': wi['title'],
                        'area_path': wi['area_path'],
                        'status': 'deleted',
                        'timestamp': datetime.now().isoformat()
                    })
                    print(f"   ✅ Successfully deleted")
                else:
                    self.error_count += 1
                    self.deletion_log.append({
                        'id': wi['id'],
                        'type': wi['type'],
                        'title': wi['title'],
                        'area_path': wi['area_path'],
                        'status': 'failed',
                        'timestamp': datetime.now().isoformat(),
                        'error': 'API returned failure'
                    })
                    print(f"   ❌ Failed to delete")
                
                # Rate limiting - pause between deletions
                time.sleep(0.5)
                
                # Progress update every 10 items
                if i % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"   Progress: {i}/{len(work_items)} ({i/len(work_items)*100:.1f}%) - Rate: {rate:.1f} items/sec")
                
            except Exception as e:
                self.error_count += 1
                error_msg = str(e)
                self.deletion_log.append({
                    'id': wi['id'],
                    'type': wi['type'],
                    'title': wi['title'],
                    'area_path': wi['area_path'],
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': error_msg
                })
                print(f"   ❌ Error deleting: {error_msg}")
                logger.error(f"Error deleting work item {wi['id']}: {e}")
        
        elapsed = time.time() - start_time
        print(f"\n📊 DELETION SUMMARY")
        print("=" * 30)
        print(f"Total processed: {len(work_items)}")
        print(f"Successfully deleted: {self.deleted_count}")
        print(f"Errors: {self.error_count}")
        print(f"Time elapsed: {elapsed:.1f} seconds")
        print(f"Average rate: {len(work_items)/elapsed:.1f} items/sec")
        
        return self.error_count == 0


def main():
    """Main cleanup function."""
    print("🧹 Azure DevOps Work Item Cleanup Tool")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Area paths to clean up
    AREA_PATHS_TO_CLEAN = [
        "Backlog Automation\\Grit",
        "Backlog Automation\\Data Visualization"
    ]
    
    print("🎯 Target Area Paths for Cleanup:")
    for area_path in AREA_PATHS_TO_CLEAN:
        print(f"   • {area_path}")
    print()
    
    try:
        # 1. Load configuration and connect to ADO
        print("📋 Step 1: Loading configuration...")
        config = Config()
        
        org = config.env.get('AZURE_DEVOPS_ORG')
        project = config.env.get('AZURE_DEVOPS_PROJECT')
        pat = config.env.get('AZURE_DEVOPS_PAT')
        
        if not all([org, project, pat]):
            print("❌ Missing Azure DevOps configuration in .env file")
            print("   Required: AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, AZURE_DEVOPS_PAT")
            return
        
        print(f"   ✅ Configuration loaded")
        print(f"   🏢 Organization: {org}")
        print(f"   📁 Project: {project}")
        
        # 2. Connect to Azure DevOps
        print("\n🔗 Step 2: Connecting to Azure DevOps...")
        
        org_url = f"https://dev.azure.com/{org}" if not org.startswith('https://') else org
        
        # Create a minimal ADO client for cleanup operations
        # We'll bypass the normal constructor to avoid area path creation
        class CleanupADOClient:
            def __init__(self, org_url, project, pat):
                self.organization = org_url.replace("https://dev.azure.com/", "")
                self.project = project
                self.pat = pat
                
                import urllib.parse
                self.project_encoded = urllib.parse.quote(self.project)
                self.project_base_url = f"https://dev.azure.com/{self.organization}/{self.project_encoded}/_apis"
                
                from requests.auth import HTTPBasicAuth
                self.auth = HTTPBasicAuth('', self.pat)
                self.headers = {
                    'Content-Type': 'application/json-patch+json',
                    'Accept': 'application/json'
                }
                
                self.logger = logger
            
            def run_wiql(self, wiql: str) -> List[int]:
                """Run a WIQL query and return work item IDs."""
                url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit/wiql?api-version=7.1-preview.2"
                
                data = {"query": wiql}
                
                response = requests.post(url, json=data, auth=self.auth)
                response.raise_for_status()
                result = response.json()
                
                return [int(item['id']) for item in result.get('workItems', [])]
            
            def get_work_item_details(self, work_item_ids: List[int]) -> List[Dict]:
                """Get detailed work item information."""
                if not work_item_ids:
                    return []
                
                # Process in batches of 200 (ADO limit)
                batch_size = 200
                all_work_items = []
                
                for i in range(0, len(work_item_ids), batch_size):
                    batch_ids = work_item_ids[i:i + batch_size]
                    ids_str = ','.join(map(str, batch_ids))
                    
                    url = f"{self.project_base_url}/wit/workitems"
                    params = {
                        'ids': ids_str,
                        'api-version': '7.0',
                        '$expand': 'all'
                    }
                    
                    response = requests.get(url, auth=self.auth, params=params)
                    response.raise_for_status()
                    
                    batch_result = response.json()
                    all_work_items.extend(batch_result.get('value', []))
                
                return all_work_items
            
            def delete_work_item(self, work_item_id: int) -> bool:
                """Delete a work item."""
                url = f"{self.project_base_url}/wit/workitems/{work_item_id}?api-version=7.0"
                
                try:
                    response = requests.delete(url, auth=self.auth)
                    
                    if response.status_code == 200:
                        return True
                    else:
                        self.logger.warning(f"Unexpected response code {response.status_code} for work item {work_item_id}")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"Failed to delete work item {work_item_id}: {e}")
                    return False
        
        # Test connection first
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Test with a simple WIQL query instead of project API
            test_url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.1-preview.2"
            test_data = {
                "query": "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project"
            }
            
            test_response = requests.post(test_url, json=test_data, auth=HTTPBasicAuth('', pat))
            
            if test_response.status_code == 200:
                result = test_response.json()
                work_item_count = len(result.get('workItems', []))
                print(f"   ✅ Connected to Azure DevOps successfully")
                print(f"   📊 Found {work_item_count} work items in project")
            else:
                print(f"   ❌ Failed to connect: {test_response.status_code}")
                print(f"   Response: {test_response.text[:200]}...")
                return
                
        except Exception as e:
            print(f"   ❌ Connection test failed: {e}")
            return
        
        # Create the cleanup client
        ado_client = CleanupADOClient(org_url, project, pat)
        
        print("   ✅ Connected to Azure DevOps")
        
        # 3. Initialize cleaner
        print("\n🧹 Step 3: Initializing cleanup tool...")
        cleaner = ADOWorkItemCleaner(ado_client)
        print("   ✅ Cleanup tool ready")
        
        # 4. Find work items to delete
        print(f"\n🔍 Step 4: Finding work items in target area paths...")
        work_items = cleaner.find_work_items_by_area_paths(AREA_PATHS_TO_CLEAN)
        
        if not work_items:
            print("✅ No work items found in the specified area paths.")
            print("   Nothing to clean up!")
            return
        
        # 5. Show preview
        cleaner.preview_deletion(work_items)
        
        # 6. Confirm deletion
        print(f"\n⚠️  WARNING: This will permanently delete {len(work_items)} work items!")
        print("   This action cannot be undone.")
        print()
        print("Options:")
        print("  1. 🧪 Dry run (show what would be deleted)")
        print("  2. 🗑️  Proceed with actual deletion")
        print("  3. ❌ Cancel")
        print()
        
        try:
            choice = input("Enter your choice (1, 2, or 3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Operation cancelled by user.")
            return
        
        if choice == '1':
            print("\n🧪 Running in dry-run mode...")
            cleaner.delete_work_items(work_items, dry_run=True)
            print("✅ Dry run completed. No work items were actually deleted.")
            
        elif choice == '2':
            print(f"\n⚠️  FINAL CONFIRMATION")
            print(f"   About to delete {len(work_items)} work items permanently.")
            try:
                confirm = input("Type 'DELETE' to confirm: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Operation cancelled by user.")
                return
                
            if confirm == 'DELETE':
                print("\n🗑️  Proceeding with deletion...")
                success = cleaner.delete_work_items(work_items, dry_run=False)
                
                # Save deletion log
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = f"output/ado_cleanup_log_{timestamp}.json"
                
                os.makedirs("output", exist_ok=True)
                with open(log_file, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'area_paths_cleaned': AREA_PATHS_TO_CLEAN,
                        'total_items': len(work_items),
                        'deleted_count': cleaner.deleted_count,
                        'error_count': cleaner.error_count,
                        'deletion_log': cleaner.deletion_log
                    }, f, indent=2)
                
                print(f"📄 Deletion log saved to: {log_file}")
                
                if success:
                    print("✅ Cleanup completed successfully!")
                else:
                    print("⚠️  Cleanup completed with some errors. Check the log for details.")
            else:
                print("❌ Confirmation not received. Operation cancelled.")
                
        else:
            print("❌ Operation cancelled.")
    
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Cleanup error: {e}")


if __name__ == "__main__":
    main()
