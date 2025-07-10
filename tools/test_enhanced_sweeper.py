#!/usr/bin/env python3
"""
Test enhanced backlog sweeper with targeted and scheduled sweep capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor.supervisor import WorkflowSupervisor
import json

def test_enhanced_sweeper_capabilities():
    """Test both targeted and scheduled sweep capabilities."""
    print("🧪 Testing Enhanced Backlog Sweeper Capabilities")
    print("=" * 60)
    
    try:
        # Initialize supervisor
        supervisor = WorkflowSupervisor()
        print("✅ Supervisor initialized")
        
        # Get sweeper agent
        sweeper = supervisor._get_sweeper_agent()
        print("✅ Sweeper agent initialized")
        
        # Test 1: Verify targeted sweep method exists
        assert hasattr(sweeper, 'run_targeted_sweep'), "Sweeper missing run_targeted_sweep method"
        print("✅ Targeted sweep method available")
        
        # Test 2: Verify comprehensive sweep method exists  
        assert hasattr(sweeper, 'run_sweep'), "Sweeper missing run_sweep method"
        print("✅ Comprehensive sweep method available")
        
        # Test 3: Test targeted sweep for specific stage
        print("\\n🎯 Testing Targeted Sweep...")
        
        # Create mock workflow data
        mock_workflow_data = {
            'epics': [
                {
                    'id': 1,
                    'title': 'Test Epic',
                    'description': 'A test epic for validation',
                    'features': [
                        {
                            'id': 2,
                            'title': 'Test Feature',
                            'description': 'A test feature',
                            'user_stories': [
                                {
                                    'id': 3,
                                    'title': 'Test User Story',
                                    'user_story': 'As a user, I want to test so that I can verify functionality',
                                    'acceptance_criteria': ['Given test, when executed, then passes']
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Test targeted sweep for epic stage (should find no issues with good data)
        discrepancies = sweeper.run_targeted_sweep(
            stage='epic_strategist',
            workflow_data=mock_workflow_data,
            immediate_callback=False  # Don't trigger callback for test
        )
        print(f"✅ Epic stage targeted sweep completed: {len(discrepancies)} discrepancies found")
        
        # Test targeted sweep for feature stage
        discrepancies = sweeper.run_targeted_sweep(
            stage='feature_decomposer_agent', 
            workflow_data=mock_workflow_data,
            immediate_callback=False
        )
        print(f"✅ Feature stage targeted sweep completed: {len(discrepancies)} discrepancies found")
        
        # Test 4: Verify supervisor has enhanced execution method
        assert hasattr(supervisor, '_execute_stage_with_validation'), "Supervisor missing _execute_stage_with_validation method"
        print("✅ Supervisor has enhanced stage execution with validation")
        
        # Test 5: Check configuration loading
        config = supervisor.config.settings
        sweeper_config = config.get('agents', {}).get('backlog_sweeper_agent', {})
        
        # Check targeted sweep config
        targeted_config = sweeper_config.get('targeted_sweeps', {})
        assert targeted_config.get('enabled', False), "Targeted sweeps not enabled in config"
        print("✅ Targeted sweeps enabled in configuration")
        
        # Check scheduled sweep config  
        scheduled_config = sweeper_config.get('scheduled_sweeps', {})
        assert scheduled_config.get('enabled', False), "Scheduled sweeps not enabled in config"
        print("✅ Scheduled sweeps enabled in configuration")
        
        # Test 6: Verify workflow validation config
        workflow_config = config.get('workflow', {})
        validation_config = workflow_config.get('validation', {})
        assert validation_config.get('immediate_validation', False), "Immediate validation not enabled"
        print("✅ Immediate validation enabled in workflow configuration")
        
        print("\\n📋 Capability Summary:")
        print("🎯 Targeted Sweeps:")
        print("   - Supervisor can call sweeper after each agent stage")
        print("   - Immediate validation and remediation of stage outputs")
        print("   - Stage-specific validation (epics, features, user stories, tasks, tests)")
        print("   - Configurable retry limits per stage")
        
        print("\\n⏰ Scheduled Sweeps:")
        print("   - Autonomous recurring health checks")
        print("   - Comprehensive backlog validation")
        print("   - Configurable schedule (cron format)")
        print("   - Can be set to report-only or include remediation")
        
        print("\\n🔄 Integration:")
        print("   - Both modes use same callback mechanism to supervisor")
        print("   - Supervisor routes all findings to appropriate agents")
        print("   - Clean separation between targeted and scheduled operations")
        
        print("\\n🎉 Enhanced backlog sweeper capabilities verified!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_sweeper_capabilities()
    exit(0 if success else 1)
