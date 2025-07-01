#!/usr/bin/env python3
"""
Script to check what section headers exist in Azure DevOps work items
"""

import os
import re
import requests
import base64
import json
from typing import List, Dict, Any, Set
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SectionHeaderChecker:
    def __init__(self):
        """Initialize the section header checker."""
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
        
        self.base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit"
    
    def query_work_items(self) -> List[int]:
        """Query all work items in the project."""
        print("Querying work items...")
        
        # WIQL query to get all work items
        wiql_query = {
            "query": f"""SELECT [System.Id], [System.Title], [System.WorkItemType] FROM WorkItems WHERE [System.TeamProject] = '{self.project}' ORDER BY [System.Id] DESC"""
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
            print(f"Found {len(work_item_ids)} work items total")
            return work_item_ids
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying work items: {e}")
            return []
    
    def get_work_item_details(self, work_item_ids: List[int]) -> List[Dict[str, Any]]:
        """Get detailed information for work items in batches."""
        if not work_item_ids:
            return []
        
        all_work_items = []
        batch_size = 200  # Azure DevOps API limit
        
        print("🔄 Fetching work item details...")
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            
            ids_param = ','.join(map(str, batch_ids))
            
            try:
                response = requests.get(
                    f"{self.base_url}/workitems?ids={ids_param}&fields=System.Id,System.Title,System.WorkItemType,System.Description&api-version=7.1",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                work_items = data.get('value', [])
                all_work_items.extend(work_items)
                
                print(f"📄 Fetched {len(work_items)} items (batch {batch_number})")
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching work items batch {batch_number}: {e}")
                continue
        
        print(f"📊 Total work items fetched: {len(all_work_items)}")
        return all_work_items
    
    def find_section_headers(self, work_items: List[Dict[str, Any]]) -> Set[str]:
        """Find all section headers in work item descriptions."""
        section_headers = set()
        
        print("Processing work items to find section headers...")
        
        for item in work_items:
            fields = item.get('fields', {})
            description = fields.get('System.Description', '') or ''
            
            # Find all section headers (text between double asterisks)
            headers = re.findall(r'\*\*([^*]+)\*\*', description)
            for header in headers:
                section_headers.add(f'**{header.strip()}**')
        
        # Also check for specific headers that might be missed
        additional_headers_to_check = [
            "Technical Requirements",
            "Definition of Done", 
            "User Story",
            "Acceptance Criteria",
            "Business Value",
            "Dependencies", 
            "Risks",
            "Success Criteria"
        ]
        
        for item in work_items:
            fields = item.get('fields', {})
            description = fields.get('System.Description', '') or ''
            
            for header in additional_headers_to_check:
                # Check for both with and without colon
                if f"**{header}:**" in description:
                    section_headers.add(f"**{header}:**")
                elif f"**{header}**" in description:
                    section_headers.add(f"**{header}**")
        
        return section_headers
    
    def check_section_headers(self):
        """Main method to check section headers in work items."""
        try:
            # Get work item IDs
            work_item_ids = self.query_work_items()
            if not work_item_ids:
                print("No work items found.")
                return
            
            # Get work item details
            work_items = self.get_work_item_details(work_item_ids)
            if not work_items:
                print("No work item details found.")
                return
            
            # Find all section headers
            section_headers = self.find_section_headers(work_items)
            
            print("\n" + "="*60)
            print("🔍 ALL SECTION HEADERS FOUND IN WORK ITEMS:")
            print("="*60)
            
            if section_headers:
                for header in sorted(section_headers):
                    print(f"  {header}")
                print(f"\nTotal unique section headers: {len(section_headers)}")
            else:
                print("  No section headers found in work items.")
            
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"❌ Error during section header check: {e}")

def main():
    """Main entry point."""
    checker = SectionHeaderChecker()
    checker.check_section_headers()

if __name__ == "__main__":
    main()
