#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix existing Azure DevOps work items that have \\n escaped newlines
in their descriptions and replace them with proper HTML formatting.
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

class WorkItemDescriptionFixer:
    def __init__(self):
        """Initialize the work item description fixer."""
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
        
        # Statistics
        self.items_checked = 0
        self.items_with_issues = 0
        self.items_fixed = 0
        self.items_failed = 0
    
    def query_work_items(self) -> List[int]:
        """Query all work items in the project."""
        print("Querying work items...")
        
        # WIQL query to get all work items (we'll filter descriptions later)
        wiql_query = {
            "query": f"""SELECT [System.Id], [System.Title], [System.WorkItemType] FROM WorkItems WHERE [System.TeamProject] = '{self.project}' ORDER BY [System.Id] DESC"""
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/wiql?api-version=7.1",
                headers=self.headers,
                json=wiql_query
            )
            
            if response.status_code != 200:
                print(f"Query failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return []
            
            result = response.json()
            work_item_ids = [item['id'] for item in result.get('workItems', [])]
            
            print(f"Found {len(work_item_ids)} work items total (will filter by description content later)")
            return work_item_ids
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to query work items: {e}")
            return []
    
    def get_work_item_details(self, work_item_ids: List[int]) -> List[Dict[str, Any]]:
        """Get detailed information for work items in batches."""
        print("📋 Fetching work item details...")
        
        work_items = []
        batch_size = 200  # Azure DevOps API limit
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            ids_param = ','.join(map(str, batch_ids))
            
            try:
                response = requests.get(
                    f"{self.base_url}/workitems?ids={ids_param}&fields=System.Id,System.Title,System.WorkItemType,System.Description&api-version=7.1",
                    headers=self.headers
                )
                response.raise_for_status()
                
                batch_items = response.json().get('value', [])
                work_items.extend(batch_items)
                print(f"📥 Fetched {len(batch_items)} items (batch {i//batch_size + 1})")
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Failed to fetch batch starting at {i}: {e}")
        
        print(f"📊 Total work items fetched: {len(work_items)}")
        return work_items
    
    def has_escaped_newlines(self, description: str) -> bool:
        """Check if description contains formatting issues that should be fixed."""
        if not description:
            return False
        
        # Skip if already HTML formatted
        if description.strip().startswith('<'):
            return False
        
        # Look for patterns that indicate missing line breaks:
        patterns = [
            r'\\n',  # Still has escaped newlines
            r'[a-zA-Z0-9.,;:!?]\s*\*\*[A-Z][^*]*\*\*',  # Text immediately followed by **Section**
            r'\*\*[^*]+\*\*:\s*-\s',  # **Section**: - (no line break before bullet)
            r'[a-zA-Z0-9.,;:!?]\s*-\s[A-Z]',  # Text immediately followed by - bullet
        ]
        
        for pattern in patterns:
            if re.search(pattern, description):
                return True
            
        return False
    
    def fix_description(self, description: str) -> str:
        """Fix formatting issues in description."""
        if not description:
            return description
        
        # Skip if already HTML formatted
        if description.strip().startswith('<'):
            return description
        
        # Start with the original description
        fixed_description = description
        
        # Step 1: Handle any remaining escaped newlines
        fixed_description = fixed_description.replace('\\n', '\n')
        
        # Step 2: Add two line breaks before any **Section Headers**
        # Find any text followed immediately by **Section** and add proper spacing
        fixed_description = re.sub(
            r'([a-zA-Z0-9.,;:!?])\s*(\*\*[^*]+\*\*:?)',
            r'\1\n\n\2',
            fixed_description
        )
        
        # Step 3: Add one line break before bullet points
        # Find any text followed immediately by "- " and add proper spacing
        fixed_description = re.sub(
            r'([a-zA-Z0-9.,;:!?\*])\s*(-\s)',
            r'\1\n\2',
            fixed_description
        )
        
        # Step 4: Clean up any excessive newlines (more than 2 consecutive)
        fixed_description = re.sub(r'\n{3,}', '\n\n', fixed_description)
        
        # Step 5: Convert to HTML format
        # Split into paragraphs (double newlines)
        paragraphs = fixed_description.split('\n\n')
        html_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Replace single newlines with <br> tags within paragraphs
                paragraph_html = paragraph.replace('\n', '<br>')
                html_paragraphs.append(f'<p>{paragraph_html}</p>')
        
        # Join paragraphs
        html_description = ''.join(html_paragraphs)
        
        # If we don't have any paragraphs, wrap the whole thing in a div
        if not html_paragraphs:
            html_description = f'<div>{fixed_description.replace("\n", "<br>")}</div>'
        
        return html_description
    
    def update_work_item(self, work_item_id: int, new_description: str) -> bool:
        """Update a work item's description."""
        patch_data = [
            {
                "op": "replace",
                "path": "/fields/System.Description",
                "value": new_description
            }
        ]
        
        try:
            response = requests.patch(
                f"{self.base_url}/workitems/{work_item_id}?api-version=7.1",
                headers=self.patch_headers,
                json=patch_data
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to update work item {work_item_id}: {e}")
            return False
    
    def process_work_items(self, dry_run: bool = True) -> None:
        """Process all work items and fix description formatting."""
        print("Starting work item description fix" + (" (DRY RUN)" if dry_run else " (LIVE UPDATE)"))
        print("="*70)
        
        # Get all work items
        work_item_ids = self.query_work_items()
        if not work_item_ids:
            print("No work items found or query failed")
            return
        
        # Get detailed information
        work_items = self.get_work_item_details(work_item_ids)
        if not work_items:
            print("Failed to fetch work item details")
            return
        
        print(f"\nProcessing {len(work_items)} work items...")
        print("-" * 70)
        
        for item in work_items:
            self.items_checked += 1
            work_item_id = item['id']
            title = item['fields'].get('System.Title', 'No Title')
            work_item_type = item['fields'].get('System.WorkItemType', 'Unknown')
            description = item['fields'].get('System.Description', '')
            
            # Check if this item needs fixing
            if not self.has_escaped_newlines(description):
                continue
            
            self.items_with_issues += 1
            
            print(f"\n🔍 Found issue in {work_item_type} #{work_item_id}: {title[:50]}...")
            
            # Show original description (truncated)
            original_preview = description.replace('\\n', '\\\\n')[:100]
            print(f"   📝 Original: {original_preview}...")
            
            # Fix the description
            fixed_description = self.fix_description(description)
            fixed_preview = fixed_description.replace('\n', '⏎')[:100]
            print(f"   ✅ Fixed:    {fixed_preview}...")
            
            if dry_run:
                print(f"   🔍 DRY RUN: Would update work item {work_item_id}")
                self.items_fixed += 1
            else:
                print(f"   🔄 Updating work item {work_item_id}...")
                if self.update_work_item(work_item_id, fixed_description):
                    print(f"   ✅ Successfully updated work item {work_item_id}")
                    self.items_fixed += 1
                else:
                    print(f"   ❌ Failed to update work item {work_item_id}")
                    self.items_failed += 1
        
        # Print summary
        print("\n" + "="*70)
        print("📊 SUMMARY:")
        print(f"   Items checked: {self.items_checked}")
        print(f"   Items with formatting issues: {self.items_with_issues}")
        print(f"   Items {'would be ' if dry_run else ''}fixed: {self.items_fixed}")
        if not dry_run:
            print(f"   Items failed to update: {self.items_failed}")
        
        if dry_run and self.items_with_issues > 0:
            print(f"\n🚀 Run with --live to actually update {self.items_with_issues} work items")
        elif not dry_run and self.items_fixed > 0:
            print(f"\n🎉 Successfully fixed {self.items_fixed} work item descriptions!")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix work item description formatting')
    parser.add_argument('--live', action='store_true', help='Actually update work items (default is dry run)')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt for live updates')
    
    args = parser.parse_args()
    
    try:
        fixer = WorkItemDescriptionFixer()
        
        if args.live and not args.confirm:
            print("⚠️  WARNING: This will modify work items in Azure DevOps!")
            print(f"   Organization: {fixer.organization}")
            print(f"   Project: {fixer.project}")
            
            response = input("\nDo you want to continue? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                print("❌ Operation cancelled")
                return
        
        fixer.process_work_items(dry_run=not args.live)
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
