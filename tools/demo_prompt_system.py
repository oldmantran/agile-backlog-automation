#!/usr/bin/env python3
"""
Demo script showcasing the modular prompt system with different project types.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from utils.project_context import ProjectContext
from utils.prompt_manager import prompt_manager

def demo_prompt_system():
    """Demonstrate the modular prompt system with different project types."""
    print("🚀 Modular Prompt System Demo")
    print("=" * 60)
    
    config = Config()
    project_context = ProjectContext(config)
    
    # Demo scenarios
    scenarios = [
        {
            'name': 'Fintech - Crypto Trading Platform',
            'project_type': 'fintech',
            'context': {
                'project_name': 'CryptoTrader Pro',
                'domain': 'cryptocurrency trading',
                'timeline': '8 months',
                'tech_stack': 'React, Node.js, WebSocket, Redis'
            }
        },
        {
            'name': 'Healthcare - Patient Management',
            'project_type': 'healthcare',
            'context': {
                'project_name': 'MedPortal',
                'domain': 'patient engagement',
                'timeline': '12 months',
                'tech_stack': 'Vue.js, Python Django, PostgreSQL'
            }
        },
        {
            'name': 'E-learning - Online Education',
            'project_type': 'education',
            'context': {
                'project_name': 'LearnHub',
                'domain': 'online education',
                'timeline': '6 months',
                'tech_stack': 'Next.js, Node.js, MongoDB'
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 50)
        
        # Reset and configure context
        project_context = ProjectContext(config)
        project_context.set_project_type(scenario['project_type'])
        project_context.update_context(scenario['context'])
        
        print("📋 Project Context:")
        print(f"   Type: {scenario['project_type']}")
        print(f"   Name: {scenario['context']['project_name']}")
        print(f"   Domain: {scenario['context']['domain']}")
        print(f"   Timeline: {scenario['context']['timeline']}")
        print(f"   Tech: {scenario['context']['tech_stack']}")
        
        # Show how each agent's prompt adapts
        print("\n🤖 Agent Prompt Adaptations:")
        
        agents = ['epic_strategist', 'feature_decomposer_agent', 'user_story_decomposer_agent', 'developer_agent', 'qa_tester_agent']
        for agent in agents:
            try:
                context = project_context.get_context(agent)
                prompt = prompt_manager.get_prompt(agent, context)
                
                # Extract key contextual elements from prompt
                key_terms = []
                if scenario['context']['project_name'].lower() in prompt.lower():
                    key_terms.append(f"✓ Project: {scenario['context']['project_name']}")
                if scenario['context']['domain'].lower() in prompt.lower():
                    key_terms.append(f"✓ Domain: {scenario['context']['domain']}")
                if scenario['context']['tech_stack'].lower() in prompt.lower():
                    key_terms.append(f"✓ Tech: {scenario['context']['tech_stack']}")
                
                # Check for compliance terms
                compliance_terms = ['PCI DSS', 'HIPAA', 'FERPA', 'GDPR', 'SOX']
                found_compliance = [term for term in compliance_terms if term in prompt]
                if found_compliance:
                    key_terms.append(f"✓ Compliance: {', '.join(found_compliance)}")
                
                print(f"   {agent.replace('_', ' ').title()}: {len(prompt)} chars")
                for term in key_terms[:3]:  # Show first 3 key terms
                    print(f"     {term}")
                    
            except Exception as e:
                print(f"   ❌ {agent}: {e}")
        
        # Show snippet of epic strategist prompt for this context
        try:
            epic_context = project_context.get_context('epic_strategist')
            epic_prompt = prompt_manager.get_prompt('epic_strategist', epic_context)
            
            print(f"\n📝 Epic Strategist Prompt Preview:")
            lines = epic_prompt.split('\n')
            for line in lines[:8]:  # Show first 8 lines
                if line.strip():
                    print(f"   {line}")
            print("   ...")
            
        except Exception as e:
            print(f"   ❌ Failed to generate preview: {e}")
    
    print(f"\n🎉 Demo completed! The system adapts prompts for:")
    print(f"   ✅ {len(scenarios)} different project types")
    print(f"   ✅ {len(agents)} specialized AI agents")
    print(f"   ✅ Domain-specific terminology and compliance")
    print(f"   ✅ Technology-aware recommendations")

def show_context_variables():
    """Show available context variables."""
    print("\n\n🔧 Available Context Variables")
    print("=" * 60)
    
    config = Config()
    project_context = ProjectContext(config)
    
    # Show default context
    default_context = project_context.get_context()
    
    categories = {
        'Project Info': ['project_name', 'domain', 'methodology'],
        'Technical': ['tech_stack', 'architecture_pattern', 'database_type', 'cloud_platform', 'platform'],
        'Team': ['team_size', 'sprint_duration', 'experience_level'],
        'Business': ['target_users', 'timeline', 'budget_constraints'],
        'Compliance': ['compliance_requirements', 'security_requirements'],
        'Quality': ['test_environment', 'quality_standards']
    }
    
    for category, variables in categories.items():
        print(f"\n{category}:")
        for var in variables:
            if var in default_context:
                value = default_context[var]
                if isinstance(value, str) and len(value) < 50:
                    print(f"   {var}: {value}")
                else:
                    print(f"   {var}: <complex value>")

if __name__ == "__main__":
    demo_prompt_system()
    show_context_variables()
