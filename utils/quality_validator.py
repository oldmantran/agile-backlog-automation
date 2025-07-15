"""
Work Item Quality Validation Utilities

Shared validation logic to ensure all agents create work items that comply
with the standards monitored by the Backlog Sweeper Agent.
"""

import re
from typing import Dict, List, Any, Tuple, Optional


class WorkItemQualityValidator:
    """
    Utility class for validating work item quality according to Backlog Sweeper standards.
    Used by agents to ensure compliance before creating work items.
    """
    
    def __init__(self, config: Dict = None):
        """Initialize validator with configuration."""
        if config:
            sweeper_config = config.get('agents', {}).get('backlog_sweeper_agent', {})
            acceptance_config = sweeper_config.get('acceptance_criteria', {})
            
            self.min_criteria_count = acceptance_config.get('min_criteria_count', 3)
            self.max_criteria_count = acceptance_config.get('max_criteria_count', 8)
            self.require_bdd_format = acceptance_config.get('require_bdd_format', True)
            self.require_functional_and_nonfunctional = acceptance_config.get('require_functional_and_nonfunctional', True)
        else:
            # Default values
            self.min_criteria_count = 3
            self.max_criteria_count = 8
            self.require_bdd_format = True
            self.require_functional_and_nonfunctional = True
    
    def validate_user_story_description(self, description: str) -> Tuple[bool, List[str]]:
        """
        Validate user story description follows "As a..." format.
        
        Returns:
            Tuple of (is_valid, issues_found)
        """
        issues = []
        
        if not description or not description.strip():
            issues.append("User story description is missing")
            return False, issues
        
        if "As a" not in description and "As an" not in description:
            issues.append("User story description should follow 'As a [user], I want [goal] so that [benefit]' format")
        
        if "I want" not in description and "I can" not in description and "I need" not in description:
            issues.append("User story description should include 'I want', 'I can', or 'I need' to express user goal")
        
        if "so that" not in description and "because" not in description and "to" not in description:
            issues.append("User story description should include benefit/rationale ('so that', 'because', or 'to')")
        
        return len(issues) == 0, issues
    
    def validate_acceptance_criteria(self, criteria: List[str], story_title: str = "") -> Tuple[bool, List[str]]:
        """
        Validate acceptance criteria against INVEST, SMART, and BDD principles.
        
        Returns:
            Tuple of (is_valid, issues_found)
        """
        issues = []
        
        if not criteria or len(criteria) == 0:
            issues.append("User story missing acceptance criteria")
            return False, issues
        
        # Check quantity
        if len(criteria) < self.min_criteria_count:
            issues.append(f"Only {len(criteria)} acceptance criteria found. Recommend {self.min_criteria_count}-{self.max_criteria_count} criteria for proper coverage")
        elif len(criteria) > self.max_criteria_count:
            issues.append(f"{len(criteria)} acceptance criteria found. Consider breaking story down - recommend {self.min_criteria_count}-{self.max_criteria_count} criteria max")
        
        # Check for BDD format (if required)
        if self.require_bdd_format:
            bdd_count = 0
            for criteria_text in criteria:
                if re.search(r'\b(given|when|then)\b', criteria_text.lower()):
                    bdd_count += 1
            
            if bdd_count == 0:
                issues.append("Consider using Given-When-Then (BDD) format for acceptance criteria clarity")
        
        # Check for functional vs non-functional criteria mix (if required)
        if self.require_functional_and_nonfunctional:
            functional_indicators = ['user can', 'system shall', 'application will', 'feature allows', 'button click', 'form submit', 'displays', 'shows']
            nonfunctional_indicators = ['performance', 'response time', 'security', 'usability', 'accessibility', 'reliability', 'scalability', 'within', 'seconds', 'concurrent']
            
            has_functional = any(any(indicator in criteria_text.lower() for indicator in functional_indicators) for criteria_text in criteria)
            has_nonfunctional = any(any(indicator in criteria_text.lower() for indicator in nonfunctional_indicators) for criteria_text in criteria)
            
            if has_functional and not has_nonfunctional:
                issues.append("Consider adding non-functional acceptance criteria (performance, security, usability)")
        
        # Check for vague or unmeasurable criteria
        vague_words = ['better', 'faster', 'easier', 'improved', 'enhanced', 'good', 'bad', 'nice', 'properly', 'correctly']
        for i, criteria_text in enumerate(criteria):
            if any(vague_word in criteria_text.lower() for vague_word in vague_words):
                if not re.search(r'\d+|specific|exact|precise|clearly|successfully', criteria_text.lower()):
                    issues.append(f"Criteria {i+1} contains vague language. Make it more specific and measurable")
        
        return len(issues) == 0, issues
    
    def validate_work_item_title(self, title: str, work_item_type: str) -> Tuple[bool, List[str]]:
        """
        Validate work item title for completeness and clarity.
        
        Returns:
            Tuple of (is_valid, issues_found)
        """
        issues = []
        
        if not title or not title.strip():
            issues.append(f"{work_item_type} missing title")
            return False, issues
        
        if len(title) > 255:
            issues.append(f"{work_item_type} title too long (max 255 characters)")
        
        if len(title.strip()) < 5:
            issues.append(f"{work_item_type} title too short (minimum 5 characters)")
        
        return len(issues) == 0, issues
    
    def enhance_acceptance_criteria(self, criteria: List[str], story_context: Dict = None) -> List[str]:
        """
        Enhance acceptance criteria to meet quality standards.
        
        Args:
            criteria: Original acceptance criteria list
            story_context: Context about the user story (title, description, etc.)
        
        Returns:
            Enhanced acceptance criteria list
        """
        enhanced_criteria = []
        
        # Ensure we have minimum number of criteria
        if len(criteria) < self.min_criteria_count:
            # Add standard criteria to reach minimum
            while len(enhanced_criteria) + len(criteria) < self.min_criteria_count:
                if story_context:
                    story_title = story_context.get('title', 'feature')
                else:
                    story_title = 'feature'
                
                # Add common quality criteria
                if 'User can successfully' not in ' '.join(enhanced_criteria + criteria):
                    enhanced_criteria.append(f"User can successfully access and use the {story_title.lower()}")
                elif 'System validates' not in ' '.join(enhanced_criteria + criteria):
                    enhanced_criteria.append("System validates all user inputs and provides clear feedback")
                elif 'response time' not in ' '.join(enhanced_criteria + criteria).lower():
                    enhanced_criteria.append("Feature responds within 3 seconds under normal load")
                else:
                    enhanced_criteria.append("Feature maintains data integrity and handles errors gracefully")
        
        # Combine original and enhanced criteria
        all_criteria = criteria + enhanced_criteria
        
        # Enhance BDD format if required
        if self.require_bdd_format:
            bdd_enhanced = []
            for criteria_text in all_criteria:
                if not re.search(r'\b(given|when|then)\b', criteria_text.lower()):
                    # Try to convert to BDD format
                    if 'user can' in criteria_text.lower():
                        bdd_enhanced.append(f"Given appropriate access, when user attempts the action, then {criteria_text.lower()}")
                    elif 'system' in criteria_text.lower():
                        bdd_enhanced.append(f"Given valid input, when system processes request, then {criteria_text.lower()}")
                    else:
                        bdd_enhanced.append(criteria_text)
                else:
                    bdd_enhanced.append(criteria_text)
            all_criteria = bdd_enhanced
        
        # Ensure we have both functional and non-functional if required
        if self.require_functional_and_nonfunctional:
            functional_indicators = ['user can', 'system shall', 'application will', 'feature allows', 'displays', 'shows']
            nonfunctional_indicators = ['performance', 'response time', 'security', 'within', 'seconds', 'concurrent']
            
            has_functional = any(any(indicator in criteria_text.lower() for indicator in functional_indicators) for criteria_text in all_criteria)
            has_nonfunctional = any(any(indicator in criteria_text.lower() for indicator in nonfunctional_indicators) for criteria_text in all_criteria)
            
            if has_functional and not has_nonfunctional:
                all_criteria.append("System maintains acceptable performance (response time under 3 seconds)")
                all_criteria.append("Feature follows security best practices and validates user permissions")
        
        # Limit to maximum count
        if len(all_criteria) > self.max_criteria_count:
            all_criteria = all_criteria[:self.max_criteria_count]
        
        return all_criteria
    
    def generate_quality_compliant_user_story(self, title: str, user_type: str, goal: str, benefit: str, 
                                             acceptance_criteria: List[str] = None, 
                                             story_points: int = None) -> Dict[str, Any]:
        """
        Generate a user story that complies with all quality standards.
        
        Args:
            title: Story title
            user_type: Type of user (e.g., "administrator", "customer")
            goal: What the user wants to do
            benefit: Why they want to do it
            acceptance_criteria: Optional initial criteria
            story_points: Optional story points estimate
        
        Returns:
            Complete user story dictionary
        """
        # Validate and fix title
        title_valid, title_issues = self.validate_work_item_title(title, "User Story")
        if not title_valid:
            title = f"User Story: {goal[:50]}..."
        
        # Create proper user story description
        description = f"As a {user_type}, I want to {goal} so that {benefit}"
        
        # Validate description
        desc_valid, desc_issues = self.validate_user_story_description(description)
        if not desc_valid:
            # Fix description format
            if "As a" not in description:
                description = f"As a {user_type}, {description}"
            if "so that" not in description:
                description = f"{description} so that I can achieve my goals"
        
        # Handle acceptance criteria
        if not acceptance_criteria:
            acceptance_criteria = [
                f"Given a {user_type} is logged in, when they attempt to {goal}, then they can successfully complete the action",
                f"System provides clear feedback when {goal} is completed successfully",
                f"Feature responds within 3 seconds under normal load"
            ]
        
        # Enhance acceptance criteria to meet standards
        enhanced_criteria = self.enhance_acceptance_criteria(acceptance_criteria, {'title': title})
        
        # Estimate story points if not provided
        if not story_points:
            criteria_count = len(enhanced_criteria)
            if criteria_count <= 3:
                story_points = 2
            elif criteria_count <= 5:
                story_points = 3
            elif criteria_count <= 7:
                story_points = 5
            else:
                story_points = 8
        
        return {
            'title': title,
            'description': description,
            'acceptance_criteria': enhanced_criteria,
            'story_points': story_points,
            'priority': 'Medium',
            'user_type': user_type,
            'definition_of_ready': [
                'Acceptance criteria defined and reviewed',
                'Story points estimated',
                'Dependencies identified',
                'UI/UX requirements clarified'
            ],
            'definition_of_done': [
                'Code developed and reviewed',
                'Unit tests written and passing',
                'Integration tests passing',
                'Acceptance criteria validated',
                'Documentation updated'
            ]
        }
    
    def validate_task_structure(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate task structure for developer agent.
        
        Returns:
            Tuple of (is_valid, issues_found)
        """
        issues = []
        
        # Check required fields
        if not task.get('title'):
            issues.append("Task missing title")
        
        if not task.get('description'):
            issues.append("Task missing description")
        
        # Validate title
        title_valid, title_issues = self.validate_work_item_title(task.get('title', ''), "Task")
        issues.extend(title_issues)
        
        # Check for effort estimation
        if not task.get('estimated_hours') and not task.get('story_points'):
            issues.append("Task missing effort estimation (hours or story points)")
        
        return len(issues) == 0, issues
    
    def validate_test_case_structure(self, test_case: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate test case structure for QA tester agent.
        
        Returns:
            Tuple of (is_valid, issues_found)
        """
        issues = []
        
        # Check required fields
        if not test_case.get('title'):
            issues.append("Test case missing title")
        
        if not test_case.get('steps') and not test_case.get('test_steps'):
            issues.append("Test case missing test steps")
        
        if not test_case.get('expected_result') and not test_case.get('expected_outcome'):
            issues.append("Test case missing expected result")
        
        # Validate title
        title_valid, title_issues = self.validate_work_item_title(test_case.get('title', ''), "Test Case")
        issues.extend(title_issues)
        
        return len(issues) == 0, issues
    
    def validate_content_specificity(self, content: str, content_type: str) -> Tuple[bool, List[str]]:
        """
        Validate content for specificity and actionability.
        
        Args:
            content: Content to validate (description, criteria, etc.)
            content_type: Type of content (e.g., 'description', 'criteria', 'title')
        
        Returns:
            Tuple of (is_valid, issues_found)
        """
        issues = []
        content_lower = content.lower()
        
        # Check for generic phrases that should be more specific
        generic_phrases = [
            'implement functionality',
            'provide capability',
            'enable feature',
            'create system',
            'build solution',
            'develop application',
            'make it work',
            'handle this',
            'process data',
            'manage information',
            'support users',
            'allow users',
            'provide interface',
            'create interface',
            'implement interface'
        ]
        
        for phrase in generic_phrases:
            if phrase in content_lower:
                issues.append(f"{content_type} contains generic phrase '{phrase}' - be more specific about what exactly should be implemented")
        
        # Check for missing concrete details
        if content_type == 'description':
            # Look for quantifiable metrics or specific behaviors
            has_specifics = any(indicator in content_lower for indicator in [
                'exactly', 'within', 'seconds', 'minutes', 'hours', 'days',
                'percentage', '%', 'number', 'count', 'amount', 'size',
                'format', 'type', 'method', 'approach', 'algorithm',
                'database', 'api', 'endpoint', 'service', 'component',
                'workflow', 'process', 'step', 'action', 'behavior'
            ])
            
            if not has_specifics and len(content) > 20:
                issues.append(f"{content_type} lacks specific details - include concrete behaviors, formats, or measurable outcomes")
        
        # Check for actionable language
        if content_type in ['criteria', 'task']:
            # Should contain action words
            action_words = [
                'click', 'select', 'enter', 'submit', 'save', 'delete', 'update',
                'display', 'show', 'hide', 'validate', 'verify', 'check',
                'calculate', 'process', 'generate', 'create', 'remove',
                'navigate', 'redirect', 'filter', 'sort', 'search'
            ]
            
            has_action = any(word in content_lower for word in action_words)
            if not has_action:
                issues.append(f"{content_type} should contain specific action words (e.g., click, enter, display, validate)")
        
        return len(issues) == 0, issues

    def enhance_content_specificity(self, content: str, content_type: str, context: Dict = None) -> str:
        """
        Enhance content to be more specific and actionable.
        
        Args:
            content: Original content
            content_type: Type of content
            context: Additional context for enhancement
        
        Returns:
            Enhanced content string
        """
        enhanced = content
        
        # Replace generic phrases with more specific alternatives
        generic_replacements = {
            'implement functionality': 'implement specific functionality to',
            'provide capability': 'provide the capability to',
            'enable feature': 'enable users to',
            'create system': 'create a system that',
            'build solution': 'build a solution that',
            'develop application': 'develop an application that',
            'handle this': 'handle the specific requirement to',
            'process data': 'process the data by',
            'manage information': 'manage information through',
            'support users': 'support users by allowing them to',
            'allow users': 'allow users to specifically',
            'provide interface': 'provide a user interface that',
            'create interface': 'create an interface that allows',
            'implement interface': 'implement an interface that enables'
        }
        
        for generic, specific in generic_replacements.items():
            enhanced = enhanced.replace(generic, specific)
        
        # Add context-specific enhancements
        if context:
            domain = context.get('domain', '').lower()
            if domain and domain in ['web', 'mobile', 'api', 'database']:
                # Add domain-specific context
                if 'user interface' in enhanced.lower() and domain in ['web', 'mobile']:
                    enhanced = enhanced.replace('user interface', f'{domain} user interface')
                elif 'system' in enhanced.lower() and domain == 'api':
                    enhanced = enhanced.replace('system', 'API system')
        
        return enhanced

    def validate_business_value(self, value_statement: str) -> Tuple[bool, List[str]]:
        """
        Validate business value statement for measurability and clarity.
        
        Args:
            value_statement: Business value statement to validate
        
        Returns:
            Tuple of (is_valid, issues_found)
        """
        issues = []
        value_lower = value_statement.lower()
        
        # Check for quantifiable metrics
        has_metrics = any(indicator in value_lower for indicator in [
            '%', 'percent', 'increase', 'decrease', 'reduce', 'improve',
            'save', 'cost', 'time', 'efficiency', 'productivity',
            'revenue', 'profit', 'roi', 'conversion', 'retention',
            'satisfaction', 'engagement', 'adoption', 'usage'
        ])
        
        if not has_metrics:
            issues.append("Business value statement should include quantifiable metrics or measurable outcomes")
        
        # Check for vague business terms
        vague_business_terms = [
            'better experience', 'improved performance', 'enhanced functionality',
            'increased value', 'optimized process', 'streamlined workflow',
            'better solution', 'improved system', 'enhanced capabilities'
        ]
        
        for term in vague_business_terms:
            if term in value_lower:
                issues.append(f"Business value contains vague term '{term}' - specify exact improvements or metrics")
        
        return len(issues) == 0, issues

    def enhance_business_value(self, value_statement: str, context: Dict = None) -> str:
        """
        Enhance business value statement to be more specific and measurable.
        
        Args:
            value_statement: Original value statement
            context: Additional context for enhancement
        
        Returns:
            Enhanced value statement
        """
        enhanced = value_statement
        
        # Add measurable language if missing
        if not any(indicator in enhanced.lower() for indicator in ['%', 'percent', 'by', 'up to', 'within']):
            # Suggest adding measurable outcomes
            if 'increase' in enhanced.lower() or 'improve' in enhanced.lower():
                enhanced = enhanced.replace('increase', 'increase by X%').replace('improve', 'improve by X%')
            elif 'reduce' in enhanced.lower() or 'decrease' in enhanced.lower():
                enhanced = enhanced.replace('reduce', 'reduce by X%').replace('decrease', 'decrease by X%')
            elif 'save' in enhanced.lower():
                enhanced = enhanced.replace('save', 'save X hours/dollars')
        
        # Add context-specific business value
        if context:
            domain = context.get('domain', '').lower()
            if domain == 'e-commerce' and 'conversion' not in enhanced.lower():
                enhanced += ' (potentially improving conversion rates)'
            elif domain == 'saas' and 'retention' not in enhanced.lower():
                enhanced += ' (potentially improving user retention)'
        
        return enhanced
