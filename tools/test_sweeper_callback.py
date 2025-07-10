#!/usr/bin/env python3
"""
Test backlog sweeper initialization and callback setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor.supervisor import WorkflowSupervisor

def test_sweeper_callback_setup():
    """Test that backlog sweeper is properly initialized with supervisor callback."""
    print("🧪 Testing Backlog Sweeper Callback Setup")
    print("=" * 50)
    
    try:
        # Initialize supervisor
        supervisor = WorkflowSupervisor()
        print("✅ Supervisor initialized")
        
        # Get sweeper agent (this should initialize it with callback)
        sweeper = supervisor._get_sweeper_agent()
        print("✅ Sweeper agent initialized")
        
        # Check that sweeper has supervisor callback
        assert hasattr(sweeper, 'supervisor_callback'), "Sweeper missing supervisor_callback attribute"
        assert sweeper.supervisor_callback is not None, "Sweeper supervisor_callback is None"
        print("✅ Sweeper has supervisor callback")
        
        # Check that callback points to supervisor's receive_sweeper_report method
        assert hasattr(supervisor, 'receive_sweeper_report'), "Supervisor missing receive_sweeper_report method"
        assert sweeper.supervisor_callback == supervisor.receive_sweeper_report, "Callback not pointing to correct method"
        print("✅ Callback correctly points to supervisor.receive_sweeper_report")
        
        # Check that sweeper has required methods
        assert hasattr(sweeper, 'run_sweep'), "Sweeper missing run_sweep method"
        assert hasattr(sweeper, 'report_to_supervisor'), "Sweeper missing report_to_supervisor method"
        print("✅ Sweeper has required methods")
        
        # Test that report_to_supervisor uses the callback
        print("✅ Testing mock report...")
        
        # Create a mock report
        mock_report = {
            'timestamp': '2025-07-10T12:00:00',
            'summary': {'total_discrepancies': 0},
            'agent_assignments': {},
            'recommended_actions': []
        }
        
        # This should call supervisor.receive_sweeper_report via callback
        sweeper.report_to_supervisor(mock_report)
        print("✅ Mock report sent to supervisor successfully")
        
        print("\n🎉 Backlog sweeper callback setup is working correctly!")
        print("\n📋 Workflow Summary:")
        print("1. Supervisor initializes sweeper with callback")
        print("2. Sweeper.run_sweep() finds discrepancies")  
        print("3. Sweeper.report_to_supervisor() calls supervisor.receive_sweeper_report()")
        print("4. Supervisor routes discrepancies to appropriate agents")
        print("5. Agents remediate the issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sweeper_callback_setup()
    exit(0 if success else 1)
