"""
Streamlined Epic Quality Assessment Module
Evaluates epics based on clear, practical criteria aligned with the simplified prompt.
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass

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
        # Domain-specific terms by category
        self.domain_terms = {
            'transportation': ['vehicle', 'ride', 'fleet', 'route', 'dispatch', 'autonomous', 'mobility', 'transit', 'passenger'],
            'healthcare': ['patient', 'clinical', 'medical', 'diagnosis', 'treatment', 'provider', 'care'],
            'finance': ['transaction', 'payment', 'investment', 'portfolio', 'trading', 'financial'],
            'retail': ['customer', 'inventory', 'product', 'shopping', 'purchase', 'order'],
            'logistics': ['warehouse', 'shipment', 'delivery', 'tracking', 'distribution', 'supply chain'],
            'education': ['student', 'learning', 'course', 'curriculum', 'teacher', 'classroom'],
            'agriculture': ['crop', 'yield', 'soil', 'irrigation', 'harvest', 'farm', 'livestock', 'agronomy', 'fertilizer', 'seed', 'agricultural', 'farming']
        }
        
        # Platform indicators
        self.platform_terms = ['mobile', 'ios', 'android', 'web', 'cloud', 'api', 'dashboard', 'real-time']
        
        # User role patterns - including domain-specific users
        self.user_patterns = r'\b(User|Customer|Student|Patient|Driver|Rider|Commuter|Manager|Admin|Teacher|Operator|Farmer|Smallholder|Agri-Lender|Cooperative|Aggregator|NGO|MFI|Lender)\b'
        
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
        # Check both title AND description for user mentions
        if re.search(self.user_patterns, title, re.I) or re.search(self.user_patterns, description, re.I):
            score += 15
            strengths.append("Identifies target users")
        else:
            specific_issues.append("No specific users mentioned")
            weaknesses.append("Add WHO will use this (e.g., Smallholder Farmers, Agri-Lenders)")
        
        # 4. Platform/Technology (15 points)
        platform_found = any(term in combined_text for term in self.platform_terms)
        if platform_found:
            score += 15
            strengths.append("Includes platform/technology details")
        else:
            weaknesses.append("Missing platform specifics (mobile, web, etc.)")
        
        # 5. Domain Terminology (15 points)
        domain_terms = self.domain_terms.get(domain, [])
        domain_count = sum(1 for term in domain_terms if term in combined_text)
        
        if domain_count >= 3:
            score += 15
            strengths.append(f"Uses {domain} domain terminology")
        elif domain_count >= 1:
            score += 8
            weaknesses.append(f"Limited {domain} domain terminology")
        else:
            specific_issues.append(f"No {domain}-specific terminology found")
        
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
            if not any(term in combined_text for term in domain_terms):
                improvement_suggestions.append(f"Include {domain} terms like: {', '.join(domain_terms[:3])}")
            if not re.search(self.user_patterns, title, re.I) and not re.search(self.user_patterns, description, re.I):
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