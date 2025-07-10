#!/usr/bin/env python3
"""
Test the modular prompt system and context integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from utils.project_context import ProjectContext
from utils.prompt_manager import prompt_manager

def test_prompt_system():
    """Test the modular prompt system with dynamic context."""
    print("🧪 Testing Modular Prompt System")
    print("=" * 50)
    
    # Test 1: List available templates
    print("\n1. Available Templates:")
    templates_info = prompt_manager.list_templates()
    for agent_name, info in templates_info.items():
        print(f"   ✅ {agent_name}: {len(info['required_variables'])} variables required")
        if info['required_variables']:
            print(f"      Required: {', '.join(info['required_variables'])}")
    
    # Test 2: Create project context
    print("\n2. Project Context Setup:")
    config = Config()
    project_context = ProjectContext(config)
    
    # Test different project types
    test_contexts = [
        ('fintech', {'project_name': 'PaymentPro', 'timeline': '8 months'}),
        ('healthcare', {'project_name': 'HealthTracker', 'team_size': '6-8 developers'}),
        ('ecommerce', {'project_name': 'ShopEasy', 'domain': 'retail e-commerce'})
    ]
    
    for project_type, custom_context in test_contexts:
        print(f"\n3. Testing {project_type.upper()} Project:")
        print("-" * 30)
        
        # Set project type
        project_context.set_project_type(project_type)
        project_context.update_context(custom_context)
        
        # Test each agent prompt
        for agent_name in ['epic_strategist', 'feature_decomposer_agent', 'user_story_decomposer_agent', 'developer_agent', 'qa_tester_agent']:
            try:
                context = project_context.get_context(agent_name)
                prompt = prompt_manager.get_prompt(agent_name, context)
                
                print(f"   ✅ {agent_name}: {len(prompt)} characters")
                
                # Show a snippet of the generated prompt
                lines = prompt.split('\n')[:5]
                snippet = '\n'.join(lines)
                print(f"      Preview: {snippet[:100]}...")
                
            except Exception as e:
                print(f"   ❌ {agent_name}: {e}")
    
    print("\n🎉 Prompt system test completed!")

def test_context_variables():
    """Test context variable substitution."""
    print("\n\n🔧 Testing Context Variable Substitution")
    print("=" * 50)
    
    config = Config()
    project_context = ProjectContext(config)
    
    # Test custom context
    custom_context = {
        'project_name': 'TestApp',
        'domain': 'AI-powered productivity',
        'tech_stack': 'Python, FastAPI, React',
        'target_users': 'knowledge workers',
        'timeline': '4 months'
    }
    
    project_context.update_context(custom_context)
    
    # Test variable substitution for epic strategist
    agent_context = project_context.get_context('epic_strategist')
    
    print("Context variables:")
    for key, value in agent_context.items():
        if isinstance(value, str) and len(value) < 50:
            print(f"   {key}: {value}")
    
    # Generate prompt and show substitutions
    try:
        prompt = prompt_manager.get_prompt('epic_strategist', agent_context)
        
        print(f"\nGenerated prompt contains:")
        for var_name in ['project_name', 'domain', 'target_users']:
            if custom_context[var_name] in prompt:
                print(f"   ✅ {var_name}: '{custom_context[var_name]}' found in prompt")
            else:
                print(f"   ❌ {var_name}: '{custom_context[var_name]}' NOT found in prompt")
    
    except Exception as e:
        print(f"❌ Error generating prompt: {e}")

if __name__ == "__main__":
    test_prompt_system()
    test_context_variables()
