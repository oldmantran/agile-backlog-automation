#!/usr/bin/env python3
"""
User Story Quality Assessor

Assesses user story quality focusing on:
1. Proper acceptance criteria format (Given/When/Then within single story)
2. Feature alignment and context preservation
3. Domain specificity and vision connection
4. Technical implementability and user value
5. Story independence and completeness
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class UserStoryQualityAssessment:
    """Represents a quality assessment for a user story."""
    rating: str  # EXCELLENT, GOOD, FAIR, POOR
    score: int   # 0-100
    strengths: List[str]
    weaknesses: List[str]
    specific_issues: List[str]
    improvement_suggestions: List[str]

class UserStoryQualityAssessor:
    """Assesses user story quality with focus on acceptance criteria format."""
    
    def __init__(self):
        self.max_score = 100
        
    def assess_user_story(self, story: Dict[str, Any], feature_context: Dict[str, Any], 
                         domain: str, product_vision: str) -> UserStoryQualityAssessment:
        """
        Assess user story quality across 5 dimensions.
        
        Args:
            story: The user story to assess
            feature_context: Parent feature context
            domain: Project domain
            product_vision: Product vision statement
            
        Returns:
            UserStoryQualityAssessment with rating and feedback
        """
        
        # Extract story details
        title = story.get('title', '')
        description = story.get('description', story.get('user_story', ''))
        acceptance_criteria = story.get('acceptance_criteria', [])
        
        # Assess 5 dimensions
        scores = {
            'acceptance_criteria_format': self._assess_acceptance_criteria_format(acceptance_criteria, title),
            'feature_alignment': self._assess_feature_alignment(story, feature_context),
            'domain_specificity': self._assess_domain_specificity(story, domain, product_vision),
            'user_value': self._assess_user_value_clarity(story),
            'story_completeness': self._assess_story_completeness(story)
        }
        
        # Calculate total score
        total_score = sum(scores.values()) // len(scores)
        
        # Determine rating
        if total_score >= 90:
            rating = "EXCELLENT"
        elif total_score >= 75:
            rating = "GOOD" 
        elif total_score >= 60:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        # Generate feedback
        strengths, weaknesses, issues, suggestions = self._generate_feedback(scores, story, feature_context, domain)
        
        return UserStoryQualityAssessment(
            rating=rating,
            score=total_score,
            strengths=strengths,
            weaknesses=weaknesses,
            specific_issues=issues,
            improvement_suggestions=suggestions
        )
    
    def _assess_acceptance_criteria_format(self, criteria: List[str], title: str) -> int:
        """Assess acceptance criteria format - CRITICAL for Given/When/Then fix."""
        if not criteria:
            return 0
        
        score = 0
        max_score = 100
        
        # Check quantity (3-5 criteria required)
        if len(criteria) < 3:
            score += 0  # Fail - too few criteria
        elif len(criteria) > 5:
            score += 60  # Partial - too many criteria
        else:
            score += 80  # Good quantity
        
        # Check format - each criterion should be complete Given/When/Then
        proper_format_count = 0
        for criterion in criteria:
            if self._is_proper_acceptance_criterion(criterion):
                proper_format_count += 1
        
        format_score = (proper_format_count / len(criteria)) * 20
        score += int(format_score)
        
        return min(score, max_score)
    
    def _is_proper_acceptance_criterion(self, criterion: str) -> bool:
        """Check if acceptance criterion follows proper Given/When/Then format."""
        criterion_lower = criterion.lower().strip()
        
        # Should contain Given, When, Then structure
        has_given = 'given' in criterion_lower
        has_when = 'when' in criterion_lower  
        has_then = 'then' in criterion_lower
        
        # Should NOT be just "Given" or "When" or "Then" (separate story issue)
        is_fragment = (
            criterion_lower.startswith('given ') and 'when' not in criterion_lower and 'then' not in criterion_lower
        ) or (
            criterion_lower.startswith('when ') and 'given' not in criterion_lower and 'then' not in criterion_lower
        ) or (
            criterion_lower.startswith('then ') and 'given' not in criterion_lower and 'when' not in criterion_lower
        )
        
        # Proper format: contains all three components OR is a complete scenario
        return (has_given and has_when and has_then) or (not is_fragment and len(criterion.strip()) > 20)
    
    def _assess_feature_alignment(self, story: Dict[str, Any], feature_context: Dict[str, Any]) -> int:
        """Assess how well story aligns with parent feature."""
        if not feature_context:
            return 50  # Neutral score if no context
        
        feature_title = feature_context.get('title', '').lower()
        feature_description = feature_context.get('description', '').lower()
        
        story_title = story.get('title', '').lower()
        story_description = story.get('description', story.get('user_story', '')).lower()
        
        # Check for shared keywords/concepts
        feature_keywords = set(re.findall(r'\b\w{4,}\b', feature_title + ' ' + feature_description))
        story_keywords = set(re.findall(r'\b\w{4,}\b', story_title + ' ' + story_description))
        
        overlap = len(feature_keywords.intersection(story_keywords))
        total_feature_keywords = len(feature_keywords)
        
        if total_feature_keywords == 0:
            return 50
        
        alignment_ratio = overlap / total_feature_keywords
        return min(int(alignment_ratio * 100), 100)
    
    def _assess_domain_specificity(self, story: Dict[str, Any], domain: str, product_vision: str) -> int:
        """Assess domain-specific terminology and context."""
        story_text = (
            story.get('title', '') + ' ' + 
            story.get('description', story.get('user_story', '')) + ' ' +
            ' '.join(story.get('acceptance_criteria', []))
        ).lower()
        
        # Domain-specific scoring
        domain_keywords = {
            'logistics': ['warehouse', 'dock', 'asset', 'gate', 'distribution', 'loading', 'shipment', 'inventory'],
            'healthcare': ['patient', 'medical', 'clinical', 'diagnosis', 'treatment', 'healthcare', 'hospital'],
            'finance': ['transaction', 'payment', 'account', 'financial', 'banking', 'investment', 'portfolio'],
            'retail': ['customer', 'product', 'order', 'shopping', 'purchase', 'inventory', 'catalog'],
            'education': ['student', 'course', 'learning', 'grade', 'assignment', 'curriculum', 'academic']
        }
        
        relevant_keywords = domain_keywords.get(domain, ['user', 'system', 'data', 'interface'])
        
        found_keywords = sum(1 for keyword in relevant_keywords if keyword in story_text)
        keyword_score = min((found_keywords / len(relevant_keywords)) * 100, 100)
        
        # Vision alignment check
        vision_words = re.findall(r'\b\w{4,}\b', product_vision.lower())
        vision_alignment = sum(1 for word in vision_words if word in story_text)
        vision_score = min((vision_alignment / max(len(vision_words), 1)) * 100, 50)
        
        return int((keyword_score + vision_score) / 2)
    
    def _assess_user_value_clarity(self, story: Dict[str, Any]) -> int:
        """Assess clarity of user value and benefit."""
        title = story.get('title', '')
        description = story.get('description', story.get('user_story', ''))
        
        score = 0
        
        # Check for proper user story format
        if 'as a' in title.lower() and 'i want' in title.lower() and 'so that' in title.lower():
            score += 40
        elif 'as a' in description.lower() and 'i want' in description.lower():
            score += 30
        
        # Check for clear user type
        user_types = ['user', 'admin', 'manager', 'operator', 'customer', 'employee']
        if any(user_type in (title + description).lower() for user_type in user_types):
            score += 20
        
        # Check for clear benefit statement
        if 'so that' in (title + description).lower():
            score += 30
        elif any(word in (title + description).lower() for word in ['benefit', 'enable', 'improve', 'reduce']):
            score += 20
        
        # Check description quality
        if len(description) > 50:
            score += 10
        
        return min(score, 100)
    
    def _assess_story_completeness(self, story: Dict[str, Any]) -> int:
        """Assess story completeness and independence."""
        score = 0
        
        # Required fields check
        required_fields = ['title', 'description', 'acceptance_criteria', 'story_points', 'priority']
        present_fields = sum(1 for field in required_fields if story.get(field))
        score += (present_fields / len(required_fields)) * 40
        
        # Story points reasonableness
        story_points = story.get('story_points', 0)
        if story_points in [1, 2, 3, 5, 8, 13]:
            score += 20
        elif story_points > 0:
            score += 10
        
        # Priority set
        if story.get('priority') in ['High', 'Medium', 'Low']:
            score += 20
        
        # Adequate description length
        description = story.get('description', story.get('user_story', ''))
        if len(description) > 100:
            score += 20
        elif len(description) > 50:
            score += 10
        
        return min(score, 100)
    
    def _generate_feedback(self, scores: Dict[str, int], story: Dict[str, Any], 
                          feature_context: Dict[str, Any], domain: str) -> tuple:
        """Generate strengths, weaknesses, issues, and suggestions."""
        strengths = []
        weaknesses = []
        issues = []
        suggestions = []
        
        # Acceptance Criteria feedback
        criteria_score = scores['acceptance_criteria_format']
        if criteria_score >= 80:
            strengths.append("Proper acceptance criteria format with complete scenarios")
        elif criteria_score >= 60:
            weaknesses.append("Acceptance criteria format needs improvement")
            suggestions.append("Ensure each criterion includes Given/When/Then or complete test scenario")
        else:
            issues.append("CRITICAL: Acceptance criteria are incomplete or improperly formatted")
            suggestions.append("Replace separate Given/When/Then stories with complete acceptance criteria")
        
        # Check for Given/When/Then fragment issue specifically
        criteria = story.get('acceptance_criteria', [])
        for criterion in criteria:
            criterion_lower = criterion.lower().strip()
            if (criterion_lower.startswith('given ') and len(criterion_lower.split()) < 10) or \
               (criterion_lower.startswith('when ') and len(criterion_lower.split()) < 8) or \
               (criterion_lower.startswith('then ') and len(criterion_lower.split()) < 8):
                issues.append("Found Given/When/Then fragments instead of complete acceptance criteria")
                suggestions.append("Combine Given/When/Then components into complete test scenarios")
                break
        
        # Feature alignment feedback
        alignment_score = scores['feature_alignment']
        if alignment_score >= 75:
            strengths.append("Strong alignment with parent feature goals")
        else:
            weaknesses.append("Weak connection to parent feature requirements")
            suggestions.append("Include more specific references to parent feature functionality")
        
        # Domain specificity feedback
        domain_score = scores['domain_specificity']
        if domain_score >= 70:
            strengths.append(f"Good use of {domain}-specific terminology")
        else:
            weaknesses.append(f"Lacks {domain} domain-specific context")
            suggestions.append(f"Include more {domain} industry terminology and workflows")
        
        # User value feedback
        value_score = scores['user_value']
        if value_score >= 70:
            strengths.append("Clear user value and benefit statement")
        else:
            weaknesses.append("User benefit not clearly articulated")
            suggestions.append("Add clear 'so that' benefit statement explaining user value")
        
        # Completeness feedback
        completeness_score = scores['story_completeness']
        if completeness_score >= 80:
            strengths.append("Complete story with all required fields")
        else:
            issues.append("Missing required story fields or information")
            suggestions.append("Ensure story points, priority, and detailed description are provided")
        
        return strengths, weaknesses, issues, suggestions
    
    def format_assessment_log(self, story: Dict[str, Any], assessment: UserStoryQualityAssessment, attempt: int) -> str:
        """Format assessment results for logging."""
        title = story.get('title', 'Unknown Story')[:60]
        
        log_parts = [
            f"USER STORY QUALITY ASSESSMENT (Attempt {attempt})",
            f"Story: {title}...",
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