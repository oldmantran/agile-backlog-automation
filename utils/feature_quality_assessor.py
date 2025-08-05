"""
Feature Quality Assessment Module
Evaluates feature quality and determines if they meet EXCELLENT standards before proceeding.
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class FeatureQualityAssessment:
    rating: str  # EXCELLENT, GOOD, FAIR, POOR
    score: int   # 0-100
    strengths: List[str]
    weaknesses: List[str]
    specific_issues: List[str]
    improvement_suggestions: List[str]

class FeatureQualityAssessor:
    """Assesses feature quality based on comprehensive criteria."""
    
    def __init__(self):
        # Domain-specific terms that should appear in features
        self.domain_indicators = {
            'healthcare': ['patient', 'medical', 'clinical', 'health', 'ehr', 'hipaa', 'diagnosis', 'treatment', 'care', 'provider'],
            'finance': ['investment', 'portfolio', 'financial', 'trading', 'market', 'risk', 'brokerage', 'wealth', 'asset', 'capital'],
            'education': ['student', 'learning', 'education', 'teacher', 'classroom', 'curriculum', 'academic', 'school', 'instruction'],
            'logistics': ['warehouse', 'dock', 'asset', 'gate', 'door', 'motor', 'lift', 'surveillance', 'inspection', 'monitoring', 'maintenance'],
            'retail': ['customer', 'product', 'inventory', 'sales', 'purchase', 'catalog', 'order', 'payment', 'checkout'],
            'manufacturing': ['production', 'assembly', 'quality', 'equipment', 'process', 'workflow', 'machinery', 'automation']
        }
        
        # Technical terms that indicate good implementation guidance
        self.technical_terms = ['api', 'database', 'interface', 'dashboard', 'analytics', 'integration', 'authentication', 'notification']
        
        # User-focused terms
        self.user_terms = ['user', 'manager', 'admin', 'operator', 'staff', 'team', 'customer', 'client']
        
    def assess_feature(self, feature: Dict[str, Any], epic_context: Dict[str, Any], domain: str, product_vision: str) -> FeatureQualityAssessment:
        """Comprehensive feature quality assessment."""
        title = feature.get('title', '').strip()
        description = feature.get('description', '').strip()
        
        if not title or not description:
            return FeatureQualityAssessment(
                rating="POOR",
                score=0,
                strengths=[],
                weaknesses=["Missing title or description"],
                specific_issues=["Feature is incomplete"],
                improvement_suggestions=["Ensure both title and description are provided"]
            )
        
        strengths = []
        weaknesses = []
        specific_issues = []
        suggestions = []
        score = 0
        
        # 1. Epic Alignment Assessment (25 points)
        epic_score, epic_strengths, epic_issues = self._assess_epic_alignment(
            title, description, epic_context
        )
        score += epic_score
        strengths.extend(epic_strengths)
        specific_issues.extend(epic_issues)
        
        # 2. Domain Specificity Assessment (20 points)
        domain_score, domain_strengths, domain_issues = self._assess_domain_specificity(
            title, description, domain, product_vision
        )
        score += domain_score
        strengths.extend(domain_strengths)
        specific_issues.extend(domain_issues)
        
        # 3. Technical Implementability Assessment (20 points)
        tech_score, tech_strengths, tech_issues = self._assess_technical_implementability(
            title, description
        )
        score += tech_score
        strengths.extend(tech_strengths)
        specific_issues.extend(tech_issues)
        
        # 4. User Story Readiness Assessment (20 points)
        story_score, story_strengths, story_issues = self._assess_user_story_readiness(
            description
        )
        score += story_score
        strengths.extend(story_strengths)
        specific_issues.extend(story_issues)
        
        # 5. Completeness Assessment (15 points)
        completeness_score, completeness_strengths, completeness_issues = self._assess_completeness(
            feature
        )
        score += completeness_score
        strengths.extend(completeness_strengths)
        specific_issues.extend(completeness_issues)
        
        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(specific_issues, domain, epic_context, product_vision)
        
        # Determine rating based on score
        if score >= 90:
            rating = "EXCELLENT"
        elif score >= 75:
            rating = "GOOD"
        elif score >= 50:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        return FeatureQualityAssessment(
            rating=rating,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            specific_issues=specific_issues,
            improvement_suggestions=suggestions
        )
    
    def _assess_epic_alignment(self, title: str, description: str, epic_context: Dict[str, Any]) -> Tuple[int, List[str], List[str]]:
        """Assess how well the feature aligns with its parent epic (25 points max)."""
        combined_text = f"{title.lower()} {description.lower()}"
        strengths = []
        issues = []
        score = 0
        
        epic_title = epic_context.get('title', '').lower()
        epic_description = epic_context.get('description', '').lower()
        
        # Check alignment with epic title concepts (10 points)
        epic_key_words = [word for word in epic_title.split() if len(word) > 3]
        aligned_words = sum(1 for word in epic_key_words if word in combined_text)
        
        if len(epic_key_words) > 0:
            alignment_ratio = aligned_words / len(epic_key_words)
            if alignment_ratio >= 0.3:  # 30% of epic key words found
                score += 10
                strengths.append("Strong alignment with epic title concepts")
            elif alignment_ratio >= 0.1:
                score += 5
                strengths.append("Some alignment with epic title")
            else:
                issues.append("Poor alignment with parent epic title")
        
        # Check for epic description concepts (15 points)
        epic_concepts = self._extract_key_concepts(epic_description)
        feature_concepts = self._extract_key_concepts(combined_text)
        
        concept_overlap = len(set(epic_concepts) & set(feature_concepts))
        if concept_overlap >= 3:
            score += 15
            strengths.append("Excellent conceptual alignment with epic")
        elif concept_overlap >= 1:
            score += 10
            strengths.append("Good conceptual alignment with epic")
        else:
            issues.append("Lacks conceptual connection to parent epic")
        
        return score, strengths, issues
    
    def _assess_domain_specificity(self, title: str, description: str, domain: str, product_vision: str) -> Tuple[int, List[str], List[str]]:
        """Assess domain specificity (20 points max)."""
        combined_text = f"{title.lower()} {description.lower()}"
        strengths = []
        issues = []
        score = 0
        
        # Check for domain-specific terms (15 points)
        domain_terms = self.domain_indicators.get(domain.lower(), [])
        found_terms = [term for term in domain_terms if term in combined_text]
        
        if len(found_terms) >= 2:
            score += 15
            strengths.append(f"Strong domain specificity: {len(found_terms)} terms found")
        elif len(found_terms) >= 1:
            score += 10
            strengths.append(f"Moderate domain specificity: {len(found_terms)} terms found")
        else:
            issues.append("Lacks domain-specific terminology")
        
        # Check vision alignment (5 points)
        vision_lower = product_vision.lower()
        vision_key_phrases = self._extract_key_phrases(vision_lower)
        aligned_phrases = [phrase for phrase in vision_key_phrases if phrase in combined_text]
        
        if len(aligned_phrases) >= 1:
            score += 5
            strengths.append("Aligned with product vision concepts")
        else:
            issues.append("No clear connection to product vision")
        
        return score, strengths, issues
    
    def _assess_technical_implementability(self, title: str, description: str) -> Tuple[int, List[str], List[str]]:
        """Assess technical implementability (20 points max)."""
        combined_text = f"{title.lower()} {description.lower()}"
        strengths = []
        issues = []
        score = 0
        
        # Check for technical implementation hints (15 points)
        found_tech = [term for term in self.technical_terms if term in combined_text]
        if len(found_tech) >= 2:
            score += 15
            strengths.append(f"Clear technical direction: {', '.join(found_tech)}")
        elif len(found_tech) >= 1:
            score += 10
            strengths.append(f"Some technical guidance: {', '.join(found_tech)}")
        else:
            issues.append("Lacks technical implementation guidance")
        
        # Check for user interface mentions (5 points)
        ui_terms = ['interface', 'dashboard', 'screen', 'form', 'button', 'menu', 'display']
        found_ui = [term for term in ui_terms if term in combined_text]
        if found_ui:
            score += 5
            strengths.append("Includes user interface considerations")
        else:
            issues.append("No user interface guidance provided")
        
        return score, strengths, issues
    
    def _assess_user_story_readiness(self, description: str) -> Tuple[int, List[str], List[str]]:
        """Assess readiness for user story decomposition (20 points max)."""
        desc_lower = description.lower()
        strengths = []
        issues = []
        score = 0
        
        # Check for user-focused language (10 points)
        found_users = [term for term in self.user_terms if term in desc_lower]
        if len(found_users) >= 2:
            score += 10
            strengths.append("Clear user focus with multiple user types")
        elif len(found_users) >= 1:
            score += 5
            strengths.append("Some user focus identified")
        else:
            issues.append("Lacks clear user perspective")
        
        # Check for action-oriented language (10 points)
        action_verbs = ['create', 'manage', 'monitor', 'track', 'analyze', 'generate', 'process', 'configure', 'view', 'update']
        found_actions = [verb for verb in action_verbs if verb in desc_lower]
        if len(found_actions) >= 3:
            score += 10
            strengths.append("Rich actionable functionality described")
        elif len(found_actions) >= 1:
            score += 5
            strengths.append("Some actionable elements present")
        else:
            issues.append("Lacks clear actionable functionality")
        
        return score, strengths, issues
    
    def _assess_completeness(self, feature: Dict[str, Any]) -> Tuple[int, List[str], List[str]]:
        """Assess feature completeness (15 points max)."""
        strengths = []
        issues = []
        score = 0
        
        # Check required fields (10 points)
        required_score = 0
        if feature.get('title') and len(feature['title'].strip()) > 0:
            required_score += 2
        if feature.get('description') and len(feature['description'].strip()) >= 20:
            required_score += 4
            strengths.append("Comprehensive description provided")
        elif feature.get('description') and len(feature['description'].strip()) >= 10:
            required_score += 2
            strengths.append("Adequate description length")
        else:
            issues.append("Description too brief for user story decomposition")
        
        if feature.get('priority') in ['High', 'Medium', 'Low']:
            required_score += 2
        else:
            issues.append("Missing or invalid priority")
        
        if feature.get('estimated_complexity') in ['XS', 'S', 'M', 'L', 'XL']:
            required_score += 2
        else:
            issues.append("Missing or invalid complexity estimate")
        
        score += required_score
        
        # Check for additional quality fields (5 points)
        if feature.get('acceptance_criteria') and len(feature.get('acceptance_criteria', [])) > 0:
            score += 3
            strengths.append("Includes acceptance criteria")
        
        if feature.get('business_value'):
            score += 2
            strengths.append("Business value clearly stated")
        
        return score, strengths, issues
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text."""
        # Simple concept extraction - meaningful words > 4 characters
        words = re.findall(r'\b\w{4,}\b', text.lower())
        # Filter out common words
        stop_words = {'that', 'this', 'with', 'from', 'they', 'them', 'will', 'have', 'been', 'were', 'would', 'could', 'should'}
        return [word for word in words if word not in stop_words][:10]
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        # Simple extraction of 2-3 word phrases
        phrases = re.findall(r'\b\w+\s+\w+(?:\s+\w+)?\b', text)
        # Filter for meaningful phrases
        stop_patterns = ['the', 'and', 'for', 'with', 'this', 'that', 'are', 'can', 'will', 'has', 'have']
        return [phrase for phrase in phrases if not any(stop in phrase for stop in stop_patterns)][:8]
    
    def _generate_improvement_suggestions(self, issues: List[str], domain: str, epic_context: Dict[str, Any], product_vision: str) -> List[str]:
        """Generate specific improvement suggestions based on identified issues."""
        suggestions = []
        
        if "Poor alignment with parent epic title" in issues:
            epic_title = epic_context.get('title', 'the epic')
            suggestions.append(f"Align feature more closely with epic: '{epic_title}'")
        
        if "Lacks conceptual connection to parent epic" in issues:
            suggestions.append("Reference key concepts from the parent epic description")
        
        if "Lacks domain-specific terminology" in issues:
            domain_terms = self.domain_indicators.get(domain.lower(), [])
            suggestions.append(f"Include domain-specific terms like: {', '.join(domain_terms[:4])}")
        
        if "No clear connection to product vision" in issues:
            suggestions.append("Reference specific elements from the product vision statement")
        
        if "Lacks technical implementation guidance" in issues:
            suggestions.append("Add technical details like API endpoints, database requirements, or integration points")
        
        if "No user interface guidance provided" in issues:
            suggestions.append("Specify user interface components like dashboards, forms, or displays")
        
        if "Lacks clear user perspective" in issues:
            suggestions.append("Identify specific user types who will interact with this feature")
        
        if "Lacks clear actionable functionality" in issues:
            suggestions.append("Use action verbs to describe what users can do with this feature")
        
        if "Description too brief for user story decomposition" in issues:
            suggestions.append("Expand description with more functional details and user interactions")
        
        return suggestions
    
    def format_assessment_log(self, feature: Dict[str, Any], assessment: FeatureQualityAssessment, attempt: int) -> str:
        """Format assessment for logging."""
        title = feature.get('title', 'Unknown')
        
        log_lines = [
            f"FEATURE QUALITY ASSESSMENT (Attempt {attempt})",
            f"Feature: {title}",
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