import json
import signal
import threading
from agents.base_agent import Agent
from config.config_loader import Config
from utils.content_enhancer import ContentEnhancer
from utils.epic_quality_assessor import EpicQualityAssessor

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise TimeoutError("Operation timed out")

class EpicStrategist(Agent):
    def __init__(self, config: Config):
        super().__init__("epic_strategist", config)
        self.content_enhancer = ContentEnhancer()
        self.quality_assessor = EpicQualityAssessor()
        self.max_quality_retries = 3  # Maximum attempts to achieve EXCELLENT rating

    def generate_epics(self, product_vision: str, context: dict = None, max_epics: int = None) -> list[dict]:
        """Generate epics from a product vision with contextual information."""
        
        # Apply max_epics constraint if specified (null = unlimited)
        epic_limit = max_epics if max_epics is not None else None  # None = unlimited
        
        # Build context for prompt template
        prompt_context = {
            'product_vision': product_vision,  # Include the actual product vision in the template
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',  # Will be determined by vision analysis
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'timeline': context.get('timeline', 'not specified') if context else 'not specified',
            'budget_constraints': context.get('budget_constraints', 'standard budget') if context else 'standard budget',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'max_epics': epic_limit if epic_limit else "unlimited"
        }
        
        print(f"DEBUG: Epic strategist product_vision: {product_vision[:200]}...")
        print(f"DEBUG: Epic strategist prompt_context: {prompt_context}")
        print(f"DEBUG: Epic strategist context from supervisor: {context}")
        print(f"DEBUG: Epic strategist max_epics: {epic_limit}")
        
        if epic_limit:
            user_input = f"Generate {epic_limit} epics based on the product vision provided in the context above."
        else:
            user_input = "Generate epics based on the product vision provided in the context above."

        
        # Debug: Check what the actual prompt looks like after template substitution
        try:
            actual_prompt = self.get_prompt(prompt_context)
            print(f"DEBUG: Successfully generated prompt for epic_strategist")
            print(f"DEBUG: User input: {user_input}")
        except Exception as e:
            print(f"DEBUG: Error getting prompt: {e}")
            print(f"DEBUG: prompt_context keys: {list(prompt_context.keys())}")
            print(f"DEBUG: max_epics value: {prompt_context.get('max_epics', 'NOT_FOUND')}")
            raise
        
        # Add timeout protection
        try:
            # Set a longer timeout for larger models (70B needs more time)
            timeout = 180 if self.model and "70b" in self.model.lower() else 60
            response = self._run_with_timeout(user_input, prompt_context, timeout=timeout)
        except TimeoutError as e:
            print("⚠️ Epic generation timed out")
            raise TimeoutError("Epic generation timed out") from e
        except Exception as e:
            print(f"❌ Epic generation failed: {e}")
            raise

        try:
            if not response:
                print("⚠️ Empty response from LLM")
                raise ValueError("Empty response from LLM")
            
            # Check for markdown code blocks
            # Extract JSON with improved parsing
            cleaned_response = self._extract_json_from_response(response)
            
            # Safety check for empty or invalid JSON
            if not cleaned_response or cleaned_response.strip() == "[]":
                print("⚠️ Empty or invalid JSON response")
                raise ValueError("Empty or invalid JSON response")
            
            try:
                epics = json.loads(cleaned_response)
            except (json.JSONDecodeError, TypeError) as e:
                print("⚠️ Failed to parse JSON response")
                raise ValueError(f"Failed to parse JSON response: {e}")
                
            if isinstance(epics, list):
                # Apply the epic limit constraint if specified
                if epic_limit:
                    limited_epics = epics[:epic_limit]
                    if len(epics) > epic_limit:
                        print(f"🔧 [EpicStrategist] Limited output from {len(epics)} to {len(limited_epics)} epics (configuration limit)")
                    
                    # Assess quality of limited epics
                    quality_approved_epics = self._assess_and_improve_quality(
                        limited_epics, product_vision, context
                    )
                    return quality_approved_epics
                else:
                    # Assess quality of all epics
                    quality_approved_epics = self._assess_and_improve_quality(
                        epics, product_vision, context
                    )
                    return quality_approved_epics
            else:
                print("⚠️ LLM response was not a list.")
                raise ValueError("LLM response was not a list")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON decode error: {e}")
    
    def _assess_and_improve_quality(self, epics: list, product_vision: str, context: dict) -> list:
        """Assess epic quality and retry generation if not EXCELLENT."""
        domain = context.get('domain', 'general') if context else 'general'
        approved_epics = []
        
        print(f"\n🔍 Starting quality assessment for {len(epics)} epics...")
        
        for i, epic in enumerate(epics):
            print(f"\n{'='*60}")
            print(f"ASSESSING EPIC {i+1}/{len(epics)}")
            print(f"{'='*60}")
            
            attempt = 1
            current_epic = epic
            
            while attempt <= self.max_quality_retries:
                # Assess current epic quality
                assessment = self.quality_assessor.assess_epic(current_epic, domain, product_vision)
                
                # Log assessment
                log_output = self.quality_assessor.format_assessment_log(current_epic, assessment, attempt)
                print(log_output)
                
                if assessment.rating == "EXCELLENT":
                    print(f"✅ Epic approved with EXCELLENT rating on attempt {attempt}")
                    approved_epics.append(current_epic)
                    break
                
                if attempt == self.max_quality_retries:
                    print(f"❌ Epic failed to reach EXCELLENT rating after {self.max_quality_retries} attempts")
                    print(f"   Final rating: {assessment.rating} ({assessment.score}/100)")
                    print("   Epic will be included but may need manual review")
                    approved_epics.append(current_epic)
                    break
                
                # Generate improvement prompt
                improvement_prompt = self._create_improvement_prompt(
                    current_epic, assessment, product_vision, context
                )
                
                print(f"🔄 Attempting to improve epic (attempt {attempt + 1}/{self.max_quality_retries})")
                
                try:
                    # Re-generate the epic with improvement guidance
                    improved_response = self._generate_improved_epic(improvement_prompt, context)
                    if improved_response:
                        current_epic = improved_response
                    else:
                        print("⚠️ Failed to generate improvement - using current version")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error during epic improvement: {e}")
                    break
                
                attempt += 1
        
        print(f"\n✅ Quality assessment complete: {len(approved_epics)} epics approved")
        return approved_epics
    
    def _create_improvement_prompt(self, epic: dict, assessment, product_vision: str, context: dict) -> str:
        """Create a prompt to improve the epic based on quality assessment."""
        title = epic.get('title', '')
        description = epic.get('description', '')
        
        improvement_text = f"""
EPIC IMPROVEMENT REQUEST

Current Epic:
Title: {title}
Description: {description}

Quality Issues Identified:
{chr(10).join('• ' + issue for issue in assessment.specific_issues)}

Improvement Suggestions:
{chr(10).join('• ' + suggestion for suggestion in assessment.improvement_suggestions)}

Product Vision Context:
{product_vision}

INSTRUCTIONS:
Rewrite this epic to address the quality issues above. Focus on:
1. Including domain-specific terminology from the product vision
2. Adding technical implementation clarity
3. Clarifying business value and user impact
4. Providing actionable details for feature decomposition
5. Maintaining strong alignment with the product vision

Return only a single improved epic in this JSON format:
{{
  "title": "Improved epic title (max 60 characters)",
  "description": "Detailed description that addresses all quality issues and provides clear context for feature decomposition.",
  "priority": "High|Medium|Low",
  "estimated_complexity": "XS|S|M|L|XL",
  "category": "core_platform|user_experience|data_management|integration|security|performance|administration"
}}
"""
        return improvement_text.strip()
    
    def _generate_improved_epic(self, improvement_prompt: str, context: dict) -> dict:
        """Generate an improved version of the epic."""
        try:
            # Build proper context for template (similar to generate_epics)
            prompt_context = {
                'product_vision': context.get('product_vision', '') if context else '',
                'domain': context.get('domain', 'dynamic') if context else 'dynamic',
                'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
                'target_users': context.get('target_users', 'end users') if context else 'end users',
                'timeline': context.get('timeline', 'not specified') if context else 'not specified',
                'budget_constraints': context.get('budget_constraints', 'standard budget') if context else 'standard budget',
                'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
                'max_epics': 1  # For improvement, we're generating just one epic
            }
            
            # Use the existing run method to generate improvement
            response = self.run(improvement_prompt, prompt_context)
            
            if not response:
                return None
            
            # Extract and parse JSON
            cleaned_response = self._extract_json_from_response(response)
            improved_epic = json.loads(cleaned_response)
            
            # Validate that we got a single epic object
            if isinstance(improved_epic, dict):
                return improved_epic
            elif isinstance(improved_epic, list) and len(improved_epic) > 0:
                return improved_epic[0]  # Take first epic if array returned
            else:
                return None
                
        except Exception as e:
            print(f"Error generating improved epic: {e}")
            return None

    def _run_with_timeout(self, user_input: str, prompt_context: dict, timeout: int = 60):
        """Run the agent with a timeout to prevent hanging."""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = self.run(user_input, prompt_context)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            print(f"⚠️ Epic generation timed out after {timeout} seconds")
            return None
        
        if exception[0]:
            raise exception[0]
        
        return result[0]

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON content from AI response with improved bracket counting and validation."""
        if not response:
            return "[]"
        
        import re
        
        # Look for JSON inside ```json blocks
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, response, re.IGNORECASE)
        
        if json_match:
            return json_match.group(1).strip()
        
        # Look for JSON inside ``` blocks (without language specifier)
        code_pattern = r'```\s*([\s\S]*?)\s*```'
        code_match = re.search(code_pattern, response)
        
        if code_match:
            content = code_match.group(1).strip()
            if content.startswith(('{', '[')):
                return content
        
        # Enhanced JSON extraction with proper bracket counting
        start_idx = response.find('[')
        if start_idx == -1:
            start_idx = response.find('{')
            if start_idx == -1:
                return "[]"
        
        # Count brackets/braces to find the complete JSON structure
        if response[start_idx] == '[':
            bracket_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            return response[start_idx:i+1]
        else:  # Starting with '{'
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return response[start_idx:i+1]
        
        return response[start_idx:].strip()