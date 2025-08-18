"""
Streamlined Epic Quality Assessment Module
Evaluates epics based on clear, practical criteria aligned with the simplified prompt.
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass
from utils.domain_relevance_scorer import DomainRelevanceScorer
from config.domain_knowledge import get_domain_personas

@dataclass
class QualityAssessment:
    rating: str  # EXCELLENT, GOOD, FAIR, POOR
    score: int   # 0-100
    strengths: List[str]
    weaknesses: List[str]
    specific_issues: List[str]
    improvement_suggestions: List[str]

class EpicQualityAssessor:
    """Streamlined epic quality assessment focused on practical criteria."""
    
    def __init__(self):
        # Initialize domain relevance scorer
        self.domain_scorer = DomainRelevanceScorer()
        
        # Platform indicators
        self.platform_terms = ['mobile', 'ios', 'android', 'web', 'cloud', 'api', 'dashboard', 'real-time']
        
        # Generic user role patterns (will be enhanced with domain-specific ones)
        self.generic_user_patterns = r'\b(User|Customer|Manager|Admin|Operator|Staff|Team|Personnel)\b'
        
    def assess_epic(self, epic: Dict[str, Any], domain: str, product_vision: str) -> QualityAssessment:
        """Assess epic quality based on streamlined criteria."""
        title = epic.get('title', '').strip()
        description = epic.get('description', '').strip()
        
        # Validate basic structure
        if not title or not description:
            return QualityAssessment(
                rating="POOR",
                score=0,
                strengths=[],
                weaknesses=["Missing required fields"],
                specific_issues=["Epic must have title and description"],
                improvement_suggestions=["Provide both title and description"]
            )
        
        score = 0
        strengths = []
        weaknesses = []
        specific_issues = []
        
        # Clean text for analysis
        combined_text = f"{title} {description}".lower()
        vision_lower = product_vision.lower() if product_vision else ""
        
        # 1. Title Quality (15 points)
        if len(title) <= 60:
            score += 10
            strengths.append("Title length appropriate")
        else:
            specific_issues.append(f"Title too long ({len(title)} chars, max 60)")
            
        if any(term in title.lower() for term in vision_lower.split()[:20]):  # Check key vision terms
            score += 5
            strengths.append("Title uses vision terminology")
        else:
            weaknesses.append("Title doesn't reflect vision terminology")
        
        # 2. Vision Alignment (20 points)
        vision_keywords = set(re.findall(r'\b\w{4,}\b', vision_lower))  # Extract meaningful words
        epic_keywords = set(re.findall(r'\b\w{4,}\b', combined_text))
        overlap = len(vision_keywords & epic_keywords)
        
        if overlap >= 10:
            score += 20
            strengths.append("Strong alignment with product vision")
        elif overlap >= 5:
            score += 10
            weaknesses.append("Moderate vision alignment - include more vision terms")
        else:
            specific_issues.append("Weak connection to product vision")
        
        # 3. User Specificity (15 points)
        # Get domain-specific user personas
        domain_personas = get_domain_personas(domain)
        user_pattern = self._build_user_pattern(domain_personas)
        
        # Check both title AND description for user mentions
        if re.search(user_pattern, title, re.I) or re.search(user_pattern, description, re.I):
            score += 15
            strengths.append("Identifies target users")
        else:
            # Check for generic user mentions - partial credit
            if re.search(self.generic_user_patterns, title, re.I) or re.search(self.generic_user_patterns, description, re.I):
                score += 8
                weaknesses.append("Uses generic user terms - specify domain users")
            else:
                specific_issues.append("No specific users mentioned")
                if domain_personas:
                    example_users = domain_personas[:3]
                    weaknesses.append(f"Add WHO will use this (e.g., {', '.join(example_users)})")
                else:
                    weaknesses.append("Add WHO will use this feature")
        
        # 4. Platform/Technology (15 points)
        platform_found = any(term in combined_text for term in self.platform_terms)
        if platform_found:
            score += 15
            strengths.append("Includes platform/technology details")
        else:
            weaknesses.append("Missing platform specifics (mobile, web, etc.)")
        
        # 5. Domain Terminology (15 points max - using flexible scoring)
        domain_score, domain_feedback = self.domain_scorer.score_domain_relevance(epic, domain, "epic")
        
        # Map domain score to epic assessment points (max 15)
        # Domain scorer can give up to ~38 points, so scale appropriately
        domain_points = min(15, int(domain_score * 0.4))  # Scale to max 15 points
        score += domain_points
        
        # Add feedback based on domain scoring
        if domain_points >= 12:
            strengths.append(f"Strong {domain} domain alignment")
        elif domain_points >= 8:
            strengths.append(f"Good {domain} domain relevance")
            # Add the most relevant feedback
            if domain_feedback:
                weaknesses.append(domain_feedback[0])
        elif domain_points >= 5:
            weaknesses.append(f"Limited {domain} domain terminology")
            # Add specific feedback
            for feedback in domain_feedback[:2]:
                weaknesses.append(feedback)
        else:
            specific_issues.append(f"Weak {domain}-specific content")
            # Provide helpful feedback
            for feedback in domain_feedback[:1]:
                weaknesses.append(feedback)
        
        # 6. Measurable Outcomes (10 points)
        if re.search(r'\d+[%\s]|<\d+|>\d+|\d+\s*(second|minute|hour|day)', description):
            score += 10
            strengths.append("Includes measurable outcomes")
        else:
            weaknesses.append("No measurable targets or metrics")
        
        # 7. Actionable Description (10 points)
        action_verbs = ['enable', 'provide', 'deliver', 'create', 'implement', 'achieve', 'reduce', 'increase']
        if any(verb in description.lower() for verb in action_verbs):
            score += 10
            strengths.append("Clear actionable language")
        else:
            weaknesses.append("Lacks actionable verbs")
        
        # Generate improvement suggestions
        improvement_suggestions = []
        if score < 75:
            # Domain-specific improvements based on flexible scoring
            if domain_points < 10:
                domain_report = self.domain_scorer.get_domain_relevance_report(epic, domain)
                improvement_suggestions.append(domain_report['recommendation'])
            
            # User specificity improvements
            if not re.search(user_pattern, title, re.I) and not re.search(user_pattern, description, re.I):
                if domain_personas:
                    improvement_suggestions.append(f"Specify target users: {', '.join(domain_personas[:3])}")
                else:
                    improvement_suggestions.append("Specify target users from the vision")
            
            if not platform_found:
                improvement_suggestions.append("Add platform details (mobile, web, cloud, etc.)")
            if overlap < 10:
                improvement_suggestions.append("Use more specific terms from the product vision")
        
        # Determine rating
        if score >= 80:
            rating = "EXCELLENT"
        elif score >= 70:
            rating = "GOOD"
        elif score >= 50:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        return QualityAssessment(
            rating=rating,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            specific_issues=specific_issues,
            improvement_suggestions=improvement_suggestions
        )
    
    def format_assessment_log(self, epic: Dict[str, Any], assessment: QualityAssessment, attempt: int) -> str:
        """Format assessment for logging."""
        title = epic.get('title', 'Untitled')
        output = f"EPIC QUALITY ASSESSMENT (Attempt {attempt})\n"
        output += f"Epic: {title}\n"
        output += f"Rating: {assessment.rating} ({assessment.score}/100)\n\n"
        
        if assessment.strengths:
            output += "+ Strengths:\n"
            for strength in assessment.strengths:
                output += f"  - {strength}\n"
            output += "\n"
        
        if assessment.weaknesses or assessment.specific_issues:
            output += "- Issues:\n"
            for issue in assessment.specific_issues + assessment.weaknesses:
                output += f"  - {issue}\n"
            output += "\n"
        
        if assessment.improvement_suggestions:
            output += "* Improvement Suggestions:\n"
            for suggestion in assessment.improvement_suggestions:
                output += f"  - {suggestion}\n"
        
        return output
    
    def _build_user_pattern(self, domain_personas: List[str]) -> str:
        """Build regex pattern for user detection including domain-specific personas."""
        # Start with generic patterns
        patterns = ['User', 'Customer', 'Manager', 'Admin', 'Operator', 'Staff', 'Team', 'Personnel']
        
        # Add domain-specific personas
        if domain_personas:
            for persona in domain_personas:
                # Add both singular and plural forms
                patterns.append(persona)
                # Handle common variations
                if persona.endswith('s') and not persona.endswith('ss'):
                    patterns.append(persona[:-1])  # Remove 's' for singular
                elif not persona.endswith('s'):
                    patterns.append(persona + 's')  # Add 's' for plural
        
        # Build regex pattern
        pattern_str = r'\b(' + '|'.join(re.escape(p) for p in patterns) + r')\b'
        return pattern_str