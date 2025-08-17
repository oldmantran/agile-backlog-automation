#!/usr/bin/env python3
"""
Task Quality Assessor

Assesses technical task quality focusing on:
1. User story alignment and traceability
2. Technical implementation specificity
3. Domain context preservation  
4. Actionability and clarity
5. Estimation accuracy and completeness
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class TaskQualityAssessment:
    """Represents a quality assessment for a technical task."""
    rating: str  # EXCELLENT, GOOD, FAIR, POOR
    score: int   # 0-100
    strengths: List[str]
    weaknesses: List[str]
    specific_issues: List[str]
    improvement_suggestions: List[str]

class TaskQualityAssessor:
    """Assesses technical task quality with focus on implementation specificity."""
    
    def __init__(self):
        self.max_score = 100
        
    def assess_task(self, task: Dict[str, Any], user_story_context: Dict[str, Any], 
                   domain: str, product_vision: str) -> TaskQualityAssessment:
        """
        Assess technical task quality across 5 dimensions.
        
        Args:
            task: The technical task to assess
            user_story_context: Parent user story context
            domain: Project domain
            product_vision: Product vision statement
            
        Returns:
            TaskQualityAssessment with rating and feedback
        """
        
        # Extract task details
        title = task.get('title', '')
        description = task.get('description', '')
        
        # Assess 5 dimensions
        scores = {
            'user_story_alignment': self._assess_user_story_alignment(task, user_story_context),
            'technical_specificity': self._assess_technical_specificity(task),
            'domain_context': self._assess_domain_context(task, domain, product_vision),
            'actionability': self._assess_actionability(task),
            'estimation_quality': self._assess_estimation_quality(task)
        }
        
        # Calculate total score
        total_score = sum(scores.values()) // len(scores)
        
        # Determine rating
        if total_score >= 80:
            rating = "EXCELLENT"
        elif total_score >= 65:
            rating = "GOOD" 
        elif total_score >= 45:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        # Generate feedback
        strengths, weaknesses, issues, suggestions = self._generate_feedback(scores, task, user_story_context, domain)
        
        return TaskQualityAssessment(
            rating=rating,
            score=total_score,
            strengths=strengths,
            weaknesses=weaknesses,
            specific_issues=issues,
            improvement_suggestions=suggestions
        )
    
    def _assess_user_story_alignment(self, task: Dict[str, Any], user_story_context: Dict[str, Any]) -> int:
        """Assess how well task aligns with parent user story."""
        if not user_story_context:
            return 50  # Neutral score if no context
        
        story_title = user_story_context.get('title', '').lower()
        story_description = user_story_context.get('description', '').lower()
        acceptance_criteria = user_story_context.get('acceptance_criteria', [])
        
        task_title = task.get('title', '').lower()
        task_description = task.get('description', '').lower()
        task_text = task_title + ' ' + task_description
        
        score = 0
        
        # Check for shared keywords/concepts with story
        story_keywords = set(re.findall(r'\b\w{4,}\b', story_title + ' ' + story_description))
        task_keywords = set(re.findall(r'\b\w{4,}\b', task_text))
        
        overlap = len(story_keywords.intersection(task_keywords))
        total_story_keywords = len(story_keywords)
        
        if total_story_keywords > 0:
            alignment_ratio = overlap / total_story_keywords
            score += int(alignment_ratio * 60)  # 60 points max for keyword alignment
        else:
            score += 30  # Neutral if no story keywords
        
        # Check for acceptance criteria alignment
        criteria_alignment = 0
        for criterion in acceptance_criteria:
            criterion_words = set(re.findall(r'\b\w{4,}\b', criterion.lower()))
            criterion_overlap = len(criterion_words.intersection(task_keywords))
            if criterion_overlap > 0:
                criteria_alignment += 1
        
        if acceptance_criteria:
            criteria_score = (criteria_alignment / len(acceptance_criteria)) * 40
            score += int(criteria_score)
        else:
            score += 20  # Neutral if no criteria
        
        return min(score, 100)
    
    def _assess_technical_specificity(self, task: Dict[str, Any]) -> int:
        """Assess technical implementation specificity and detail."""
        title = task.get('title', '')
        description = task.get('description', '')
        task_text = (title + ' ' + description).lower()
        
        score = 0
        
        # Technical implementation indicators
        tech_indicators = [
            'api', 'endpoint', 'database', 'table', 'model', 'class', 'function', 'method',
            'component', 'service', 'controller', 'repository', 'interface', 'schema',
            'query', 'validation', 'authentication', 'authorization', 'middleware',
            'configuration', 'deployment', 'testing', 'logging', 'monitoring'
        ]
        
        found_tech_terms = sum(1 for term in tech_indicators if term in task_text)
        tech_score = min((found_tech_terms / 5) * 40, 40)  # 40 points max, expect 5+ terms
        score += int(tech_score)
        
        # Specific technology/framework mentions
        tech_specifics = [
            'react', 'angular', 'vue', 'node', 'express', 'fastapi', 'django', 'flask',
            'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
            'aws', 'azure', 'gcp', 'rest', 'graphql', 'jwt', 'oauth'
        ]
        
        found_specifics = sum(1 for term in tech_specifics if term in task_text)
        specific_score = min((found_specifics / 2) * 30, 30)  # 30 points max, expect 2+ specifics
        score += int(specific_score)
        
        # Implementation detail indicators
        detail_indicators = ['create', 'implement', 'configure', 'setup', 'build', 'develop', 'design']
        found_details = sum(1 for term in detail_indicators if term in task_text)
        
        if found_details > 0:
            score += 30  # 30 points for actionable implementation verbs
        
        return min(score, 100)
    
    def _assess_domain_context(self, task: Dict[str, Any], domain: str, product_vision: str) -> int:
        """Assess domain-specific context preservation."""
        task_text = (
            task.get('title', '') + ' ' + 
            task.get('description', '')
        ).lower()
        
        # Domain-specific scoring
        domain_keywords = {
            'logistics': ['warehouse', 'dock', 'asset', 'gate', 'distribution', 'loading', 'shipment', 'inventory', 'tracking'],
            'healthcare': ['patient', 'medical', 'clinical', 'diagnosis', 'treatment', 'healthcare', 'hospital', 'record'],
            'finance': ['transaction', 'payment', 'account', 'financial', 'banking', 'investment', 'portfolio', 'compliance'],
            'retail': ['customer', 'product', 'order', 'shopping', 'purchase', 'inventory', 'catalog', 'checkout'],
            'education': ['student', 'course', 'learning', 'grade', 'assignment', 'curriculum', 'academic', 'assessment'],
            'agriculture': ['field', 'crop', 'soil', 'irrigation', 'harvest', 'yield', 'sensor', 'weather', 'farm', 
                           'precision', 'variable rate', 'isobus', 'fertilizer', 'moisture', 'satellite', 'ndvi',
                           'agronomy', 'planting', 'tractor', 'implement', 'grain', 'livestock', 'pasture']
        }
        
        relevant_keywords = domain_keywords.get(domain, ['user', 'system', 'data', 'interface'])
        
        found_keywords = sum(1 for keyword in relevant_keywords if keyword in task_text)
        keyword_score = min((found_keywords / len(relevant_keywords)) * 60, 60)
        
        # Vision alignment check
        vision_words = re.findall(r'\b\w{4,}\b', product_vision.lower())
        vision_alignment = sum(1 for word in vision_words if word in task_text)
        vision_score = min((vision_alignment / max(len(vision_words), 1)) * 40, 40)
        
        return int(keyword_score + vision_score)
    
    def _assess_actionability(self, task: Dict[str, Any]) -> int:
        """Assess task actionability and clarity."""
        title = task.get('title', '')
        description = task.get('description', '')
        
        score = 0
        
        # Clear action verbs in title
        action_verbs = [
            'implement', 'create', 'build', 'develop', 'design', 'configure', 'setup',
            'integrate', 'test', 'deploy', 'refactor', 'optimize', 'fix', 'update'
        ]
        
        has_action_verb = any(verb in title.lower() for verb in action_verbs)
        if has_action_verb:
            score += 30
        
        # Specific deliverable mentioned
        deliverables = [
            'component', 'endpoint', 'api', 'database', 'table', 'function', 'class',
            'interface', 'service', 'test', 'documentation', 'configuration'
        ]
        
        has_deliverable = any(deliverable in (title + description).lower() for deliverable in deliverables)
        if has_deliverable:
            score += 30
        
        # Adequate description length
        if len(description) > 100:
            score += 40
        elif len(description) > 50:
            score += 20
        
        return min(score, 100)
    
    def _assess_estimation_quality(self, task: Dict[str, Any]) -> int:
        """Assess estimation accuracy and completeness."""
        score = 0
        
        # Time estimate provided
        time_estimate = task.get('time_estimate', 0)
        if isinstance(time_estimate, (int, float)) and time_estimate > 0:
            score += 40
            
            # Reasonable estimate range (0.5 to 16 hours)
            if 0.5 <= time_estimate <= 16:
                score += 20
        
        # Complexity/difficulty provided
        complexity = task.get('complexity', '')
        if complexity in ['Low', 'Medium', 'High']:
            score += 20
        
        # Story points or effort estimate
        effort = task.get('story_points', task.get('effort_points', 0))
        if isinstance(effort, (int, float)) and effort > 0:
            score += 20
        
        return min(score, 100)
    
    def _generate_feedback(self, scores: Dict[str, int], task: Dict[str, Any], 
                          user_story_context: Dict[str, Any], domain: str) -> tuple:
        """Generate strengths, weaknesses, issues, and suggestions."""
        strengths = []
        weaknesses = []
        issues = []
        suggestions = []
        
        # User story alignment feedback
        alignment_score = scores['user_story_alignment']
        if alignment_score >= 75:
            strengths.append("Strong alignment with parent user story requirements")
        else:
            weaknesses.append("Weak connection to parent user story")
            suggestions.append("Include more specific references to user story acceptance criteria")
        
        # Technical specificity feedback
        tech_score = scores['technical_specificity']
        if tech_score >= 70:
            strengths.append("Good technical implementation specificity")
        else:
            issues.append("Lacks technical implementation details")
            suggestions.append("Add specific APIs, database tables, components, or technical approaches")
        
        # Domain context feedback
        domain_score = scores['domain_context']
        if domain_score >= 60:
            strengths.append(f"Good use of {domain}-specific context")
        else:
            weaknesses.append(f"Missing {domain} domain context")
            suggestions.append(f"Include {domain} industry-specific terminology and requirements")
        
        # Actionability feedback
        action_score = scores['actionability']
        if action_score >= 70:
            strengths.append("Clear actionable task definition")
        else:
            issues.append("Task lacks clear actionable steps")
            suggestions.append("Define specific deliverables and implementation steps")
        
        # Estimation feedback
        estimation_score = scores['estimation_quality']
        if estimation_score >= 60:
            strengths.append("Good estimation and effort planning")
        else:
            issues.append("Missing or inadequate time/effort estimates")
            suggestions.append("Provide time estimate, complexity level, and story points")
        
        return strengths, weaknesses, issues, suggestions
    
    def format_assessment_log(self, task: Dict[str, Any], assessment: TaskQualityAssessment, attempt: int) -> str:
        """Format assessment results for logging."""
        title = task.get('title', 'Unknown Task')[:60]
        
        log_parts = [
            f"TASK QUALITY ASSESSMENT (Attempt {attempt})",
            f"Task: {title}...",
            f"Rating: {assessment.rating} ({assessment.score}/100)",
            ""
        ]
        
        if assessment.strengths:
            log_parts.append("STRENGTHS:")
            for strength in assessment.strengths[:3]:  # Limit to top 3
                log_parts.append(f"   + {strength}")
            log_parts.append("")
        
        if assessment.specific_issues:
            log_parts.append("CRITICAL ISSUES:")
            for issue in assessment.specific_issues:
                log_parts.append(f"   - {issue}")
            log_parts.append("")
        
        if assessment.improvement_suggestions:
            log_parts.append("IMPROVEMENT SUGGESTIONS:")
            for suggestion in assessment.improvement_suggestions[:3]:  # Limit to top 3
                log_parts.append(f"   * {suggestion}")
            log_parts.append("")
        
        return "\n".join(log_parts)