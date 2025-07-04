from typing import Dict, Any
from config.config_loader import Config

class ProjectContext:
    """Manages project-specific context for prompt templates and agent behavior."""
    
    def __init__(self, config: Config):
        self.config = config
        self._context = self._load_default_context()
    
    def _load_default_context(self) -> Dict[str, Any]:
        """Load default context from configuration and environment."""
        return {
            # Project Information
            'project_name': self.config.settings.get('project', {}).get('name', 'Agile Project'),
            'domain': 'software development',
            'methodology': 'Agile/Scrum',
            
            # Technical Context
            'tech_stack': 'Modern Web Stack (React, Node.js, Python)',
            'architecture_pattern': 'Microservices',
            'database_type': 'PostgreSQL/MongoDB',
            'cloud_platform': 'AWS/Azure',
            'platform': 'Web Application with Mobile Support',
            
            # Team Context
            'team_size': '5-8 developers',
            'sprint_duration': '2 weeks',
            'experience_level': 'Senior',
            
            # Business Context
            'target_users': 'End users and administrators',
            'timeline': '6-12 months',
            'budget_constraints': 'Standard enterprise budget',
            'compliance_requirements': 'GDPR, SOC2',
            
            # Quality Context
            'test_environment': 'Automated CI/CD pipeline',
            'quality_standards': 'Industry best practices',
            'security_requirements': 'Enterprise security standards',
            
            # Integration Context
            'integrations': 'REST APIs, third-party services',
            'external_systems': 'CRM, Analytics, Payment systems'
        }
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update context with new values."""
        self._context.update(updates)
    
    def get_context(self, agent_type: str = None) -> Dict[str, Any]:
        """Get context appropriate for the specified agent type."""
        base_context = self._context.copy()
        
        # Add agent-specific context
        if agent_type == 'epic_strategist':
            base_context.update({
                'focus': 'business value and strategic alignment',
                'scope': 'high-level product roadmap'
            })
        elif agent_type == 'decomposition_agent':
            base_context.update({
                'focus': 'user experience and feature completeness',
                'scope': 'detailed feature specifications'
            })
        elif agent_type == 'developer_agent':
            base_context.update({
                'focus': 'technical implementation and architecture',
                'scope': 'development tasks and technical debt'
            })
        elif agent_type == 'qa_tester_agent':
            base_context.update({
                'focus': 'quality assurance and risk mitigation',
                'scope': 'comprehensive test coverage'
            })
        
        return base_context
    
    def set_project_type(self, project_type: str) -> None:
        """Set context for specific project types."""
        project_contexts = {
            'fintech': {
                'domain': 'financial technology',
                'compliance_requirements': 'PCI DSS, SOX, GDPR',
                'security_requirements': 'Banking-grade security',
                'target_users': 'Financial institution users',
                'integrations': 'Banking APIs, Payment processors'
            },
            'healthcare': {
                'domain': 'healthcare technology',
                'compliance_requirements': 'HIPAA, FDA, GDPR',
                'security_requirements': 'HIPAA-compliant security',
                'target_users': 'Healthcare providers and patients',
                'integrations': 'EHR systems, Medical devices'
            },
            'ecommerce': {
                'domain': 'e-commerce',
                'compliance_requirements': 'PCI DSS, GDPR, CCPA',
                'security_requirements': 'E-commerce security standards',
                'target_users': 'Online shoppers and merchants',
                'integrations': 'Payment gateways, Inventory systems'
            },
            'education': {
                'domain': 'educational technology',
                'compliance_requirements': 'FERPA, COPPA, GDPR',
                'security_requirements': 'Educational data protection',
                'target_users': 'Students, teachers, administrators',
                'integrations': 'LMS, Student information systems'
            },
            'mobile_app': {
                'platform': 'Mobile Application (iOS/Android)',
                'tech_stack': 'React Native/Flutter, Node.js backend',
                'target_users': 'Mobile app users',
                'integrations': 'Push notifications, App store APIs'
            },
            'saas': {
                'domain': 'Software as a Service',
                'architecture_pattern': 'Multi-tenant SaaS',
                'target_users': 'Business users and administrators',
                'integrations': 'CRM, Analytics, Billing systems'
            }
        }
        
        if project_type in project_contexts:
            self.update_context(project_contexts[project_type])
    
    def get_context_summary(self) -> str:
        """Get a formatted summary of current context."""
        summary = f"""
Project Context Summary:
========================
Project: {self._context['project_name']}
Domain: {self._context['domain']}
Platform: {self._context['platform']}
Technology: {self._context['tech_stack']}
Team: {self._context['team_size']} ({self._context['experience_level']} level)
Timeline: {self._context['timeline']}
Methodology: {self._context['methodology']}
"""
        return summary.strip()
