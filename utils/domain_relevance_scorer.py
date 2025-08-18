"""
Domain Relevance Scorer

Provides flexible domain relevance scoring for work items that doesn't 
automatically fail items for missing specific domain terms.
"""

from typing import Dict, List, Tuple
from config.domain_knowledge import get_domain_knowledge, is_infrastructure_work_item

class DomainRelevanceScorer:
    """Scores work items for domain relevance using flexible criteria."""
    
    def __init__(self):
        self.scoring_weights = {
            "primary_terms": 10,      # Uses exact domain terms
            "secondary_terms": 8,     # Related domain concepts
            "user_personas": 10,      # Domain-specific users
            "problem_domain": 5,      # Addresses domain problems
            "technical_fit": 5,       # Uses appropriate tech
            "infrastructure": 7       # Infrastructure items get base score
        }
        
    def score_domain_relevance(self, work_item: Dict, domain_key: str, work_item_type: str = "epic") -> Tuple[int, List[str]]:
        """
        Score a work item for domain relevance.
        
        Returns:
            Tuple of (score, feedback_messages)
        """
        title = work_item.get('title', '')
        description = work_item.get('description', '')
        combined_text = f"{title} {description}".lower()
        
        # Check if it's infrastructure/platform work
        if is_infrastructure_work_item(title, description):
            return self._score_infrastructure_item(work_item, domain_key)
        
        # Get domain knowledge
        domain = get_domain_knowledge(domain_key)
        if not domain:
            # Unknown domain - be lenient
            return (15, ["Domain not fully configured - using basic scoring"])
        
        score = 0
        feedback = []
        
        # Check primary terms (10 points max)
        primary_matches = self._count_term_matches(combined_text, domain.get('primary_terms', []))
        if primary_matches > 0:
            term_score = min(10, 5 + primary_matches * 2)  # 5 base + 2 per match, max 10
            score += term_score
            feedback.append(f"Uses {primary_matches} primary domain terms (+{term_score})")
        
        # Check secondary terms (8 points max)
        secondary_matches = self._count_term_matches(combined_text, domain.get('secondary_terms', []))
        if secondary_matches > 0:
            term_score = min(8, 4 + secondary_matches * 2)  # 4 base + 2 per match, max 8
            score += term_score
            feedback.append(f"Uses {secondary_matches} related domain concepts (+{term_score})")
        
        # Check user personas (10 points max)
        persona_matches = self._count_persona_matches(combined_text, domain.get('user_personas', []))
        if persona_matches > 0:
            persona_score = min(10, 5 + persona_matches * 5)  # 5 base + 5 per match, max 10
            score += persona_score
            feedback.append(f"References {persona_matches} domain user types (+{persona_score})")
        
        # Check if it addresses domain problems (5 points max)
        problem_matches = self._count_term_matches(combined_text, domain.get('problems', []))
        if problem_matches > 0:
            problem_score = min(5, problem_matches * 2)
            score += problem_score
            feedback.append(f"Addresses domain-specific problems (+{problem_score})")
        
        # Check technical fit (5 points max)
        system_matches = self._count_term_matches(combined_text, domain.get('systems', []))
        if system_matches > 0:
            tech_score = min(5, system_matches * 2)
            score += tech_score
            feedback.append(f"Uses domain-appropriate technology (+{tech_score})")
        
        # Minimum score threshold - don't completely fail items
        if score == 0:
            # Give partial credit if it at least seems relevant
            if self._has_general_relevance(combined_text, domain_key):
                score = 5
                feedback.append("Shows general domain relevance (+5)")
            else:
                score = 3
                feedback.append("Limited domain terminology used (+3)")
        
        return (score, feedback)
    
    def _score_infrastructure_item(self, work_item: Dict, domain_key: str) -> Tuple[int, List[str]]:
        """Score infrastructure/platform items differently."""
        title = work_item.get('title', '')
        description = work_item.get('description', '')
        
        score = self.scoring_weights['infrastructure']
        feedback = ["Infrastructure/platform work item - domain terms not required (+7)"]
        
        # Check if it at least mentions relevant users
        domain = get_domain_knowledge(domain_key)
        combined_text = f"{title} {description}".lower()
        
        persona_matches = self._count_persona_matches(combined_text, domain.get('user_personas', []))
        if persona_matches > 0:
            score += 3
            feedback.append(f"References domain users in infrastructure context (+3)")
        
        return (score, feedback)
    
    def _count_term_matches(self, text: str, terms: List[str]) -> int:
        """Count how many terms appear in the text."""
        if not terms:
            return 0
        
        matches = 0
        for term in terms:
            # Check for word boundaries to avoid partial matches
            if term.lower() in text:
                matches += 1
        
        return matches
    
    def _count_persona_matches(self, text: str, personas: List[str]) -> int:
        """Count how many user personas are referenced."""
        if not personas:
            return 0
        
        matches = 0
        for persona in personas:
            # Handle variations (e.g., "Grid Operator" vs "Grid Operators")
            singular = persona.lower().rstrip('s')
            plural = persona.lower()
            
            if singular in text or plural in text:
                matches += 1
        
        return matches
    
    def _has_general_relevance(self, text: str, domain_key: str) -> bool:
        """Check if text has general relevance to the domain."""
        # Domain-specific general relevance checks
        general_relevance = {
            "energy": ["power", "utility", "electric", "energy"],
            "healthcare": ["health", "medical", "care", "treatment"],
            "finance": ["financial", "money", "payment", "account"],
            "retail": ["store", "shop", "product", "customer"],
            "education": ["learn", "teach", "student", "course"],
            "manufacturing": ["produce", "factory", "assembly", "build"]
        }
        
        relevant_terms = general_relevance.get(domain_key, [])
        return any(term in text for term in relevant_terms)
    
    def get_domain_relevance_report(self, work_item: Dict, domain_key: str) -> Dict:
        """Generate a detailed domain relevance report."""
        score, feedback = self.score_domain_relevance(work_item, domain_key)
        
        # Calculate percentage (assuming max possible score is 38)
        max_possible = sum(self.scoring_weights.values()) - self.scoring_weights['infrastructure']
        percentage = (score / max_possible) * 100
        
        return {
            "score": score,
            "percentage": round(percentage, 1),
            "feedback": feedback,
            "is_infrastructure": is_infrastructure_work_item(
                work_item.get('title', ''), 
                work_item.get('description', '')
            ),
            "recommendation": self._get_recommendation(score, percentage)
        }
    
    def _get_recommendation(self, score: int, percentage: float) -> str:
        """Get recommendation based on score."""
        if percentage >= 60:
            return "Strong domain alignment"
        elif percentage >= 40:
            return "Acceptable domain alignment"
        elif percentage >= 20:
            return "Consider adding more domain-specific details"
        else:
            return "Low domain alignment - review if this item belongs to this domain"