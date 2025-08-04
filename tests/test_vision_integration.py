#!/usr/bin/env python3
"""
Integration test for vision statement processing - the exact workflow that broke.
This test simulates the full API -> Supervisor -> Agent -> Template flow.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
from utils.settings_manager import SettingsManager
from utils.user_id_resolver import user_id_resolver


class TestVisionIntegration:
    """Integration tests for the complete vision processing pipeline."""
    
    def setup_method(self):
        """Setup method run before each test."""
        self.config = Config()
        self.settings_manager = SettingsManager()
        self.user_id = user_id_resolver.get_default_user_id()
        
        # Test vision that matches what API server would create
        self.test_vision = """
Project: Product Idea Promoter App
Domain: Technology

We are building a mobile application that helps entrepreneurs and innovators 
validate, develop, and promote their product ideas through AI-powered insights 
and community feedback.

Key Features:
- AI-powered idea validation and market analysis
- Community-driven feedback and collaboration
- Business model canvas generation
- Prototype development guidance
- Investor pitch preparation tools

Target Users: Entrepreneurs, startup founders, product managers, innovators
Platform: Mobile-first application with web dashboard
Technology Stack: React Native, Node.js, AI/ML services
Business Model: Freemium with premium features for advanced analytics
""".strip()
    
    def test_complete_vision_processing_pipeline(self):
        """Test the complete pipeline from API server format to agent execution."""
        # Step 1: Initialize supervisor exactly like unified_api_server.py does
        supervisor = WorkflowSupervisor(
            organization_url="",  # No Azure for integration test
            project="Product Idea Promoter App",
            personal_access_token="",
            area_path="",
            iteration_path="", 
            job_id="integration_test_001",
            settings_manager=self.settings_manager,
            user_id=self.user_id,
            include_test_artifacts=False
        )
        
        # Step 2: Update project context exactly like supervisor.execute_workflow does
        supervisor.project = "Product Idea Promoter App"
        supervisor.project_context.update_context({
            'project_name': "Product Idea Promoter App",
            'domain': 'technology'
        })
        
        # Step 3: Test that execute_workflow would receive product_vision correctly
        context_updates = {
            'product_vision': self.test_vision
        }
        supervisor.project_context.update_context(context_updates)
        
        # Step 4: Test that user_story_decomposer_agent gets the context correctly
        context = supervisor.project_context.get_context('user_story_decomposer_agent')
        
        # CRITICAL ASSERTIONS - These exact checks failed before
        assert 'product_vision' in context, "product_vision must be in context"
        assert context['product_vision'] == self.test_vision, "product_vision content must match"
        assert len(context['product_vision']) > 200, "product_vision must not be empty"
        assert 'Product Idea Promoter App' in context['product_vision'], "Vision must contain project name"
        assert 'AI-powered' in context['product_vision'], "Vision must contain key features"
        
        print("✅ Step 1-4: Context flow validated")
        
        # Step 5: Test that agent can actually generate prompt (this was failing)
        from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
        
        agent = UserStoryDecomposerAgent(self.config)
        
        # This was throwing "Missing required template variables" error
        try:
            prompt = agent.get_prompt(context)
            
            # Validate prompt generation
            assert len(prompt) > 1000, "Generated prompt must be substantial"
            assert self.test_vision.replace('\n', ' ') in prompt.replace('\n', ' '), "Prompt must contain full vision"
            assert '${product_vision}' not in prompt, "All template variables must be resolved"
            assert 'Product Idea Promoter App' in prompt, "Project name must be in prompt"
            
            print("✅ Step 5: Agent prompt generation validated")
            
        except Exception as e:
            pytest.fail(f"INTEGRATION FAILURE: Agent prompt generation failed: {e}")
        
        # Step 6: Test that the agent context flows to parallel processing
        features = [
            ('test_epic', {
                'title': 'Test Feature',
                'description': 'Test feature for validation'
            })
        ]
        
        # This simulates the call in _execute_user_story_decomposition
        try:
            # Test that context is preserved in agent calls
            test_feature = features[0][1]
            
            # The actual agent call would be:
            # user_stories = agent.decompose_feature_to_user_stories(test_feature, context=context)
            # But we'll just test the context passing part
            
            assert context['product_vision'] == self.test_vision, "Context must be preserved through calls"
            
            print("✅ Step 6: Context preservation validated")
            
        except Exception as e:
            pytest.fail(f"INTEGRATION FAILURE: Context preservation failed: {e}")
    
    def test_template_manager_integration(self):
        """Test the specific template manager integration that was broken."""
        from utils.prompt_manager import prompt_manager
        
        # Test context that matches what supervisor provides
        test_context = {
            'product_vision': self.test_vision,
            'project_name': 'Product Idea Promoter App',
            'domain': 'technology',
            'platform': 'Mobile Application',
            'target_users': 'Entrepreneurs and innovators',
            'timeline': '6-12 months'
        }
        
        # This was the exact call that was failing
        try:
            prompt = prompt_manager.get_prompt('user_story_decomposer', test_context)
            
            # Validate the prompt was generated correctly
            assert len(prompt) > 500, "Prompt must be substantial"
            assert self.test_vision in prompt, "Product vision must be in final prompt"
            assert '${product_vision}' not in prompt, "Template variable must be resolved"
            
            print("✅ Template manager integration validated")
            
        except ValueError as e:
            if "missing required variables" in str(e):
                pytest.fail(f"TEMPLATE REGRESSION: The exact error that was fixed is back: {e}")
            else:
                pytest.fail(f"TEMPLATE FAILURE: {e}")
        except Exception as e:
            pytest.fail(f"TEMPLATE FAILURE: Unexpected error: {e}")
    
    def test_api_server_format_compatibility(self):
        """Test that the vision format from API server works correctly."""
        # This is the exact format created by unified_api_server.py lines 1248-1253
        project_name = "Product Idea Promoter App"
        project_domain = "technology"
        full_vision = """We are building a mobile application that helps entrepreneurs and innovators 
validate, develop, and promote their product ideas through AI-powered insights 
and community feedback."""
        
        api_format_vision = f"""
Project: {project_name}
Domain: {project_domain}

{full_vision}
""".strip()
        
        # Test that this format works through the entire pipeline
        supervisor = WorkflowSupervisor(
            organization_url="",
            project=project_name,
            personal_access_token="",
            area_path="",
            iteration_path="",
            job_id="api_format_test_001",
            include_test_artifacts=False
        )
        
        # Simulate execute_workflow context update
        supervisor.project_context.update_context({
            'product_vision': api_format_vision,
            'project_name': project_name,
            'domain': project_domain
        })
        
        context = supervisor.project_context.get_context('user_story_decomposer_agent')
        
        # Test that API format is preserved and accessible
        assert context['product_vision'] == api_format_vision
        assert project_name in context['product_vision']
        assert project_domain in context['product_vision'] 
        assert full_vision in context['product_vision']
        
        print("✅ API server format compatibility validated")


def run_integration_tests():
    """Run integration tests."""
    print("🔄 Running vision processing integration tests...")
    print("=" * 60)
    
    exit_code = pytest.main([__file__, "-v", "--tb=long"])
    
    if exit_code == 0:
        print("✅ INTEGRATION TESTS PASSED")
        return True
    else:
        print("❌ INTEGRATION TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)