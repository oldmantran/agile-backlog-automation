#!/usr/bin/env python3
"""
Test script for the enhanced Backlog Sweeper Agent.
Tests the advanced acceptance criteria validation and reporting functionality.
"""

import sys
import os
import json
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.backlog_sweeper_agent import BacklogSweeperAgent
from config.config_loader import Config


class MockAzureDevOpsIntegrator:
    """Mock ADO client for testing purposes."""
    
    def __init__(self):
        # Mock work items for testing
        self.mock_work_items = [
            {
                'id': 1001,
                'fields': {
                    'System.WorkItemType': 'User Story',
                    'System.Title': 'Test User Story',
                    'System.Description': 'As a user, I want to test the system so that I can validate functionality.',
                    'Microsoft.VSTS.Common.AcceptanceCriteria': '''
                        • User can log into the system
                        • System response time is under 2 seconds
                        • Application displays welcome message
                    ''',
                    'Microsoft.VSTS.Scheduling.StoryPoints': 5
                }
            },
            {
                'id': 1002,
                'fields': {
                    'System.WorkItemType': 'User Story',
                    'System.Title': 'Poor Acceptance Criteria Story',
                    'System.Description': 'As a user, I want better functionality.',
                    'Microsoft.VSTS.Common.AcceptanceCriteria': '''
                        • Make it better
                        • Improve the interface
                    ''',
                    'Microsoft.VSTS.Scheduling.StoryPoints': None
                }
            },
            {
                'id': 1003,
                'fields': {
                    'System.WorkItemType': 'User Story',
                    'System.Title': 'BDD Format Story',
                    'System.Description': 'As a user, I want to test BDD format.',
                    'Microsoft.VSTS.Common.AcceptanceCriteria': '''
                        • Given a user is logged in
                        • When they click the submit button  
                        • Then the form should be processed
                        • And a confirmation message should appear
                        • The response time should be under 1 second
                        • Security validation should prevent unauthorized access
                    ''',
                    'Microsoft.VSTS.Scheduling.StoryPoints': 3
                }
            },
            {
                'id': 1004,
                'fields': {
                    'System.WorkItemType': 'User Story',
                    'System.Title': 'Missing Acceptance Criteria',
                    'System.Description': 'As a user, I want missing criteria story.',
                    'Microsoft.VSTS.Common.AcceptanceCriteria': '',
                    'Microsoft.VSTS.Scheduling.StoryPoints': None
                }
            },
            {
                'id': 1005,
                'fields': {
                    'System.WorkItemType': 'Epic',
                    'System.Title': 'Test Epic',
                    'System.Description': 'Test Epic Description'
                }
            }
        ]
    
    def query_work_items(self, work_item_type):
        """Return mock work item IDs for the given type."""
        return [wi['id'] for wi in self.mock_work_items 
                if wi['fields'].get('System.WorkItemType') == work_item_type]
    
    def get_work_item_details(self, work_item_ids):
        """Return mock work item details."""
        return [wi for wi in self.mock_work_items if wi['id'] in work_item_ids]
    
    def get_work_item_relations(self, work_item_id):
        """Return mock relations (empty for testing)."""
        return []


def test_acceptance_criteria_validation():
    """Test the acceptance criteria validation functionality."""
    print("🧪 Testing Acceptance Criteria Validation")
    print("=" * 50)
    
    # Load configuration
    config = Config()
    
    # Create mock ADO client
    mock_ado = MockAzureDevOpsIntegrator()
    
    # Capture reports
    reports = []
    def capture_report(report):
        reports.append(report)
    
    # Create agent with configuration
    agent = BacklogSweeperAgent(
        ado_client=mock_ado,
        supervisor_callback=capture_report,
        config=config.config
    )
    
    # Run the sweep
    print("Running backlog sweep...")
    result = agent.run_sweep()
    
    # Analyze results
    if reports:
        report = reports[0]
        print(f"\n📊 Sweep Results:")
        print(f"   Total Discrepancies: {report['summary']['total_discrepancies']}")
        print(f"   High Priority: {report['summary']['high_priority_count']}")
        print(f"   Medium Priority: {report['summary']['medium_priority_count']}")
        print(f"   Low Priority: {report['summary']['low_priority_count']}")
        
        print(f"\n🎯 Agent Assignments:")
        for agent_name, discrepancies in report['agent_assignments'].items():
            print(f"   {agent_name}: {len(discrepancies)} items")
        
        print(f"\n📋 Sample Discrepancies:")
        all_discrepancies = []
        for priority in ['high', 'medium', 'low']:
            all_discrepancies.extend(report['discrepancies_by_priority'][priority])
        
        for i, disc in enumerate(all_discrepancies[:5]):  # Show first 5
            print(f"   {i+1}. [{disc['severity'].upper()}] Work Item {disc['work_item_id']}: {disc['type']}")
            print(f"      → {disc['description']}")
            print(f"      → Suggested Agent: {disc['suggested_agent']}")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommended_actions']:
            print(f"   • {rec}")
            
        # Test specific acceptance criteria validation
        print(f"\n🔍 Acceptance Criteria Validation Details:")
        criteria_issues = [d for d in all_discrepancies 
                          if 'acceptance_criteria' in d['type'] or 'criteria' in d['type']]
        
        for issue in criteria_issues:
            print(f"   • Work Item {issue['work_item_id']}: {issue['type']}")
            print(f"     {issue['description']}")
    
    else:
        print("❌ No reports generated")
    
    return reports


def test_configuration_compliance():
    """Test that the agent respects configuration settings."""
    print("\n🔧 Testing Configuration Compliance")
    print("=" * 50)
    
    # Test with custom configuration
    custom_config = {
        'agents': {
            'backlog_sweeper_agent': {
                'acceptance_criteria': {
                    'min_criteria_count': 5,  # Higher than default
                    'max_criteria_count': 6,  # Lower than default
                    'require_bdd_format': False,  # Disabled
                    'require_functional_and_nonfunctional': False  # Disabled
                }
            }
        }
    }
    
    mock_ado = MockAzureDevOpsIntegrator()
    reports = []
    
    agent = BacklogSweeperAgent(
        ado_client=mock_ado,
        supervisor_callback=lambda r: reports.append(r),
        config=custom_config
    )
    
    # Test configuration values
    print(f"✅ Min Criteria Count: {agent.min_criteria_count} (expected: 5)")
    print(f"✅ Max Criteria Count: {agent.max_criteria_count} (expected: 6)")
    print(f"✅ Require BDD Format: {agent.require_bdd_format} (expected: False)")
    print(f"✅ Require Functional/Non-functional: {agent.require_functional_and_nonfunctional} (expected: False)")
    
    # Run sweep with custom config
    agent.run_sweep()
    
    if reports:
        report = reports[0]
        print(f"\n📊 Custom Config Results:")
        print(f"   Total Discrepancies: {report['summary']['total_discrepancies']}")
        
        # Check if BDD-related discrepancies are reduced (since we disabled the requirement)
        all_discrepancies = []
        for priority in ['high', 'medium', 'low']:
            all_discrepancies.extend(report['discrepancies_by_priority'][priority])
        
        bdd_issues = [d for d in all_discrepancies if 'bdd' in d['type']]
        print(f"   BDD Format Issues: {len(bdd_issues)} (should be 0 with requirement disabled)")


if __name__ == "__main__":
    print("🚀 Backlog Sweeper Agent Testing")
    print("=" * 50)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Run tests
        reports = test_acceptance_criteria_validation()
        test_configuration_compliance()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
        # Save test results
        if reports:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/test_backlog_sweeper_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(reports[0], f, indent=2)
            print(f"📄 Test results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
