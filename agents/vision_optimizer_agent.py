import json
import re
from typing import Dict, List, Any, Optional, Tuple
from agents.base_agent import Agent
from config.config_loader import Config
from utils.vision_quality_assessor import VisionQualityAssessor
from utils.safe_logger import get_safe_logger


class VisionOptimizerAgent(Agent):
    """
    Agent responsible for optimizing product vision statements to improve work item generation quality.
    Takes an existing vision and optimizes it based on selected domains with weighted importance.
    """
    
    def __init__(self, config: Config, user_id: str = None):
        super().__init__("vision_optimizer_agent", config, user_id)
        self.vision_assessor = VisionQualityAssessor()
        self.logger = get_safe_logger(__name__)
        
    def optimize_vision(self, original_vision: str, domains: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize a product vision statement based on selected domains.
        
        Args:
            original_vision: The original vision statement to optimize
            domains: List of domain dictionaries with 'domain' and 'weight' keys
                    e.g., [{'domain': 'healthcare', 'weight': 70}, {'domain': 'retail', 'weight': 30}]
                    
        Returns:
            Dictionary containing:
                - optimized_vision: The improved vision statement
                - original_assessment: Quality assessment of original vision
                - optimized_assessment: Quality assessment of optimized vision
                - optimization_feedback: Details about what was improved
        """
        
        # Assess original vision quality
        primary_domain = domains[0]['domain'] if domains else 'general'
        original_assessment = self.vision_assessor.assess_vision(original_vision, primary_domain)
        
        self.logger.info(f"Original vision assessment: {original_assessment.rating} ({original_assessment.score}/100)")
        
        # Build context for optimization
        domain_context = self._build_domain_context(domains)
        
        # Create optimization prompt
        prompt_context = {
            'original_vision': original_vision,
            'domain_context': domain_context,
            'primary_domain': domains[0]['domain'] if domains else 'general',
            'domain_weights': json.dumps(domains),
            'original_score': original_assessment.score,
            'original_rating': original_assessment.rating,
            'strengths': ', '.join(original_assessment.strengths[:3]) if original_assessment.strengths else 'None identified',
            'weaknesses': ', '.join(original_assessment.weaknesses[:3]) if original_assessment.weaknesses else 'None identified',
            'missing_elements': ', '.join(original_assessment.missing_elements[:3]) if original_assessment.missing_elements else 'All elements present',
            'improvement_suggestions': '\n'.join(f"- {s}" for s in original_assessment.improvement_suggestions[:5])
        }
        
        user_input = f"""
OPTIMIZE THIS VISION STATEMENT

Original Vision (Score: {original_assessment.score}/100):
{original_vision}

Domain Focus:
{domain_context}

Quality Issues to Address:
{chr(10).join('- ' + w for w in original_assessment.weaknesses)}

Missing Elements:
{chr(10).join('- ' + m for m in original_assessment.missing_elements)}

REQUIREMENTS:
1. Maintain the core business concept and objectives
2. Integrate domain-specific terminology and requirements
3. Add missing elements identified above
4. Ensure 500+ words for comprehensive coverage
5. Structure with clear sections (Vision, Features, Value Proposition, etc.)
6. Include measurable objectives and success metrics
7. Provide technical implementation details
8. Target quality score of 85+ (EXCELLENT rating)

Generate an optimized vision that will enable high-quality epic generation.
"""
        
        try:
            # Generate optimized vision
            response = self.run(user_input, prompt_context)
            
            if not response:
                raise ValueError("Empty response from LLM")
            
            # Extract optimized vision from response
            optimized_vision = self._extract_vision_from_response(response)
            
            # Assess optimized vision quality
            optimized_assessment = self.vision_assessor.assess_vision(optimized_vision, primary_domain)
            
            self.logger.info(f"Optimized vision assessment: {optimized_assessment.rating} ({optimized_assessment.score}/100)")
            
            # Generate optimization feedback
            optimization_feedback = self._generate_optimization_feedback(
                original_assessment, optimized_assessment, domains
            )
            
            return {
                'optimized_vision': optimized_vision,
                'original_assessment': original_assessment,
                'optimized_assessment': optimized_assessment,
                'optimization_feedback': optimization_feedback,
                'success': optimized_assessment.score > original_assessment.score
            }
            
        except Exception as e:
            self.logger.error(f"Vision optimization failed: {e}")
            raise
    
    def _build_domain_context(self, domains: List[Dict[str, Any]]) -> str:
        """Build domain context string for the prompt."""
        if not domains:
            return "No specific domain focus"
        
        context_parts = []
        for i, domain_info in enumerate(domains):
            domain = domain_info['domain']
            weight = domain_info['weight']
            
            if i == 0:
                context_parts.append(f"Primary Domain: {domain} ({weight}% focus)")
            elif i == 1:
                context_parts.append(f"Secondary Domain: {domain} ({weight}% focus)")
            elif i == 2:
                context_parts.append(f"Tertiary Domain: {domain} ({weight}% focus)")
        
        return '\n'.join(context_parts)
    
    def _extract_vision_from_response(self, response: str) -> str:
        """Extract the optimized vision from the LLM response."""
        # Try to extract JSON first
        try:
            # Look for JSON structure
            json_match = re.search(r'\{.*"optimized_vision".*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if 'optimized_vision' in data:
                    return data['optimized_vision']
        except:
            pass
        
        # If no JSON, look for markdown sections
        # Try to find content after "Optimized Vision:" or similar headers
        patterns = [
            r'(?:Optimized Vision|OPTIMIZED VISION|Improved Vision|IMPROVED VISION):\s*\n(.*)',
            r'(?:##\s*Optimized Vision|##\s*OPTIMIZED VISION)\s*\n(.*)',
            r'(?:###\s*Vision Statement|###\s*VISION STATEMENT)\s*\n(.*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no specific pattern found, clean and return the whole response
        # Remove any instruction-like text
        cleaned = re.sub(r'^.*?(?:optimize|improve|enhance).*?vision.*?\n', '', response, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        # If cleaned version is too short, return the full response
        if len(cleaned) < 200:
            return response.strip()
        
        return cleaned
    
    def _generate_optimization_feedback(self, original: Any, optimized: Any, 
                                      domains: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate feedback about the optimization process."""
        feedback = {
            'score_improvement': optimized.score - original.score,
            'rating_change': f"{original.rating} → {optimized.rating}",
            'domains_applied': domains,
            'improvements_made': [],
            'remaining_issues': []
        }
        
        # Identify improvements made
        for weakness in original.weaknesses:
            if weakness not in optimized.weaknesses:
                feedback['improvements_made'].append(f"Resolved: {weakness}")
        
        for element in original.missing_elements:
            if element not in optimized.missing_elements:
                feedback['improvements_made'].append(f"Added: {element}")
        
        # Note remaining issues
        feedback['remaining_issues'] = optimized.weaknesses + optimized.missing_elements
        
        # Add new strengths
        new_strengths = [s for s in optimized.strengths if s not in original.strengths]
        if new_strengths:
            feedback['new_strengths'] = new_strengths
        
        return feedback