"""
Test script for running the enhanced backlog sweeper on the Well Data Team area path.

This script:
1. Configures the sweeper to target the Well Data Team area path specifically
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

def test_well_data_team_sweeper():
    """
    Test the enhanced backlog sweeper on the Well Data Team area path.
    """
    
    # Setup logging
    logger = setup_logger("test_well_data_sweeper", "logs/test_well_data_sweeper.log")
    logger.info("Starting Well Data Team backlog sweeper test")
    
    try:
        # Load configuration
        config = Config()
        
        # Initialize Azure DevOps integrator
        ado_client = AzureDevOpsIntegrator(config)
        
        # Initialize supervisor (to receive and process sweeper reports)
        supervisor = WorkflowSupervisor()
        
        # Create a callback function for the sweeper to send reports to supervisor
        def sweeper_callback(report):
            logger.info("Sweeper report received - forwarding to supervisor")
            supervisor.receive_sweeper_report(report)
        
        # Initialize backlog sweeper with supervisor callback
        sweeper = BacklogSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=sweeper_callback,
            config=config.settings
        )
        
        # Configure the sweep parameters for Well Data Team
        sweep_config = {
            'project_name': 'Backlog Automation',
            'area_path': 'Backlog Automation\\Well Data Team',  # Target the Well Data Team specifically
            'work_item_types': ['Epic', 'Feature', 'User Story', 'Task', 'Test Case'],
            'include_completed': False,  # Focus on active work items
            'max_items': 50,  # Limit for testing
            'deep_validation': True,  # Enable comprehensive validation
            'auto_remediation_preview': True  # Show what would be auto-remediated
        }
        
        logger.info(f"Configured sweep for area path: {sweep_config['area_path']}")
        logger.info(f"Work item types: {sweep_config['work_item_types']}")
        logger.info(f"Max items to analyze: {sweep_config['max_items']}")
        
        # Run the sweep
        logger.info("Starting comprehensive backlog sweep...")
        
        # Use the sweep_backlog method with custom parameters
        discrepancies = sweeper.sweep_backlog(
            area_path=sweep_config['area_path'],
            work_item_types=sweep_config['work_item_types'],
            include_completed=sweep_config['include_completed'],
            max_items=sweep_config['max_items']
        )
        
        # Display results
        print("\\n" + "="*80)
        print("WELL DATA TEAM BACKLOG SWEEP RESULTS")
        print("="*80)
        
        if discrepancies:
            print(f"\\nFound {len(discrepancies)} total discrepancies")
            
            # Group discrepancies by priority
            high_priority = [d for d in discrepancies if d.get('priority') == 'high']
            medium_priority = [d for d in discrepancies if d.get('priority') == 'medium']
            low_priority = [d for d in discrepancies if d.get('priority') == 'low']
            
            print(f"Priority breakdown:")
            print(f"  - High Priority: {len(high_priority)}")
            print(f"  - Medium Priority: {len(medium_priority)}")
            print(f"  - Low Priority: {len(low_priority)}")
            
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
            agent_assignments = {}
            for disc in discrepancies:
                agent = disc.get('suggested_agent', 'unknown')
                if agent not in agent_assignments:
                    agent_assignments[agent] = []
                agent_assignments[agent].append(disc)
            
            print(f"\\nAgent Assignment Recommendations:")
            for agent, assigned_discs in agent_assignments.items():
                print(f"  - {agent}: {len(assigned_discs)} discrepancies")
            
        else:
            print("\\n✅ No discrepancies found! The Well Data Team backlog appears to be compliant.")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"output/well_data_team_sweep_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'area_path': sweep_config['area_path'],
                'configuration': sweep_config,
                'discrepancies': discrepancies,
                'summary': {
                    'total_discrepancies': len(discrepancies) if discrepancies else 0,
                    'high_priority_count': len(high_priority) if 'high_priority' in locals() else 0,
                    'medium_priority_count': len(medium_priority) if 'medium_priority' in locals() else 0,
                    'low_priority_count': len(low_priority) if 'low_priority' in locals() else 0,
                    'agent_assignments': {agent: len(discs) for agent, discs in agent_assignments.items()} if 'agent_assignments' in locals() else {}
                }
            }, f, indent=2, default=str)
        
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
        
        print(f"\\n✅ Well Data Team sweep test completed successfully!")
        return discrepancies
        
    except Exception as e:
        logger.error(f"Well Data Team sweep test failed: {e}")
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
    print("Starting Well Data Team Backlog Sweeper Test...")
    print("="*80)
    
    try:
        # Run the main test
        discrepancies = test_well_data_team_sweeper()
        
        # Show auto-remediation capabilities
        demonstrate_auto_remediation_capabilities()
        
        print("\\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\\n❌ Test execution failed: {e}")
        sys.exit(1)
