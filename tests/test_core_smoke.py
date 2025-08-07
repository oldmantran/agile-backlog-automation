#!/usr/bin/env python3
"""
Core Smoke Tests - Critical Path Validation
These tests must ALWAYS pass. If any test fails, the application is broken.
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
from utils.project_context import ProjectContext


class TestCoreSmokeTests:
    """Critical path smoke tests that validate core functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        self.config = Config()
        self.test_vision = """
        Product Vision: AI-Powered Task Management Platform
        
        We are building an intelligent task management platform that helps teams 
        collaborate more effectively using AI-driven insights and automation.
        
        Key Features:
        - Smart task prioritization
        - Automated workflow suggestions  
        - Team collaboration tools
        - AI-powered analytics
        
        Target Users: Software development teams, project managers
        Platform: Web application with mobile support
        Domain: Technology/Productivity
        """
    
    def test_product_vision_context_flow(self):
        """CRITICAL: Test that product vision flows through the entire system."""
        # 1. Initialize supervisor (no Azure integration for smoke test)
        supervisor = WorkflowSupervisor(
            organization_url="",
            project="Test Project", 
            personal_access_token="",
            area_path="",
            iteration_path="",
            job_id="smoke_test_001",
            include_test_artifacts=False
        )
        
        # 2. Test project context can store and retrieve product vision
        supervisor.project_context.update_context({
            'product_vision': self.test_vision,
            'project_name': 'Test Project'
        })
        
        context = supervisor.project_context.get_context('user_story_decomposer_agent')
        
        # CRITICAL ASSERTIONS - These must never fail
        assert 'product_vision' in context, "product_vision must be in context"
        assert context['product_vision'] == self.test_vision, "product_vision must match input"
        assert len(context['product_vision']) > 100, "product_vision must not be empty"
        
        print("✅ SMOKE TEST PASSED: Product vision context flow working")
    
    def test_agent_prompt_generation(self):
        """CRITICAL: Test that agents can generate prompts with product vision."""
        from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
        
        try:
            # Initialize agent
            agent = UserStoryDecomposerAgent(self.config)
            
            # Test context with product vision
            test_context = {
                'product_vision': self.test_vision,
                'project_name': 'Test Project',
                'domain': 'technology',
                'platform': 'Web Application',
                'epic_context': 'Test epic context for user story decomposer'
            }
            
            # CRITICAL: This must not throw an exception
            prompt = agent.get_prompt(test_context)
            
            # CRITICAL ASSERTIONS
            assert len(prompt) > 500, "Generated prompt must be substantial"
            assert self.test_vision.replace('\n', ' ') in prompt.replace('\n', ' '), "Prompt must contain product vision"
            assert '${product_vision}' not in prompt, "Template variables must be resolved"
            
            print("✅ SMOKE TEST PASSED: Agent prompt generation working")
            
        except Exception as e:
            pytest.fail(f"CRITICAL FAILURE: Agent template processing broken: {e}")
    
    def test_template_variable_validation(self):
        """CRITICAL: Test that template validation doesn't break with empty initial context."""
        from utils.prompt_manager import prompt_manager
        
        # Test with empty context (like during agent initialization)
        empty_context = {}
        
        # This should not crash - template validation should be robust
        try:
            validation = prompt_manager.validate_template('user_story_decomposer')
            assert validation['valid'], f"Template validation failed: {validation.get('error')}"
            
            print("✅ SMOKE TEST PASSED: Template validation robust")
            
        except Exception as e:
            pytest.fail(f"CRITICAL FAILURE: Template validation broken: {e}")
    
    def test_workflow_initialization(self):
        """CRITICAL: Test that workflow can initialize without errors."""
        supervisor = WorkflowSupervisor(
            organization_url="",
            project="Smoke Test Project",
            personal_access_token="", 
            area_path="",
            iteration_path="",
            job_id="smoke_test_002",
            include_test_artifacts=False
        )
        
        # Test that we can prepare for workflow execution
        supervisor.workflow_data = {
            'product_vision': self.test_vision,
            'epics': [],
            'metadata': {}
        }
        
        supervisor.project_context.update_context({
            'product_vision': self.test_vision,
            'project_name': 'Smoke Test Project'
        })
        
        # CRITICAL: These must not fail
        assert supervisor.workflow_data['product_vision'] == self.test_vision
        assert supervisor.project_context.get_context()['product_vision'] == self.test_vision
        
        print("✅ SMOKE TEST PASSED: Workflow initialization working")


def run_smoke_tests():
    """Run smoke tests and return success/failure."""
    print("Running CRITICAL smoke tests...")
    print("=" * 60)
    
    try:
        # Run pytest on this file
        exit_code = pytest.main([__file__, "-v", "--tb=short"])
        
        if exit_code == 0:
            print("=" * 60)
            print("ALL SMOKE TESTS PASSED - Core functionality verified")
            return True
        else:
            print("=" * 60)
            print("SMOKE TESTS FAILED - Application has critical issues")
            return False
            
    except Exception as e:
        print(f"SMOKE TEST EXECUTION FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)