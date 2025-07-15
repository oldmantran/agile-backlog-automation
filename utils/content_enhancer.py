"""
Content Enhancement Utility

This module provides tools for enhancing generated content to be more specific,
actionable, and valuable. It integrates with the quality validation system
to automatically improve content quality.
"""

from typing import Dict, List, Any, Tuple
import re
from utils.quality_validator import QualityValidator


class ContentEnhancer:
    """Enhances generated content for better specificity and actionability."""
    
    def __init__(self):
        self.quality_validator = QualityValidator()
        
        # Domain-specific terminology and patterns
        self.domain_patterns = {
            'web': {
                'ui_elements': ['button', 'form', 'dropdown', 'modal', 'page', 'component'],
                'actions': ['click', 'submit', 'navigate', 'validate', 'display'],
                'metrics': ['page load time', 'response time', 'conversion rate', 'bounce rate']
            },
            'mobile': {
                'ui_elements': ['screen', 'gesture', 'notification', 'permission', 'device'],
                'actions': ['tap', 'swipe', 'scroll', 'rotate', 'authenticate'],
                'metrics': ['app launch time', 'crash rate', 'user session length']
            },
            'api': {
                'ui_elements': ['endpoint', 'request', 'response', 'parameter', 'header'],
                'actions': ['call', 'authenticate', 'validate', 'transform', 'route'],
                'metrics': ['response time', 'throughput', 'error rate', 'availability']
            },
            'saas': {
                'ui_elements': ['dashboard', 'workspace', 'tenant', 'subscription', 'usage'],
                'actions': ['provision', 'configure', 'monitor', 'scale', 'backup'],
                'metrics': ['uptime', 'user adoption', 'feature usage', 'churn rate']
            }
        }
    
    def enhance_epic_content(self, epic: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
        """
        Enhance epic content for better specificity and business value.
        
        Args:
            epic: Epic dictionary with title, description, business_value, etc.
            context: Additional context (domain, project_name, etc.)
        
        Returns:
            Enhanced epic dictionary
        """
        enhanced_epic = epic.copy()
        
        # Enhance title
        if 'title' in enhanced_epic:
            enhanced_epic['title'] = self._enhance_title(
                enhanced_epic['title'], 'epic', context
            )
        
        # Enhance description
        if 'description' in enhanced_epic:
            enhanced_epic['description'] = self._enhance_description(
                enhanced_epic['description'], 'epic', context
            )
        
        # Enhance business value
        if 'business_value' in enhanced_epic:
            enhanced_epic['business_value'] = self.quality_validator.enhance_business_value(
                enhanced_epic['business_value'], context
            )
        
        # Enhance success criteria
        if 'success_criteria' in enhanced_epic:
            enhanced_epic['success_criteria'] = self._enhance_criteria_list(
                enhanced_epic['success_criteria'], context
            )
        
        return enhanced_epic
    
    def enhance_feature_content(self, feature: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
        """
        Enhance feature content for better specificity and clarity.
        
        Args:
            feature: Feature dictionary
            context: Additional context
        
        Returns:
            Enhanced feature dictionary
        """
        enhanced_feature = feature.copy()
        
        # Enhance title
        if 'title' in enhanced_feature:
            enhanced_feature['title'] = self._enhance_title(
                enhanced_feature['title'], 'feature', context
            )
        
        # Enhance description
        if 'description' in enhanced_feature:
            enhanced_feature['description'] = self._enhance_description(
                enhanced_feature['description'], 'feature', context
            )
        
        # Enhance acceptance criteria
        if 'acceptance_criteria' in enhanced_feature:
            enhanced_feature['acceptance_criteria'] = self._enhance_criteria_list(
                enhanced_feature['acceptance_criteria'], context
            )
        
        return enhanced_feature
    
    def enhance_user_story_content(self, user_story: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
        """
        Enhance user story content for better specificity and testability.
        
        Args:
            user_story: User story dictionary
            context: Additional context
        
        Returns:
            Enhanced user story dictionary
        """
        enhanced_story = user_story.copy()
        
        # Enhance title
        if 'title' in enhanced_story:
            enhanced_story['title'] = self._enhance_title(
                enhanced_story['title'], 'user_story', context
            )
        
        # Enhance user story statement
        if 'user_story' in enhanced_story:
            enhanced_story['user_story'] = self._enhance_user_story_statement(
                enhanced_story['user_story'], context
            )
        
        # Enhance description
        if 'description' in enhanced_story:
            enhanced_story['description'] = self._enhance_description(
                enhanced_story['description'], 'user_story', context
            )
        
        # Enhance acceptance criteria
        if 'acceptance_criteria' in enhanced_story:
            enhanced_story['acceptance_criteria'] = self._enhance_criteria_list(
                enhanced_story['acceptance_criteria'], context
            )
        
        return enhanced_story
    
    def enhance_task_content(self, task: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
        """
        Enhance task content for better actionability and clarity.
        
        Args:
            task: Task dictionary
            context: Additional context
        
        Returns:
            Enhanced task dictionary
        """
        enhanced_task = task.copy()
        
        # Enhance title
        if 'title' in enhanced_task:
            enhanced_task['title'] = self._enhance_title(
                enhanced_task['title'], 'task', context
            )
        
        # Enhance description
        if 'description' in enhanced_task:
            enhanced_task['description'] = self._enhance_description(
                enhanced_task['description'], 'task', context
            )
        
        # Add specific implementation details if missing
        if 'implementation_details' not in enhanced_task and context:
            enhanced_task['implementation_details'] = self._generate_implementation_details(
                enhanced_task, context
            )
        
        return enhanced_task
    
    def _enhance_title(self, title: str, item_type: str, context: Dict = None) -> str:
        """Enhance title for better specificity."""
        enhanced = title
        
        # Add domain-specific context if available
        if context and 'domain' in context:
            domain = context['domain'].lower()
            if domain in self.domain_patterns:
                # Add domain-specific terminology if missing
                patterns = self.domain_patterns[domain]
                if not any(element in enhanced.lower() for element in patterns['ui_elements']):
                    # Add appropriate domain context
                    if item_type == 'epic':
                        enhanced = f"{enhanced} ({domain.capitalize()} Platform)"
                    elif item_type == 'feature':
                        enhanced = f"{enhanced} Feature"
        
        return enhanced
    
    def _enhance_description(self, description: str, item_type: str, context: Dict = None) -> str:
        """Enhance description for better specificity."""
        enhanced = self.quality_validator.enhance_content_specificity(
            description, 'description', context
        )
        
        # Add domain-specific enhancements
        if context and 'domain' in context:
            domain = context['domain'].lower()
            if domain in self.domain_patterns:
                patterns = self.domain_patterns[domain]
                
                # Add specific action words if missing
                if not any(action in enhanced.lower() for action in patterns['actions']):
                    # Suggest adding appropriate actions
                    if item_type in ['user_story', 'task']:
                        enhanced += f" The implementation should include {patterns['actions'][0]} functionality."
        
        return enhanced
    
    def _enhance_user_story_statement(self, user_story: str, context: Dict = None) -> str:
        """Enhance user story statement for better clarity."""
        enhanced = user_story
        
        # Ensure proper user story format
        if not enhanced.startswith('As a'):
            enhanced = f"As a user, I want to {enhanced.lower()}"
        
        # Add specific user types if too generic
        if 'As a user' in enhanced and context:
            if 'target_users' in context and context['target_users'] != 'users':
                enhanced = enhanced.replace('As a user', f"As a {context['target_users']}")
        
        # Ensure "so that" clause exists
        if 'so that' not in enhanced.lower():
            enhanced += " so that I can accomplish my goal effectively"
        
        return enhanced
    
    def _enhance_criteria_list(self, criteria: List[str], context: Dict = None) -> List[str]:
        """Enhance list of criteria for better testability."""
        enhanced_criteria = []
        
        for criterion in criteria:
            # Validate and enhance each criterion
            is_valid, issues = self.quality_validator.validate_content_specificity(
                criterion, 'criteria'
            )
            
            if not is_valid:
                # Apply enhancements based on issues
                enhanced = self.quality_validator.enhance_content_specificity(
                    criterion, 'criteria', context
                )
                enhanced_criteria.append(enhanced)
            else:
                enhanced_criteria.append(criterion)
        
        return enhanced_criteria
    
    def _generate_implementation_details(self, task: Dict[str, Any], context: Dict) -> str:
        """Generate specific implementation details for a task."""
        details = []
        
        domain = context.get('domain', '').lower()
        if domain in self.domain_patterns:
            patterns = self.domain_patterns[domain]
            
            # Add domain-specific implementation guidance
            if 'database' in task.get('description', '').lower():
                details.append("Database operations should include proper indexing and error handling")
            
            if 'api' in task.get('description', '').lower():
                details.append("API implementation should include authentication, validation, and proper HTTP status codes")
            
            if 'ui' in task.get('description', '').lower() or 'interface' in task.get('description', '').lower():
                details.append("UI implementation should include responsive design and accessibility considerations")
        
        return '; '.join(details) if details else "Implementation should follow project coding standards and best practices"
    
    def validate_and_enhance_content(self, content: Dict[str, Any], content_type: str, context: Dict = None) -> Dict[str, Any]:
        """
        Validate and enhance content in a single operation.
        
        Args:
            content: Content dictionary to enhance
            content_type: Type of content (epic, feature, user_story, task)
            context: Additional context
        
        Returns:
            Enhanced content dictionary
        """
        if content_type == 'epic':
            return self.enhance_epic_content(content, context)
        elif content_type == 'feature':
            return self.enhance_feature_content(content, context)
        elif content_type == 'user_story':
            return self.enhance_user_story_content(content, context)
        elif content_type == 'task':
            return self.enhance_task_content(content, context)
        else:
            return content
