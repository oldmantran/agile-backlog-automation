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
            domains: List of domain dictionaries with 'domain' and 'priority' keys
                    e.g., [{'domain': 'healthcare', 'priority': 'primary'}, {'domain': 'retail', 'priority': 'secondary'}]
                    
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
        domain_strategy = self._build_domain_strategy(domains)
        domain_instructions = self._build_domain_instructions(domains)
        
        # Create optimization prompt
        prompt_context = {
            'original_vision': original_vision,
            'domain_strategy': domain_strategy,
            'domain_instructions': domain_instructions,
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

{prompt_context['domain_strategy']}

Quality Issues to Address:
{chr(10).join('- ' + w for w in original_assessment.weaknesses)}

Missing Elements:
{chr(10).join('- ' + m for m in original_assessment.missing_elements)}

REQUIREMENTS:
1. Maintain the core business concept and objectives
2. Follow the domain integration approach specified above
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
    
    def _build_domain_strategy(self, domains: List[Dict[str, Any]]) -> str:
        """Build a human-readable domain strategy description."""
        if not domains:
            return "General business application"
        
        if len(domains) == 1:
            return f"Focused entirely on {domains[0]['domain']} industry requirements and best practices"
        elif len(domains) == 2:
            return f"Primary focus on {domains[0]['domain']} with significant {domains[1]['domain']} integration"
        else:
            return f"Core {domains[0]['domain']} solution incorporating {domains[1]['domain']} requirements and {domains[2]['domain']} considerations"
    
    def _build_domain_instructions(self, domains: List[Dict[str, Any]]) -> str:
        """Build specific instructions for domain integration."""
        if not domains:
            return "Focus on general business best practices and universal software principles"
        
        instructions = []
        
        # Domain-specific patterns and vocabulary
        domain_patterns = {
            "healthcare": {
                "terms": ["HIPAA compliance", "patient outcomes", "clinical workflows", "EHR integration", "medical records"],
                "focus": "patient safety, regulatory compliance, and clinical efficiency"
            },
            "finance": {
                "terms": ["regulatory compliance", "audit trails", "transaction security", "risk management", "KYC/AML"],
                "focus": "security, compliance, and financial accuracy"
            },
            "retail": {
                "terms": ["inventory management", "customer experience", "omnichannel", "POS integration", "supply chain"],
                "focus": "customer satisfaction, inventory optimization, and sales growth"
            },
            "technology": {
                "terms": ["scalability", "API integration", "cloud architecture", "DevOps", "microservices"],
                "focus": "technical excellence, scalability, and maintainability"
            },
            "education": {
                "terms": ["learning outcomes", "student engagement", "curriculum management", "assessment tools", "LMS integration"],
                "focus": "educational effectiveness and student success"
            },
            "manufacturing": {
                "terms": ["production efficiency", "quality control", "supply chain", "IoT sensors", "predictive maintenance"],
                "focus": "operational efficiency and quality assurance"
            }
        }
        
        for i, domain_info in enumerate(domains):
            domain = domain_info['domain'].lower()
            priority = domain_info.get('priority', 'primary')
            
            if domain in domain_patterns:
                pattern = domain_patterns[domain]
                if priority == 'primary':
                    instructions.append(f"PRIMARY DOMAIN ({domain.upper()}):")
                    instructions.append(f"- Use extensive {domain} terminology: {', '.join(pattern['terms'])}")
                    instructions.append(f"- Focus heavily on {pattern['focus']}")
                    instructions.append(f"- Include {domain}-specific features and requirements throughout")
                    instructions.append(f"- Reference industry standards and best practices")
                elif priority == 'secondary':
                    instructions.append(f"SECONDARY DOMAIN ({domain.upper()}):")
                    instructions.append(f"- Integrate {domain} considerations where they naturally fit")
                    instructions.append(f"- Include key {domain} requirements: {', '.join(pattern['terms'][:3])}")
                    instructions.append(f"- Ensure compatibility with {domain} standards")
                else:  # tertiary
                    instructions.append(f"TERTIARY DOMAIN ({domain.upper()}):")
                    instructions.append(f"- Add {domain} aspects only where they provide clear value")
                    instructions.append(f"- Mention {', '.join(pattern['terms'][:2])} if relevant")
            else:
                # Generic domain handling
                if priority == 'primary':
                    instructions.append(f"PRIMARY DOMAIN ({domain.upper()}):")
                    instructions.append(f"- Make this the core focus of the vision")
                    instructions.append(f"- Use {domain}-specific terminology throughout")
                elif priority == 'secondary':
                    instructions.append(f"SECONDARY DOMAIN ({domain.upper()}):")
                    instructions.append(f"- Include significant {domain} integration points")
                else:
                    instructions.append(f"TERTIARY DOMAIN ({domain.upper()}):")
                    instructions.append(f"- Add minor {domain} considerations where appropriate")
            
            instructions.append("")  # Add spacing between domains
        
        # Add domain intersection guidance
        if len(domains) >= 2:
            instructions.append("DOMAIN INTERSECTIONS:")
            primary = domains[0]['domain'].lower()
            secondary = domains[1]['domain'].lower()
            
            # Known beneficial intersections
            intersections = {
                ("healthcare", "finance"): "Focus on medical billing, insurance claims processing, and healthcare payment systems",
                ("healthcare", "technology"): "Emphasize telemedicine, health informatics, and clinical decision support systems",
                ("finance", "technology"): "Highlight fintech innovations, digital banking, and automated trading systems",
                ("retail", "technology"): "Focus on e-commerce platforms, inventory automation, and customer analytics",
                ("education", "technology"): "Emphasize e-learning platforms, educational analytics, and virtual classrooms",
                ("manufacturing", "technology"): "Focus on Industry 4.0, IoT integration, and smart factory concepts"
            }
            
            key = tuple(sorted([primary, secondary]))
            if key in intersections:
                instructions.append(f"- {intersections[key]}")
        
        return "\n".join(instructions)