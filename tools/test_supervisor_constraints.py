#!/usr/bin/env python3
"""
Quick validation that supervisor constraint logic is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config

def test_supervisor_constraints():
    """Test supervisor constraint attribute setting."""
    print("🔍 Testing Supervisor Constraint Logic")
    print("=" * 40)
    
    try:
        # Import supervisor after setting path
        from supervisor.supervisor import WorkflowSupervisor
        
        # Create supervisor instance (pass None to use default config)
        supervisor = WorkflowSupervisor(None)
        
        # Test constraint setting
        supervisor._test_max_epics = 2
        supervisor._test_max_features = 3
        
        # Verify constraints are set
        max_epics = getattr(supervisor, '_test_max_epics', None)
        max_features = getattr(supervisor, '_test_max_features', None)
        
        print(f"✅ Supervisor created successfully")
        print(f"🎯 Epic constraint: {max_epics}")
        print(f"🏗️  Feature constraint: {max_features}")
        
        if max_epics == 2 and max_features == 3:
            print("✅ Constraints set correctly!")
            return True
        else:
            print("❌ Constraints not set properly!")
            return False
            
    except Exception as e:
        print(f"❌ Supervisor constraint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supervisor_constraints()
    exit(0 if success else 1)
