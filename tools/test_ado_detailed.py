#!/usr/bin/env python3
"""
Detailed Azure DevOps integration test that creates an actual work item.
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator

def main():
    print("🔍 Testing Azure DevOps Work Item Creation...")
    
    # Load config
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    print(f"Organization: {integrator.organization}")
    print(f"Project: {integrator.project}")
    print(f"Enabled: {integrator.enabled}")
    
    if not integrator.enabled:
        print("❌ Integration not enabled")
        return
    
    # Test connection first
    print("\n🌐 Testing connection...")
    try:
        success = integrator.test_connection()
        if not success:
            print("❌ Connection failed")
            return
        print("✅ Connection successful!")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Test creating a simple Epic
    print("\n📝 Creating test Epic...")
    test_epic_data = {
        "title": "Test Epic - Agile Backlog Automation",
        "description": "This is a test epic created by the Agile Backlog Automation system to validate ADO integration.",
        "business_value": "Validate that the system can successfully create work items in Azure DevOps.",
        "priority": "Medium",
        "success_criteria": [
            "Epic is created successfully in ADO",
            "Epic has correct title and description",
            "Epic has proper business value assigned"
        ],
        "dependencies": [],
        "risks": []
    }
    
    try:
        epic_result = integrator._create_epic(test_epic_data)
        print(f"✅ Epic created successfully!")
        print(f"   ID: {epic_result['id']}")
        print(f"   Title: {epic_result['title']}")
        print(f"   URL: {epic_result['url']}")
        print(f"   State: {epic_result['state']}")
        
        # Try to retrieve the created work item
        print(f"\n🔍 Retrieving created Epic...")
        retrieved_epic = integrator.get_work_item(epic_result['id'])
        print(f"✅ Epic retrieved successfully!")
        print(f"   Title: {retrieved_epic['fields']['System.Title']}")
        print(f"   Work Item Type: {retrieved_epic['fields']['System.WorkItemType']}")
        print(f"   State: {retrieved_epic['fields']['System.State']}")
        
        # Test creating a Feature under the Epic
        print(f"\n📋 Creating test Feature under Epic...")
        test_feature_data = {
            "title": "Test Feature - Data Processing",
            "description": "A test feature to validate feature creation with parent linking.",
            "user_story": "As a user, I want to process data efficiently so that I can get quick results.",
            "priority": "High",
            "acceptance_criteria": [
                "Data processing is completed within 5 seconds",
                "Results are accurate and validated",
                "User receives confirmation of completion"
            ],
            "tasks": [],
            "test_cases": []
        }
        
        feature_result = integrator._create_feature(test_feature_data, epic_result['id'])
        print(f"✅ Feature created successfully!")
        print(f"   ID: {feature_result['id']}")
        print(f"   Title: {feature_result['title']}")
        print(f"   URL: {feature_result['url']}")
        print(f"   State: {feature_result['state']}")
        
        print(f"\n🎉 Full ADO integration test completed successfully!")
        print(f"Created Epic: {epic_result['id']} and Feature: {feature_result['id']}")
        print(f"You can view them in ADO at:")
        print(f"  Epic: {epic_result['url']}")
        print(f"  Feature: {feature_result['url']}")
        
    except Exception as e:
        print(f"❌ Work item creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
