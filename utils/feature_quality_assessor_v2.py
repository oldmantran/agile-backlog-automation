"""
Streamlined Feature Quality Assessment Module
Evaluates features based on clear, practical criteria aligned with the simplified prompt.
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

class FeatureQualityAssessor:
    """Streamlined feature quality assessment focused on practical criteria."""
    
    def __init__(self):
        # User role patterns
        self.user_patterns = r'\b(User|Customer|Student|Patient|Driver|Rider|Commuter|Manager|Admin|Teacher|Operator|Tourist|Night Owl)\b'
        
        # Platform indicators
        self.platform_terms = ['mobile', 'ios', 'android', 'web', 'cloud', 'api', 'dashboard', 'real-time']
        
        # Value indicators
        self.value_patterns = r'\d+[%\s]|<\d+|>\d+|\d+x|reduces|increases|enables|improves|accelerates'
        
    def assess_feature(self, feature: Dict[str, Any], epic: Dict[str, Any], 
                      domain: str, product_vision: str) -> QualityAssessment:
        """Assess feature quality based on streamlined criteria."""
        title = feature.get('title', '').strip()
        description = feature.get('description', '').strip()
        business_value = feature.get('business_value', '').strip()
        
        # Validate basic structure
        if not title or not description:
            return QualityAssessment(
                rating="POOR",
                score=0,
                strengths=[],
                weaknesses=["Missing required fields"],
                specific_issues=["Feature must have title and description"],
                improvement_suggestions=["Provide both title and description"]
            )
        
        score = 0
        strengths = []
        weaknesses = []
        specific_issues = []
        
        # Clean text for analysis
        combined_text = f"{title} {description} {business_value}".lower()
        epic_text = f"{epic.get('title', '')} {epic.get('description', '')}".lower()
        
        # 1. Title Quality (15 points)
        if len(title) <= 80:
            score += 10
            strengths.append("Title length appropriate")
        else:
            specific_issues.append(f"Title too long ({len(title)} chars, max 80)")
            
        if any(term in title.lower() for term in epic_text.split()[:10]):  # Check epic terms
            score += 5
            strengths.append("Title aligns with epic")
        else:
            weaknesses.append("Title doesn't reflect epic terminology")
        
        # 2. Epic Support (20 points)
        epic_keywords = set(re.findall(r'\b\w{4,}\b', epic_text))
        feature_keywords = set(re.findall(r'\b\w{4,}\b', combined_text))
        overlap = len(epic_keywords & feature_keywords)
        
        if overlap >= 5:
            score += 20
            strengths.append("Strong alignment with epic goals")
        elif overlap >= 3:
            score += 10
            weaknesses.append("Moderate epic alignment - strengthen connection")
        else:
            specific_issues.append("Weak connection to parent epic")
        
        # 3. User Specificity (15 points)
        if re.search(self.user_patterns, description, re.I):
            score += 15
            strengths.append("Identifies target users")
        else:
            specific_issues.append("No specific users mentioned")
            weaknesses.append("Add WHO will use this feature")
        
        # 4. Platform/Technology (15 points)
        platform_found = any(term in combined_text for term in self.platform_terms)
        if platform_found:
            score += 15
            strengths.append("Includes platform/technology details")
        else:
            weaknesses.append("Missing platform specifics (mobile, web, etc.)")
        
        # 5. Business Value (15 points)
        if business_value and re.search(self.value_patterns, business_value, re.I):
            score += 15
            strengths.append("Clear measurable business value")
        elif business_value:
            score += 8
            weaknesses.append("Business value lacks metrics")
        else:
            specific_issues.append("No business value specified")
        
        # 6. Independence & Deliverability (10 points)
        dependencies = feature.get('dependencies', [])
        if len(dependencies) <= 2:
            score += 10
            strengths.append("Independently deliverable")
        else:
            weaknesses.append(f"Many dependencies ({len(dependencies)}) may impact delivery")
        
        # 7. Appropriate Scope (10 points)
        story_points = feature.get('estimated_story_points', 0)
        if 5 <= story_points <= 13:
            score += 10
            strengths.append("Appropriate feature scope")
        else:
            weaknesses.append(f"Story points ({story_points}) suggest scope issues")
        
        # Generate improvement suggestions
        improvement_suggestions = []
        if score < 75:
            if not re.search(self.user_patterns, description, re.I):
                improvement_suggestions.append("Specify which users from the epic will use this")
            if not platform_found:
                improvement_suggestions.append("Add platform details (mobile app, web dashboard, etc.)")
            if overlap < 5:
                improvement_suggestions.append("Use more specific terms from the parent epic")
            if not re.search(self.value_patterns, business_value or "", re.I):
                improvement_suggestions.append("Add measurable business value (percentages, time savings, etc.)")
        
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
    
    def format_assessment_log(self, feature: Dict[str, Any], assessment: QualityAssessment, attempt: int) -> str:
        """Format assessment for logging."""
        title = feature.get('title', 'Untitled')
        output = f"FEATURE QUALITY ASSESSMENT (Attempt {attempt})\n"
        output += f"Feature: {title}\n"
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