#!/usr/bin/env python3
"""
Test the corrected workflow: Backlog Sweeper → Supervisor → Agents
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_qa_architecture():
    """Test that QA architecture is properly set up"""
    print("🧪 Testing QA Architecture...")
    
    try:
        from config.config_loader import Config
        from agents.qa_lead_agent import QALeadAgent
        
        config = Config()
        qa_lead = QALeadAgent(config)
        
        # Verify QA Lead has correct methods for Backlog Sweeper tasks
        assert hasattr(qa_lead, 'correct_area_path_mismatch'), "Missing area path correction method"
        assert hasattr(qa_lead, 'assign_orphaned_test_case_to_suite'), "Missing orphaned test case assignment"
        assert hasattr(qa_lead, 'test_suite_agent'), "Missing test suite agent"
        
        print("✅ QA Lead Agent properly configured")
        return True
        
    except Exception as e:
        print(f"❌ QA Architecture test failed: {e}")
        return False

def test_supervisor_integration():
    """Test that supervisor uses QA Lead Agent"""
    print("🧪 Testing Supervisor Integration...")
    
    try:
        # Read supervisor file
        with open('supervisor/supervisor.py', 'r') as f:
            supervisor_content = f.read()
        
        # Check for correct imports and references
        assert 'from agents.qa_lead_agent import QALeadAgent' in supervisor_content, "Supervisor not importing QA Lead Agent"
        assert 'qa_lead_agent' in supervisor_content, "Supervisor not referencing qa_lead_agent"
        assert 'qa_tester_agent' not in supervisor_content, "Supervisor still has qa_tester_agent references"
        
        print("✅ Supervisor properly integrated with QA Lead Agent")
        return True
        
    except Exception as e:
        print(f"❌ Supervisor integration test failed: {e}")
        return False

def test_deprecated_files_removed():
    """Test that deprecated files are removed"""
    print("🧪 Testing Deprecated Files Removal...")
    
    qa_tester_py = os.path.exists('agents/qa_tester_agent.py')
    qa_tester_txt = os.path.exists('prompts/qa_tester_agent.txt')
    
    if qa_tester_py:
        print("❌ qa_tester_agent.py still exists")
        return False
    
    if qa_tester_txt:
        print("❌ qa_tester_agent.txt still exists")
        return False
    
    print("✅ Deprecated QA Tester Agent files properly removed")
    return True

def test_workflow_routing():
    """Test that Backlog Sweeper routes to Supervisor"""
    print("🧪 Testing Workflow Routing...")
    
    try:
        with open('prompts/backlog_sweeper_agent.txt', 'r') as f:
            content = f.read()
        
        # Check that actions route to supervisor
        assert 'Route to Supervisor:' in content, "Backlog Sweeper not routing to Supervisor"
        assert 'QA Lead Agent' in content, "Backlog Sweeper not mentioning QA Lead Agent"
        
        print("✅ Backlog Sweeper correctly routes to Supervisor")
        return True
        
    except Exception as e:
        print(f"❌ Workflow routing test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CORRECTED WORKFLOW ARCHITECTURE TEST")
    print("=" * 60)
    
    all_passed = True
    all_passed &= test_deprecated_files_removed()
    all_passed &= test_qa_architecture()
    all_passed &= test_supervisor_integration()
    all_passed &= test_workflow_routing()
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Corrected Workflow:")
        print("   Backlog Sweeper identifies issues")
        print("            ↓")
        print("   Routes to Supervisor with agent suggestions")
        print("            ↓")
        print("   Supervisor assigns work to appropriate agents:")
        print("   • QA Lead Agent (manages Test Plan/Suite/Case agents)")
        print("   • Developer Agent (story points, decomposition)")
        print("   • Epic Strategist (epic-level issues)")
        print("   • Future Scrum Master Agent (metrics)")
        print("\n⚰️  QA Tester Agent - DELETED")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
