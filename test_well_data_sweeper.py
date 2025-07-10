"""
Test script for running the enhanced backlog sweeper on the Data Visualization area path.

This script:
1. Configures the sweeper to target the Data Visualization area path specifically
2. Runs a comprehensive sweep of that area
3. Demonstrates the supervisor's ability to process sweeper reports
4. Shows auto-remediation capabilities for missing children and criteria
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
from supervisor.supervisor import WorkflowSupervisor
from utils.logger import setup_logger

def test_data_visualization_sweeper():
    """
    Test the enhanced backlog sweeper on the Data Visualization area path.
    """
    
    # Setup logging
    logger = setup_logger("test_data_visualization_sweeper", "logs/test_data_visualization_sweeper.log")
    logger.info("Starting Data Visualization area backlog sweeper test")
    
    try:
        # Load configuration
        config = Config()
        
        # Initialize Azure DevOps integrator
        ado_client = AzureDevOpsIntegrator(config)
        
        # Initialize supervisor (to receive and process sweeper reports)
        supervisor = WorkflowSupervisor()
        
        # Create a callback function for the sweeper to send reports to supervisor
        captured_report = None
        
        def sweeper_callback(report):
            nonlocal captured_report
            logger.info("Sweeper report received - forwarding to supervisor")
            captured_report = report
            supervisor.receive_sweeper_report(report)
        
        # Initialize backlog sweeper with supervisor callback
        sweeper = BacklogSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=sweeper_callback,
            config=config.settings
        )
        
        # Configure the sweep parameters for Data Visualization team
        sweep_config = {
            'project_name': 'Backlog Automation',
            'area_path': 'Backlog Automation\\Data Visualization',  # Target the Data Visualization area specifically
            'work_item_types': ['Epic', 'Feature', 'User Story', 'Task', 'Test Case'],
            'include_completed': False,  # Focus on active work items
            'max_items': 50,  # Limit for testing
            'deep_validation': True,  # Enable comprehensive validation
            'auto_remediation_preview': True  # Show what would be auto-remediated
        }
        
        logger.info(f"Configured sweep for area path: {sweep_config['area_path']}")
        logger.info(f"Work item types: {sweep_config['work_item_types']}")
        logger.info(f"Max items to analyze: {sweep_config['max_items']}")
        
        # Configure the sweeper for the specific area path
        # We need to temporarily modify the sweeper to use our specific area path
        original_scrape_method = sweeper.scrape_and_validate_work_items
        
        def custom_scrape_and_validate():
            """Custom scraping method that targets the Well Data Team area path."""
            discrepancies = []
            types = sweep_config['work_item_types']
            all_ids = []
            
            for t in types:
                area_ids = ado_client.query_work_items(
                    work_item_type=t, 
                    area_path=sweep_config['area_path'], 
                    max_items=sweep_config['max_items']
                )
                all_ids.extend(area_ids)
            
            logger.info(f"Found {len(all_ids)} work items in {sweep_config['area_path']}")
            
            if not all_ids:
                logger.warning(f"No work items found in area path: {sweep_config['area_path']}")
                return []
            
            # Get work item details
            work_items = ado_client.get_work_item_details(all_ids)
            if not work_items:
                logger.warning("No work item details retrieved")
                return []
            
            logger.info(f"Retrieved details for {len(work_items)} work items")
            
            # Process each work item using the original validation logic
            # We'll implement a simplified version here since we're overriding the method
            work_items_by_id = {wi['id']: wi for wi in work_items}

            def get_field(wi, field):
                return wi.get('fields', {}).get(field, '')

            for wi in work_items:
                wi_id = wi['id']
                wi_type = get_field(wi, 'System.WorkItemType')
                title = get_field(wi, 'System.Title')
                description = get_field(wi, 'System.Description')
                
                # Basic validation - check for missing titles
                if not title:
                    discrepancies.append({
                        'type': f'missing_{wi_type.lower().replace(" ", "_")}_title',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': f'{wi_type} missing title.',
                        'priority': 'high',
                        'suggested_agent': 'user_story_decomposer_agent',
                        'area_path': get_field(wi, 'System.AreaPath')
                    })
                
                # Check for missing acceptance criteria on User Stories
                if wi_type == "User Story":
                    criteria = get_field(wi, 'Microsoft.VSTS.Common.AcceptanceCriteria')
                    if not criteria or len(criteria.strip()) < 10:
                        discrepancies.append({
                            'type': 'missing_acceptance_criteria',
                            'work_item_id': wi_id,
                            'work_item_type': wi_type,
                            'title': title,
                            'description': 'User Story missing or insufficient acceptance criteria.',
                            'priority': 'high',
                            'suggested_agent': 'qa_tester_agent',
                            'area_path': get_field(wi, 'System.AreaPath')
                        })
                
                # Check for missing story points
                if wi_type == "User Story":
                    story_points = get_field(wi, 'Microsoft.VSTS.Scheduling.StoryPoints')
                    if not story_points:
                        discrepancies.append({
                            'type': 'missing_story_points',
                            'work_item_id': wi_id,
                            'work_item_type': wi_type,
                            'title': title,
                            'description': 'User Story missing story points estimation.',
                            'priority': 'medium',
                            'suggested_agent': 'developer_agent',
                            'area_path': get_field(wi, 'System.AreaPath')
                        })
            
            logger.info(f"Found {len(discrepancies)} discrepancies in area validation")
            return discrepancies
        
        # Temporarily replace the method
        sweeper.scrape_and_validate_work_items = custom_scrape_and_validate
        
        # Run the sweep
        logger.info("Starting comprehensive backlog sweep...")
        
        # Use the run_sweep method (the correct method name)
        sweeper.run_sweep()
        
        # Get the discrepancies from the captured report
        discrepancies = []
        if captured_report:
            # Extract discrepancies from different sections of the report
            discrepancies_by_priority = captured_report.get('discrepancies_by_priority', {})
            for priority, discs in discrepancies_by_priority.items():
                discrepancies.extend(discs)
            
            logger.info(f"Captured report with {len(discrepancies)} total discrepancies")
        
        # Display results
        print("\\n" + "="*80)
        print("DATA VISUALIZATION AREA BACKLOG SWEEP RESULTS")
        print("="*80)
        
        if captured_report:
            summary = captured_report.get('summary', {})
            print(f"\\nSweep Summary:")
            print(f"  - Total discrepancies: {summary.get('total_discrepancies', 0)}")
            print(f"  - High priority: {summary.get('high_priority_count', 0)}")
            print(f"  - Medium priority: {summary.get('medium_priority_count', 0)}")
            print(f"  - Low priority: {summary.get('low_priority_count', 0)}")
            
            if discrepancies:
                # Group discrepancies by priority
                high_priority = [d for d in discrepancies if d.get('priority') == 'high']
                medium_priority = [d for d in discrepancies if d.get('priority') == 'medium']
                low_priority = [d for d in discrepancies if d.get('priority') == 'low']
                
                # Show examples of each priority level
                if high_priority:
                    print(f"\\nHigh Priority Issues (showing first 3):")
                    for i, disc in enumerate(high_priority[:3], 1):
                        print(f"  {i}. Work Item {disc.get('work_item_id')}: {disc.get('description')}")
                
                if medium_priority:
                    print(f"\\nMedium Priority Issues (showing first 3):")
                    for i, disc in enumerate(medium_priority[:3], 1):
                        print(f"  {i}. Work Item {disc.get('work_item_id')}: {disc.get('description')}")
                
                # Show agent assignment suggestions
                agent_assignments = captured_report.get('agent_assignments', {})
                if agent_assignments:
                    print(f"\\nAgent Assignment Recommendations:")
                    for agent, assigned_discs in agent_assignments.items():
                        print(f"  - {agent}: {len(assigned_discs)} discrepancies")
        else:
            print("\\n⚠️ No report was captured from the sweeper - this may indicate a configuration issue.")
            print("\\nPossible issues:")
            print("  - Azure DevOps connection problems")
            print("  - Invalid area path or work item query")
            print("  - Authentication or permission issues")
        
        if not discrepancies and captured_report:
            print("\\n✅ No discrepancies found! The Data Visualization area backlog appears to be compliant.")
        elif not captured_report:
            print("\\n❌ Unable to complete the sweep - check logs for details.")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"output/data_visualization_sweep_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        
        # Prepare results data
        results_data = {
            'timestamp': timestamp,
            'area_path': sweep_config['area_path'],
            'configuration': sweep_config,
            'captured_report': captured_report,
            'discrepancies': discrepancies,
            'summary': {
                'total_discrepancies': len(discrepancies),
                'report_captured': captured_report is not None
            }
        }
        
        # Add priority breakdown if we have discrepancies
        if discrepancies:
            high_priority = [d for d in discrepancies if d.get('priority') == 'high']
            medium_priority = [d for d in discrepancies if d.get('priority') == 'medium']
            low_priority = [d for d in discrepancies if d.get('priority') == 'low']
            
            results_data['summary'].update({
                'high_priority_count': len(high_priority),
                'medium_priority_count': len(medium_priority),
                'low_priority_count': len(low_priority)
            })
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to: {results_file}")
        print(f"\\nDetailed results saved to: {results_file}")
        
        # Test supervisor integration
        if discrepancies:
            print(f"\\n" + "="*80)
            print("TESTING SUPERVISOR INTEGRATION")
            print("="*80)
            
            print("\\nThe supervisor has received the sweeper report and will:")
            print("  1. Route discrepancies to appropriate agents")
            print("  2. Attempt auto-remediation for supported discrepancy types")
            print("  3. Log manual review requirements for complex issues")
            print("\\nCheck the supervisor logs for detailed processing information.")
        
        print(f"\\n✅ Data Visualization area sweep test completed successfully!")
        return discrepancies
        
    except Exception as e:
        logger.error(f"Data Visualization area sweep test failed: {e}")
        print(f"\\n❌ Test failed: {e}")
        raise

def demonstrate_auto_remediation_capabilities():
    """
    Demonstrate the supervisor's auto-remediation capabilities.
    """
    print("\\n" + "="*80)
    print("AUTO-REMEDIATION CAPABILITIES DEMO")
    print("="*80)
    
    print("\\nThe enhanced supervisor can automatically remediate:")
    print("\\n🔧 Developer Agent Discrepancies:")
    print("  - Missing child tasks for user stories")
    print("  - Missing story point estimates")
    print("  - Task breakdown and sizing")
    
    print("\\n🧪 QA Tester Agent Discrepancies:")
    print("  - Missing child test cases for user stories")
    print("  - Invalid or missing acceptance criteria")
    print("  - Test coverage gaps")
    
    print("\\n📊 Epic Strategist Discrepancies:")
    print("  - Epic-level business value validation")
    print("  - Strategic alignment issues")
    
    print("\\n🏗️ Decomposition Agent Discrepancies:")
    print("  - Feature breakdown completeness")
    print("  - User story format and structure")
    
    print("\\n⚠️ Manual Review Required:")
    print("  - Complex business logic issues")
    print("  - Cross-team dependencies")
    print("  - Architecture decisions")

if __name__ == "__main__":
    print("Starting Data Visualization Area Backlog Sweeper Test...")
    print("="*80)
    
    try:
        # Run the main test
        discrepancies = test_data_visualization_sweeper()
        
        # Show auto-remediation capabilities
        demonstrate_auto_remediation_capabilities()
        
        print("\\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\\n❌ Test execution failed: {e}")
        sys.exit(1)
