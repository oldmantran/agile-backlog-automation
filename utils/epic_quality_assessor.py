"""
Epic Quality Assessment Module
Evaluates epic quality and determines if they meet EXCELLENT standards before proceeding.
"""

import re
from typing import Dict, List, Tuple, Any
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
    """Assesses epic quality based on comprehensive criteria."""
    
    def __init__(self):
        # Vision-specific terms that should appear in domain contexts
        self.domain_indicators = {
            'healthcare': ['patient', 'medical', 'clinical', 'health', 'ehr', 'hipaa', 'diagnosis', 'treatment', 'care', 'provider'],
            'finance': ['investment', 'portfolio', 'financial', 'trading', 'market', 'risk', 'brokerage', 'wealth', 'asset', 'capital'],
            'education': ['student', 'learning', 'education', 'teacher', 'classroom', 'curriculum', 'academic', 'school', 'instruction'],
            'logistics': ['warehouse', 'dock', 'asset', 'gate', 'door', 'motor', 'lift', 'surveillance', 'inspection', 'monitoring', 'maintenance'],
            'retail': ['customer', 'product', 'inventory', 'sales', 'purchase', 'catalog', 'order', 'payment', 'checkout'],
            'manufacturing': ['production', 'assembly', 'quality', 'equipment', 'process', 'workflow', 'machinery', 'automation']
        }
        
        # Generic terms that indicate lack of specificity
        self.generic_terms = ['system', 'platform', 'management', 'tracking', 'application', 'solution', 'tool', 'interface']
        
        # Technology indicators (positive)
        self.technology_terms = ['ai-powered', 'cloud-based', 'real-time', 'automated', 'api', 'dashboard', 'analytics', 'integration']
        
    def assess_epic(self, epic: Dict[str, Any], domain: str, product_vision: str) -> QualityAssessment:
        """Comprehensive epic quality assessment."""
        title = epic.get('title', '').strip()
        description = epic.get('description', '').strip()
        
        if not title or not description:
            return QualityAssessment(
                rating="POOR",
                score=0,
                strengths=[],
                weaknesses=["Missing title or description"],
                specific_issues=["Epic is incomplete"],
                improvement_suggestions=["Ensure both title and description are provided"]
            )
        
        strengths = []
        weaknesses = []
        specific_issues = []
        suggestions = []
        score = 0
        
        # 1. Domain Specificity Assessment (25 points)
        domain_score, domain_strengths, domain_issues = self._assess_domain_specificity(
            title, description, domain, product_vision
        )
        score += domain_score
        strengths.extend(domain_strengths)
        specific_issues.extend(domain_issues)
        
        # 2. Technical Clarity Assessment (20 points)
        tech_score, tech_strengths, tech_issues = self._assess_technical_clarity(
            title, description
        )
        score += tech_score
        strengths.extend(tech_strengths)
        specific_issues.extend(tech_issues)
        
        # 3. Business Value Assessment (20 points)
        value_score, value_strengths, value_issues = self._assess_business_value(
            description
        )
        score += value_score
        strengths.extend(value_strengths)
        specific_issues.extend(value_issues)
        
        # 4. Actionability Assessment (15 points)
        action_score, action_strengths, action_issues = self._assess_actionability(
            description
        )
        score += action_score
        strengths.extend(action_strengths)
        specific_issues.extend(action_issues)
        
        # 5. Context Completeness Assessment (20 points)
        context_score, context_strengths, context_issues = self._assess_context_completeness(
            title, description, product_vision
        )
        score += context_score
        strengths.extend(context_strengths)
        specific_issues.extend(context_issues)
        
        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(specific_issues, domain, product_vision)
        
        # Determine rating based on score
        if score >= 80:
            rating = "EXCELLENT"
        elif score >= 65:
            rating = "GOOD"
        elif score >= 45:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        return QualityAssessment(
            rating=rating,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            specific_issues=specific_issues,
            improvement_suggestions=suggestions
        )
    
    def _assess_domain_specificity(self, title: str, description: str, domain: str, product_vision: str) -> Tuple[int, List[str], List[str]]:
        """Assess how domain-specific the epic is (25 points max)."""
        combined_text = f"{title.lower()} {description.lower()}"
        strengths = []
        issues = []
        score = 0
        
        # Check for domain-specific terms (15 points)
        domain_terms = self.domain_indicators.get(domain.lower(), [])
        found_terms = [term for term in domain_terms if term in combined_text]
        
        if len(found_terms) >= 3:
            score += 15
            strengths.append(f"Strong domain specificity: {len(found_terms)} domain terms found")
        elif len(found_terms) >= 1:
            score += 10
            strengths.append(f"Moderate domain specificity: {len(found_terms)} domain terms found")
        else:
            issues.append("Lacks domain-specific terminology")
        
        # Check for vision alignment (10 points)
        vision_lower = product_vision.lower()
        vision_key_phrases = self._extract_key_phrases(vision_lower)
        aligned_phrases = [phrase for phrase in vision_key_phrases if phrase in combined_text]
        
        if len(aligned_phrases) >= 2:
            score += 10
            strengths.append("Well-aligned with product vision key concepts")
        elif len(aligned_phrases) >= 1:
            score += 5
            strengths.append("Partially aligned with product vision")
        else:
            issues.append("Poor alignment with product vision key concepts")
        
        return score, strengths, issues
    
    def _assess_technical_clarity(self, title: str, description: str) -> Tuple[int, List[str], List[str]]:
        """Assess technical clarity and implementation hints (20 points max)."""
        combined_text = f"{title.lower()} {description.lower()}"
        strengths = []
        issues = []
        score = 0
        
        # Check for technology indicators (10 points)
        found_tech = [term for term in self.technology_terms if term in combined_text]
        if len(found_tech) >= 2:
            score += 10
            strengths.append(f"Clear technology direction: {', '.join(found_tech)}")
        elif len(found_tech) >= 1:
            score += 5
            strengths.append(f"Some technology clarity: {', '.join(found_tech)}")
        else:
            issues.append("Lacks specific technology or implementation approach")
        
        # Check for architectural hints (10 points)
        architectural_terms = ['platform', 'engine', 'system', 'service', 'api', 'interface', 'framework']
        found_arch = [term for term in architectural_terms if term in combined_text]
        if found_arch:
            score += 10
            strengths.append("Provides architectural direction")
        else:
            issues.append("Missing architectural or structural guidance")
        
        return score, strengths, issues
    
    def _assess_business_value(self, description: str) -> Tuple[int, List[str], List[str]]:
        """Assess business value clarity (20 points max)."""
        desc_lower = description.lower()
        strengths = []
        issues = []
        score = 0
        
        # Check for value indicators (15 points)
        value_terms = ['optimize', 'improve', 'enhance', 'reduce', 'increase', 'minimize', 'maximize', 'efficient', 'effective']
        found_value = [term for term in value_terms if term in desc_lower]
        
        if len(found_value) >= 2:
            score += 15
            strengths.append("Clear business value proposition")
        elif len(found_value) >= 1:
            score += 10
            strengths.append("Some business value indicated")
        else:
            issues.append("Unclear business value or benefits")
        
        # Check for user impact (5 points)
        user_terms = ['user', 'provider', 'manager', 'team', 'staff', 'customer', 'client']
        if any(term in desc_lower for term in user_terms):
            score += 5
            strengths.append("Identifies target users")
        else:
            issues.append("Target users not clearly identified")
        
        return score, strengths, issues
    
    def _assess_actionability(self, description: str) -> Tuple[int, List[str], List[str]]:
        """Assess how actionable the description is for feature decomposition (15 points max)."""
        desc_lower = description.lower()
        strengths = []
        issues = []
        score = 0
        
        # Check for action verbs (10 points)
        action_verbs = ['develop', 'create', 'build', 'implement', 'design', 'integrate', 'establish', 'provide', 'enable']
        found_actions = [verb for verb in action_verbs if verb in desc_lower]
        
        if len(found_actions) >= 2:
            score += 10
            strengths.append("Multiple clear action items identified")
        elif len(found_actions) >= 1:
            score += 5
            strengths.append("Some actionable elements present")
        else:
            issues.append("Lacks clear actionable directives")
        
        # Check for scope clarity (5 points)
        if len(description.split()) >= 20:  # Sufficient detail
            score += 5
            strengths.append("Sufficient detail for feature decomposition")
        else:
            issues.append("Description too brief for proper feature breakdown")
        
        return score, strengths, issues
    
    def _assess_context_completeness(self, title: str, description: str, product_vision: str) -> Tuple[int, List[str], List[str]]:
        """Assess context completeness relative to vision (20 points max)."""
        strengths = []
        issues = []
        score = 0
        
        # Title quality (5 points)
        if len(title.split()) >= 3 and len(title) <= 60:
            score += 5
            strengths.append("Well-structured title")
        else:
            issues.append("Title should be 3+ words and under 60 characters")
        
        # Description completeness (15 points)
        if len(description.split()) >= 15:
            score += 10
            strengths.append("Comprehensive description")
        elif len(description.split()) >= 8:
            score += 5
            strengths.append("Adequate description length")
        else:
            issues.append("Description needs more detail")
        
        # Context preservation (5 points)
        vision_nouns = self._extract_key_nouns(product_vision.lower())
        desc_lower = description.lower()
        preserved_context = sum(1 for noun in vision_nouns if noun in desc_lower)
        
        if preserved_context >= 3:
            score += 5
            strengths.append("Preserves key vision context")
        else:
            issues.append("Loses important context from product vision")
        
        return score, strengths, issues
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from vision text."""
        # Simple extraction of 2-3 word phrases that might be important
        phrases = re.findall(r'\b\w+\s+\w+(?:\s+\w+)?\b', text)
        # Filter for meaningful phrases (not common stop words)
        stop_patterns = ['the', 'and', 'for', 'with', 'this', 'that', 'are', 'can', 'will', 'has', 'have']
        return [phrase for phrase in phrases if not any(stop in phrase for stop in stop_patterns)][:10]
    
    def _extract_key_nouns(self, text: str) -> List[str]:
        """Extract key nouns from text."""
        # Simple noun extraction - words that don't match common verbs/adjectives
        words = text.split()
        # Filter for likely nouns (basic heuristic)
        likely_nouns = [word for word in words if len(word) > 3 and 
                       not word.endswith('ing') and not word.endswith('ed') and
                       word not in ['this', 'that', 'with', 'from', 'they', 'them', 'will', 'have', 'been']]
        return list(set(likely_nouns))[:15]
    
    def _generate_improvement_suggestions(self, issues: List[str], domain: str, product_vision: str) -> List[str]:
        """Generate specific improvement suggestions based on identified issues."""
        suggestions = []
        
        if "Lacks domain-specific terminology" in issues:
            domain_terms = self.domain_indicators.get(domain.lower(), [])
            suggestions.append(f"Include domain-specific terms like: {', '.join(domain_terms[:5])}")
        
        if "Poor alignment with product vision key concepts" in issues:
            suggestions.append("Reference specific elements from the product vision statement")
        
        if "Lacks specific technology or implementation approach" in issues:
            suggestions.append("Specify technology approach (AI-powered, cloud-based, real-time, etc.)")
        
        if "Unclear business value or benefits" in issues:
            suggestions.append("Clearly state the business benefits and value proposition")
        
        if "Lacks clear actionable directives" in issues:
            suggestions.append("Use action verbs and specify what will be developed/implemented")
        
        if "Description too brief for proper feature breakdown" in issues:
            suggestions.append("Expand description with more implementation details and context")
        
        return suggestions
    
    def format_assessment_log(self, epic: Dict[str, Any], assessment: QualityAssessment, attempt: int) -> str:
        """Format assessment for logging."""
        title = epic.get('title', 'Unknown')
        
        log_lines = [
            f"EPIC QUALITY ASSESSMENT (Attempt {attempt})",
            f"Epic: {title}",
            f"Rating: {assessment.rating} ({assessment.score}/100)",
            ""
        ]
        
        if assessment.strengths:
            log_lines.append("+ Strengths:")
            for strength in assessment.strengths:
                log_lines.append(f"  - {strength}")
            log_lines.append("")
        
        if assessment.specific_issues:
            log_lines.append("- Issues:")
            for issue in assessment.specific_issues:
                log_lines.append(f"  - {issue}")
            log_lines.append("")
        
        if assessment.improvement_suggestions:
            log_lines.append("* Improvement Suggestions:")
            for suggestion in assessment.improvement_suggestions:
                log_lines.append(f"  - {suggestion}")
            log_lines.append("")
        
        return "\n".join(log_lines)