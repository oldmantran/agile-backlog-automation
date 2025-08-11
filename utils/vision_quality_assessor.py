"""
Vision Statement Quality Assessor

This module evaluates the quality of product vision statements to ensure they provide
sufficient detail and clarity for generating high-quality work items.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from utils.safe_logger import get_safe_logger


@dataclass
class VisionAssessment:
    """Assessment result for a product vision statement."""
    score: int
    rating: str
    strengths: List[str]
    weaknesses: List[str]
    missing_elements: List[str]
    improvement_suggestions: List[str]
    is_acceptable: bool
    

class VisionQualityAssessor:
    """Assesses the quality of product vision statements."""
    
    def __init__(self):
        self.logger = get_safe_logger(__name__)
        
        # Essential elements of a high-quality vision statement
        self.essential_elements = {
            'vision_statement': {
                'description': 'Clear vision or mission statement',
                'keywords': ['vision', 'mission', 'transform', 'revolutionize', 'empower', 'enable', 'deliver'],
                'weight': 15
            },
            'target_audience': {
                'description': 'Well-defined target users or customers',
                'keywords': ['users', 'customers', 'audience', 'personas', 'segments', 'demographics'],
                'weight': 15
            },
            'core_features': {
                'description': 'Specific features or capabilities',
                'keywords': ['features', 'capabilities', 'functionality', 'modules', 'components'],
                'weight': 20
            },
            'value_proposition': {
                'description': 'Clear value proposition or benefits',
                'keywords': ['value', 'benefits', 'advantages', 'roi', 'proposition', 'outcomes'],
                'weight': 15
            },
            'technical_details': {
                'description': 'Technical implementation details',
                'keywords': ['technology', 'architecture', 'platform', 'integration', 'api', 'infrastructure'],
                'weight': 10
            },
            'business_objectives': {
                'description': 'Business goals or metrics',
                'keywords': ['objectives', 'goals', 'metrics', 'kpis', 'targets', 'milestones'],
                'weight': 10
            },
            'domain_specific': {
                'description': 'Domain-specific terminology and context',
                'keywords': [],  # Evaluated based on domain
                'weight': 15
            }
        }
        
        # Domain-specific keywords for better assessment
        self.domain_keywords = {
            'transportation': ['vehicle', 'route', 'fleet', 'mobility', 'autonomous', 'traffic', 'logistics', 'ride', 'transit'],
            'healthcare': ['patient', 'clinical', 'medical', 'diagnosis', 'treatment', 'ehr', 'hipaa', 'provider'],
            'finance': ['transaction', 'payment', 'banking', 'investment', 'portfolio', 'compliance', 'fintech'],
            'retail': ['inventory', 'customer', 'shopping', 'commerce', 'pos', 'supply chain', 'merchandising'],
            'education': ['student', 'learning', 'curriculum', 'assessment', 'course', 'lms', 'educational'],
            'manufacturing': ['production', 'quality', 'assembly', 'inventory', 'scm', 'erp', 'automation'],
            'real_estate': ['property', 'listing', 'tenant', 'lease', 'mortgage', 'valuation', 'realty'],
            'hospitality': ['guest', 'reservation', 'booking', 'hotel', 'restaurant', 'service', 'accommodation'],
            'energy': ['power', 'renewable', 'grid', 'consumption', 'utility', 'efficiency', 'sustainability'],
            'agriculture': ['farm', 'crop', 'yield', 'harvest', 'irrigation', 'livestock', 'agricultural']
        }
        
        # Minimum acceptable score (same as work items)
        self.minimum_score = 75
        
    def assess_vision(self, vision_text: str, domain: str = 'general') -> VisionAssessment:
        """
        Assess the quality of a product vision statement.
        
        Args:
            vision_text: The product vision text to assess
            domain: The domain/industry context
            
        Returns:
            VisionAssessment with score, rating, and feedback
        """
        if not vision_text or len(vision_text.strip()) < 100:
            return VisionAssessment(
                score=0,
                rating="POOR",
                strengths=[],
                weaknesses=["Vision statement is too short or missing"],
                missing_elements=list(self.essential_elements.keys()),
                improvement_suggestions=["Provide a comprehensive product vision with all essential elements"],
                is_acceptable=False
            )
        
        # Initialize assessment
        total_score = 0
        strengths = []
        weaknesses = []
        missing_elements = []
        
        # Clean the text for analysis
        vision_lower = vision_text.lower()
        
        # 1. Assess length and detail (10 points)
        word_count = len(vision_text.split())
        if word_count >= 500:
            total_score += 10
            strengths.append("Comprehensive and detailed vision")
        elif word_count >= 300:
            total_score += 7
            strengths.append("Good level of detail")
        elif word_count >= 150:
            total_score += 4
            weaknesses.append("Could benefit from more detail")
        else:
            total_score += 1
            weaknesses.append("Vision is too brief - needs significant expansion")
        
        # 2. Assess essential elements
        for element_key, element_info in self.essential_elements.items():
            element_score = 0
            element_found = False
            
            if element_key == 'domain_specific':
                # Special handling for domain-specific content
                if domain in self.domain_keywords:
                    domain_terms = self.domain_keywords[domain]
                    found_terms = [term for term in domain_terms if term in vision_lower]
                    if len(found_terms) >= 3:
                        element_score = element_info['weight']
                        strengths.append(f"Strong {domain} domain terminology")
                        element_found = True
                    elif len(found_terms) >= 1:
                        element_score = element_info['weight'] * 0.5
                        weaknesses.append(f"Limited {domain} domain terminology")
                        element_found = True
            else:
                # Check for keywords
                keywords_found = [kw for kw in element_info['keywords'] if kw in vision_lower]
                if keywords_found:
                    element_found = True
                    # Check content depth around keywords
                    if self._check_element_depth(vision_text, keywords_found):
                        element_score = element_info['weight']
                        strengths.append(f"Clear {element_info['description']}")
                    else:
                        element_score = element_info['weight'] * 0.5
                        weaknesses.append(f"{element_info['description']} lacks detail")
            
            if not element_found:
                missing_elements.append(element_info['description'])
                
            total_score += element_score
        
        # 3. Check for specific sections or structure (10 points)
        structure_score = 0
        if any(marker in vision_text for marker in ['##', '**', '###', '1.', '•', '-']):
            structure_score += 5
            strengths.append("Well-structured with clear sections")
        
        if re.search(r'\b(goal|objective|metric|kpi)\b.*\d+', vision_lower):
            structure_score += 5
            strengths.append("Contains measurable objectives")
        else:
            weaknesses.append("Lacks measurable goals or metrics")
            
        total_score += structure_score
        
        # 4. Check for actionable content (10 points)
        action_words = ['implement', 'develop', 'create', 'build', 'deploy', 'integrate', 'automate', 'optimize']
        action_count = sum(1 for word in action_words if word in vision_lower)
        if action_count >= 5:
            total_score += 10
            strengths.append("Contains actionable implementation details")
        elif action_count >= 2:
            total_score += 5
            weaknesses.append("Could use more actionable language")
        else:
            weaknesses.append("Lacks actionable implementation details")
        
        # 5. Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            missing_elements, weaknesses, domain, word_count
        )
        
        # Cap total score at 100
        total_score = min(total_score, 100)
        
        # Calculate final rating
        rating = self._get_rating(total_score)
        is_acceptable = total_score >= self.minimum_score
        
        return VisionAssessment(
            score=total_score,
            rating=rating,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_elements=missing_elements,
            improvement_suggestions=improvement_suggestions,
            is_acceptable=is_acceptable
        )
    
    def _check_element_depth(self, text: str, keywords: List[str]) -> bool:
        """Check if keywords are supported by substantial content."""
        for keyword in keywords:
            # Find sentences containing the keyword
            sentences = [s for s in text.split('.') if keyword in s.lower()]
            for sentence in sentences:
                # Check if sentence has meaningful content (more than just the keyword)
                words = sentence.split()
                if len(words) > 10:  # Substantial sentence
                    return True
        return False
    
    def _generate_improvement_suggestions(self, missing_elements: List[str], 
                                        weaknesses: List[str], domain: str, 
                                        word_count: int) -> List[str]:
        """Generate specific improvement suggestions."""
        suggestions = []
        
        # Address missing elements
        if missing_elements:
            suggestions.append(f"Add the following missing elements: {', '.join(missing_elements[:3])}")
        
        # Address length issues
        if word_count < 300:
            suggestions.append("Expand the vision to at least 300-500 words for comprehensive coverage")
        
        # Domain-specific suggestions
        if domain != 'general' and f"Limited {domain} domain terminology" in ' '.join(weaknesses):
            suggestions.append(f"Include more {domain}-specific terminology and use cases")
        
        # Structure suggestions
        if "Well-structured" not in ' '.join(weaknesses):
            suggestions.append("Organize content with clear sections (Vision, Features, Value Proposition, etc.)")
        
        # Metrics suggestions
        if "measurable" in ' '.join(weaknesses).lower():
            suggestions.append("Add specific, measurable objectives with timelines and success metrics")
        
        # Technical details
        if any("technical" in elem for elem in missing_elements):
            suggestions.append("Include technical architecture, integrations, and implementation approach")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _get_rating(self, score: int) -> str:
        """Get rating based on score."""
        if score >= 80:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "FAIR"
        else:
            return "POOR"
    
    def format_assessment_report(self, assessment: VisionAssessment) -> str:
        """Format assessment results for display."""
        report = f"""
VISION STATEMENT QUALITY ASSESSMENT
{'='*60}
Score: {assessment.score}/100
Rating: {assessment.rating}
Acceptable: {'YES' if assessment.is_acceptable else 'NO (Minimum: 75)'}

STRENGTHS ({len(assessment.strengths)}):
{chr(10).join('+ ' + s for s in assessment.strengths) if assessment.strengths else '  None identified'}

WEAKNESSES ({len(assessment.weaknesses)}):
{chr(10).join('- ' + w for w in assessment.weaknesses) if assessment.weaknesses else '  None identified'}

MISSING ELEMENTS ({len(assessment.missing_elements)}):
{chr(10).join('! ' + m for m in assessment.missing_elements) if assessment.missing_elements else '  All essential elements present'}

IMPROVEMENT SUGGESTIONS:
{chr(10).join(f'{i+1}. ' + s for i, s in enumerate(assessment.improvement_suggestions)) if assessment.improvement_suggestions else '  No improvements needed'}
"""
        return report.strip()