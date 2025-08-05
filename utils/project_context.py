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
            'domain': 'dynamic',  # Will be set dynamically based on vision analysis
            'product_vision': '',  # Will be set dynamically from project data
            'methodology': 'Agile/Scrum',
            
            # Technical Context
            'tech_stack': 'Modern technology stack',
            'architecture_pattern': 'Scalable architecture',
            'database_type': 'Appropriate database solution',
            'cloud_platform': 'Cloud platform',
            'platform': 'Digital platform',
            
            # Team Context
            'team_size': '5-8 developers',
            'sprint_duration': '2 weeks',
            'experience_level': 'Senior',
            
            # Business Context  
            'target_users': 'end users',
            'timeline': '3-6 months',
            'budget_constraints': 'Moderate budget',
            'compliance_requirements': 'Industry standards',
            
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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"DEBUG: ProjectContext.update_context called with keys: {list(updates.keys())}")
        if 'product_vision' in updates:
            vision_length = len(updates['product_vision']) if updates['product_vision'] else 0
            logger.info(f"DEBUG: Updating product_vision, length: {vision_length}")
            if vision_length > 0:
                logger.info(f"DEBUG: product_vision preview: '{updates['product_vision'][:100]}...'")
        
        self._context.update(updates)
        
        # Verify the update worked
        if 'product_vision' in updates:
            stored_vision = self._context.get('product_vision', '')
            stored_length = len(stored_vision) if stored_vision else 0
            logger.info(f"DEBUG: After update, stored product_vision length: {stored_length}")
            if stored_length != vision_length:
                logger.error(f"DEBUG: MISMATCH! Input length {vision_length} != stored length {stored_length}")
    
    def get_context(self, agent_type: str = None) -> Dict[str, Any]:
        """Get context appropriate for the specified agent type."""
        import logging
        logger = logging.getLogger(__name__)
        
        base_context = self._context.copy()
        
        # Debug logging
        logger.info(f"DEBUG: ProjectContext.get_context for {agent_type}")
        logger.info(f"DEBUG: Context keys in _context: {list(self._context.keys())}")
        if 'product_vision' in self._context:
            vision_length = len(self._context['product_vision']) if self._context['product_vision'] else 0
            logger.info(f"DEBUG: product_vision in _context, length: {vision_length}")
        else:
            logger.warning(f"DEBUG: product_vision NOT in _context for {agent_type}")
        
        # Add agent-specific context
        if agent_type == 'epic_strategist':
            base_context.update({
                'focus': 'business value and strategic alignment',
                'scope': 'high-level product roadmap'
            })
        elif agent_type in ['feature_decomposer_agent', 'user_story_decomposer_agent']:
            base_context.update({
                'focus': 'user experience and feature completeness',
                'scope': 'detailed feature specifications'
            })
        elif agent_type == 'developer_agent':
            base_context.update({
                'focus': 'technical implementation and architecture',
                'scope': 'development tasks and technical debt'
            })
        elif agent_type == 'qa_lead_agent':
            base_context.update({
                'focus': 'quality assurance and risk mitigation',
                'scope': 'comprehensive test coverage'
            })
        
        # Final verification
        logger.info(f"DEBUG: Final context keys being returned: {list(base_context.keys())}")
        if 'product_vision' in base_context:
            vision_length = len(base_context['product_vision']) if base_context['product_vision'] else 0
            logger.info(f"DEBUG: Returning product_vision, length: {vision_length}")
        else:
            logger.error(f"DEBUG: CRITICAL - product_vision NOT in final context for {agent_type}")
        
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
