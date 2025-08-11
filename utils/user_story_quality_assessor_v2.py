"""
Streamlined User Story Quality Assessment Module
Evaluates user stories based on clear, practical criteria aligned with the simplified prompt.
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

class UserStoryQualityAssessor:
    """Streamlined user story quality assessment focused on practical criteria."""
    
    def __init__(self):
        # User story format pattern
        self.story_pattern = r'^As an?\s+(.+?),\s*I want\s+(.+?)\s+so that\s+(.+?)[\.\s]*$'
        
        # Given/When/Then pattern
        self.gwt_pattern = r'Given\s+.+?,\s*When\s+.+?,\s*Then\s+.+?'
        
        # Specific role patterns (not generic "user")
        self.specific_roles = ['Urban Commuter', 'College Student', 'Tourist', 'Night Owl', 
                              'Manager', 'Admin', 'Operator', 'Inspector', 'Driver']
        
    def assess_user_story(self, story: Dict[str, Any], feature: Dict[str, Any], 
                         domain: str, product_vision: str) -> QualityAssessment:
        """Assess user story quality based on streamlined criteria."""
        title = story.get('title', '').strip()
        user_story = story.get('user_story', '').strip()
        description = story.get('description', '').strip()
        acceptance_criteria = story.get('acceptance_criteria', [])
        
        # Validate basic structure
        if not title or not user_story or not description:
            return QualityAssessment(
                rating="POOR",
                score=0,
                strengths=[],
                weaknesses=["Missing required fields"],
                specific_issues=["User story must have title, user_story, and description"],
                improvement_suggestions=["Provide all required fields"]
            )
        
        score = 0
        strengths = []
        weaknesses = []
        specific_issues = []
        
        # 1. User Story Format (20 points)
        match = re.match(self.story_pattern, user_story, re.I)
        if match:
            role, goal, benefit = match.groups()
            score += 15
            strengths.append("Proper user story format")
            
            # Check for specific role (not generic "user")
            if any(specific_role.lower() in role.lower() for specific_role in self.specific_roles):
                score += 5
                strengths.append("Uses specific role/persona")
            else:
                weaknesses.append("Role too generic - use specific persona")
        else:
            specific_issues.append("User story doesn't follow 'As a [role], I want [goal] so that [benefit]' format")
        
        # 2. Title Quality (10 points)
        if len(title) <= 60:
            score += 10
            strengths.append("Title length appropriate")
        else:
            specific_issues.append(f"Title too long ({len(title)} chars, max 60)")
        
        # 3. Acceptance Criteria (25 points)
        criteria_count = len(acceptance_criteria)
        if 3 <= criteria_count <= 5:
            score += 10
            strengths.append(f"Has {criteria_count} acceptance criteria")
            
            # Check Given/When/Then format
            gwt_count = sum(1 for ac in acceptance_criteria if re.search(self.gwt_pattern, ac, re.I))
            if gwt_count == criteria_count:
                score += 15
                strengths.append("All criteria use Given/When/Then format")
            elif gwt_count > 0:
                score += 8
                weaknesses.append(f"Only {gwt_count}/{criteria_count} criteria use proper format")
            else:
                specific_issues.append("No criteria use Given/When/Then format")
        else:
            specific_issues.append(f"Must have 3-5 acceptance criteria (has {criteria_count})")
        
        # 4. Description Quality (15 points)
        if description.startswith(user_story):
            score += 10
            strengths.append("Description starts with user story")
        else:
            weaknesses.append("Description should start with the full user story")
        
        if len(description) > len(user_story) + 50:
            score += 5
            strengths.append("Description includes implementation details")
        else:
            weaknesses.append("Description needs more implementation detail")
        
        # 5. Independence (15 points)
        # Check if story seems independently deliverable
        story_points = story.get('story_points', 0)
        if 1 <= story_points <= 8:
            score += 15
            strengths.append("Story size suggests independent delivery")
        else:
            weaknesses.append(f"Story points ({story_points}) suggest scope issues")
        
        # 6. Feature Alignment (15 points)
        feature_text = f"{feature.get('title', '')} {feature.get('description', '')}".lower()
        story_text = f"{title} {user_story} {description}".lower()
        
        feature_keywords = set(re.findall(r'\b\w{4,}\b', feature_text))
        story_keywords = set(re.findall(r'\b\w{4,}\b', story_text))
        overlap = len(feature_keywords & story_keywords)
        
        if overlap >= 5:
            score += 15
            strengths.append("Strong alignment with parent feature")
        elif overlap >= 3:
            score += 8
            weaknesses.append("Moderate feature alignment - strengthen connection")
        else:
            specific_issues.append("Weak connection to parent feature")
        
        # Generate improvement suggestions
        improvement_suggestions = []
        if score < 75:
            if not match:
                improvement_suggestions.append("Rewrite in 'As a [role], I want [goal] so that [benefit]' format")
            if criteria_count < 3 or criteria_count > 5:
                improvement_suggestions.append("Provide exactly 3-5 acceptance criteria")
            if gwt_count < criteria_count:
                improvement_suggestions.append("Use Given/When/Then format for all acceptance criteria")
            if not any(role in user_story for role in self.specific_roles):
                improvement_suggestions.append(f"Use specific role from vision (e.g., {', '.join(self.specific_roles[:3])})")
        
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
    
    def format_assessment_log(self, story: Dict[str, Any], assessment: QualityAssessment, attempt: int) -> str:
        """Format assessment for logging."""
        title = story.get('title', 'Untitled')
        output = f"USER STORY QUALITY ASSESSMENT (Attempt {attempt})\n"
        output += f"Story: {title}\n"
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