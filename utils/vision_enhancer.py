"""
Vision Statement Enhancer

This module uses AI to automatically enhance vision statements based on
quality assessment feedback.
"""

import json
from typing import Dict, Optional
from utils.safe_logger import get_safe_logger
from utils.vision_quality_assessor import VisionQualityAssessor, VisionAssessment


class VisionEnhancer:
    """Enhances vision statements using AI based on quality assessment feedback."""
    
    def __init__(self, llm_client=None):
        self.logger = get_safe_logger(__name__)
        self.vision_assessor = VisionQualityAssessor()
        self.llm_client = llm_client
        
    def enhance_vision(self, original_vision: str, assessment: VisionAssessment, 
                      domain: str = 'general', project_name: str = None) -> Dict[str, any]:
        """
        Enhance a vision statement based on quality assessment feedback.
        
        Args:
            original_vision: The original vision statement
            assessment: The quality assessment results
            domain: The project domain
            project_name: Optional project name for context
            
        Returns:
            Dict with enhanced_vision and enhancement_details
        """
        if not self.llm_client:
            return {
                "enhanced_vision": original_vision,
                "enhancement_applied": False,
                "reason": "No LLM client available for enhancement"
            }
        
        # Build enhancement prompt
        enhancement_prompt = self._build_enhancement_prompt(
            original_vision, assessment, domain, project_name
        )
        
        try:
            # Use LLM to enhance the vision
            enhanced_vision = self._call_llm_for_enhancement(enhancement_prompt)
            
            # Validate the enhanced vision
            new_assessment = self.vision_assessor.assess_vision(enhanced_vision, domain)
            
            return {
                "enhanced_vision": enhanced_vision,
                "enhancement_applied": True,
                "original_score": assessment.score,
                "enhanced_score": new_assessment.score,
                "score_improvement": new_assessment.score - assessment.score,
                "enhanced_rating": new_assessment.rating,
                "is_acceptable": new_assessment.is_acceptable,
                "changes_made": self._summarize_changes(original_vision, enhanced_vision),
                "new_assessment": new_assessment
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enhance vision: {e}")
            return {
                "enhanced_vision": original_vision,
                "enhancement_applied": False,
                "reason": f"Enhancement failed: {str(e)}"
            }
    
    def _build_enhancement_prompt(self, original_vision: str, assessment: VisionAssessment,
                                 domain: str, project_name: str) -> str:
        """Build the prompt for vision enhancement."""
        
        prompt = f"""You are an expert product manager helping to enhance a product vision statement.

ORIGINAL VISION:
{original_vision}

PROJECT CONTEXT:
- Project Name: {project_name or 'Not specified'}
- Domain: {domain}
- Current Score: {assessment.score}/100 (Minimum required: 75)
- Current Rating: {assessment.rating}

QUALITY ASSESSMENT RESULTS:

Strengths to preserve:
{chr(10).join('- ' + s for s in assessment.strengths) if assessment.strengths else 'None identified'}

Weaknesses to address:
{chr(10).join('- ' + w for w in assessment.weaknesses) if assessment.weaknesses else 'None identified'}

Missing elements to add:
{chr(10).join('- ' + m for m in assessment.missing_elements) if assessment.missing_elements else 'None'}

Specific improvements needed:
{chr(10).join(f'{i+1}. ' + s for i, s in enumerate(assessment.improvement_suggestions))}

INSTRUCTIONS:
1. Enhance the vision statement to address ALL weaknesses and missing elements
2. Preserve the original intent and key ideas
3. Add specific, measurable objectives where missing
4. Include technical implementation details if missing
5. Ensure the vision is comprehensive (300-500 words minimum)
6. Use clear sections with headers (Vision, Core Offering, Key Features, etc.)
7. Include {domain}-specific terminology and use cases
8. Make it actionable and detailed enough for epic generation

Return ONLY the enhanced vision statement text, properly formatted with markdown headers.
Do not include any commentary or explanation - just the enhanced vision.
"""
        return prompt
    
    def _call_llm_for_enhancement(self, prompt: str) -> str:
        """Call the LLM to enhance the vision."""
        # This would integrate with the unified LLM config
        # For now, returning a placeholder
        raise NotImplementedError("LLM integration needs to be implemented")
    
    def _summarize_changes(self, original: str, enhanced: str) -> list:
        """Summarize the key changes made to the vision."""
        changes = []
        
        # Check length improvement
        original_words = len(original.split())
        enhanced_words = len(enhanced.split())
        if enhanced_words > original_words * 1.5:
            changes.append(f"Expanded content from {original_words} to {enhanced_words} words")
        
        # Check for structure improvements
        if '##' in enhanced and '##' not in original:
            changes.append("Added structured sections with headers")
        
        # Check for metrics
        import re
        if re.search(r'\d+%|\d+ (days|months|years)', enhanced) and not re.search(r'\d+%|\d+ (days|months|years)', original):
            changes.append("Added measurable objectives and metrics")
        
        # Check for technical details
        tech_keywords = ['api', 'database', 'architecture', 'integration', 'cloud', 'security']
        original_lower = original.lower()
        enhanced_lower = enhanced.lower()
        tech_added = any(kw in enhanced_lower and kw not in original_lower for kw in tech_keywords)
        if tech_added:
            changes.append("Added technical implementation details")
        
        return changes


class InteractiveVisionEnhancer:
    """Provides interactive vision enhancement with user feedback loop."""
    
    def __init__(self, vision_enhancer: VisionEnhancer):
        self.vision_enhancer = vision_enhancer
        self.logger = get_safe_logger(__name__)
        
    def enhance_with_feedback(self, original_vision: str, domain: str,
                            project_name: str = None, max_iterations: int = 3) -> Dict[str, any]:
        """
        Enhance vision with iterative improvements until it meets quality standards.
        
        Args:
            original_vision: The original vision statement
            domain: The project domain
            project_name: Optional project name
            max_iterations: Maximum enhancement iterations
            
        Returns:
            Dict with final enhanced vision and iteration history
        """
        current_vision = original_vision
        iteration_history = []
        
        for iteration in range(max_iterations):
            # Assess current vision
            assessment = self.vision_enhancer.vision_assessor.assess_vision(
                current_vision, domain
            )
            
            # Record iteration
            iteration_data = {
                "iteration": iteration + 1,
                "score": assessment.score,
                "rating": assessment.rating,
                "is_acceptable": assessment.is_acceptable
            }
            
            # Check if acceptable
            if assessment.is_acceptable:
                iteration_data["result"] = "Accepted"
                iteration_history.append(iteration_data)
                break
            
            # Try to enhance
            enhancement_result = self.vision_enhancer.enhance_vision(
                current_vision, assessment, domain, project_name
            )
            
            if enhancement_result["enhancement_applied"]:
                current_vision = enhancement_result["enhanced_vision"]
                iteration_data["enhanced_score"] = enhancement_result["enhanced_score"]
                iteration_data["improvement"] = enhancement_result["score_improvement"]
                iteration_data["changes"] = enhancement_result["changes_made"]
                iteration_data["result"] = "Enhanced"
            else:
                iteration_data["result"] = "Enhancement failed"
                iteration_data["reason"] = enhancement_result.get("reason")
                break
                
            iteration_history.append(iteration_data)
        
        # Final assessment
        final_assessment = self.vision_enhancer.vision_assessor.assess_vision(
            current_vision, domain
        )
        
        return {
            "original_vision": original_vision,
            "final_vision": current_vision,
            "iterations": len(iteration_history),
            "iteration_history": iteration_history,
            "final_score": final_assessment.score,
            "final_rating": final_assessment.rating,
            "is_acceptable": final_assessment.is_acceptable,
            "total_improvement": final_assessment.score - iteration_history[0]["score"],
            "final_assessment": final_assessment
        }