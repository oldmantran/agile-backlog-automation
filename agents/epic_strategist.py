import json
import signal
import threading
import time
from agents.base_agent import Agent
from config.config_loader import Config
from utils.content_enhancer import ContentEnhancer
from utils.epic_quality_assessor import EpicQualityAssessor
from utils.model_fallback_manager import ModelFallbackManager
from utils.safe_logger import get_safe_logger

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise TimeoutError("Operation timed out")

class EpicStrategist(Agent):
    def __init__(self, config: Config, user_id: str = None):
        super().__init__("epic_strategist", config, user_id)
        self.content_enhancer = ContentEnhancer()
        self.quality_assessor = EpicQualityAssessor()
        self.max_quality_retries = 3  # Maximum attempts to achieve GOOD or better rating
        self.model_fallback = ModelFallbackManager()
        self.logger = get_safe_logger(__name__)
        
        # Don't set a model attribute - let the unified LLM config system handle it
        # The fallback system will manage model switching during generation
        self.logger.info(f"[MODEL INIT] Epic strategist will use intelligent model fallback system")

    def generate_epics(self, product_vision: str, context: dict = None, max_epics: int = None) -> list[dict]:
        """Generate epics using current LLM configuration."""
        
        # Apply max_epics constraint if specified (null = unlimited)
        epic_limit = max_epics if max_epics is not None else None  # None = unlimited
        
        # Build context for prompt template
        prompt_context = {
            'product_vision': product_vision,
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'timeline': context.get('timeline', 'not specified') if context else 'not specified',
            'budget_constraints': context.get('budget_constraints', 'standard budget') if context else 'standard budget',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'max_epics': epic_limit if epic_limit else "unlimited"
        }
        
        self.logger.info(f"[EPIC GENERATION] Starting with product vision: {product_vision[:200]}...")
        self.logger.info(f"[EPIC GENERATION] Context: domain={context.get('domain', 'N/A')}, max_epics={epic_limit}")
        self.logger.info(f"[EPIC GENERATION] Using provider: {self.llm_provider}, model: {getattr(self, 'model', 'default')}")
        
        if epic_limit:
            user_input = f"Generate {epic_limit} epics based on the product vision provided in the context above."
        else:
            user_input = "Generate epics based on the product vision provided in the context above."

        # Check if we should use fallback system (Ollama only) or direct generation
        if self.llm_provider == "ollama":
            return self._generate_epics_with_ollama_fallback(user_input, product_vision, context, prompt_context, epic_limit)
        else:
            return self._generate_epics_with_current_provider(user_input, product_vision, context, prompt_context, epic_limit)
    
    def _generate_epics_with_current_provider(self, user_input: str, product_vision: str, context: dict, prompt_context: dict, epic_limit: int = None) -> list[dict]:
        """Generate epics using the current provider (OpenAI, etc.) without fallback."""
        self.logger.info(f"[DIRECT GENERATION] Using {self.llm_provider} provider without model fallback")
        
        start_time = time.time()
        approved_epics = []
        total_attempts = 0
        max_total_attempts = 10  # Prevent infinite loops
        max_duration = 600  # 10 minute timeout
        
        # Keep generating until we have enough quality epics or hit max attempts/timeout
        while (epic_limit is None or len(approved_epics) < epic_limit) and total_attempts < max_total_attempts:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_duration:
                self.logger.warning(f"[TIMEOUT] Epic generation exceeded {max_duration}s time limit")
                break
                
            total_attempts += 1
            
            try:
                # Calculate how many more epics we need
                needed = epic_limit - len(approved_epics) if epic_limit else 3
                
                # Generate batch of epics
                self.logger.info(f"[ATTEMPT {total_attempts}] Generating {needed} more epics...")
                epics = self._generate_epics_with_model(user_input, prompt_context, needed)
                
                # Assess quality - this will only return epics that meet quality threshold
                quality_epics = self._assess_and_improve_quality(epics, product_vision, context)
                
                # Add approved epics to our collection
                approved_epics.extend(quality_epics)
                
                self.logger.info(f"[BATCH RESULT] {len(quality_epics)}/{len(epics)} epics met quality threshold")
                
                # If we have enough, we're done
                if epic_limit and len(approved_epics) >= epic_limit:
                    approved_epics = approved_epics[:epic_limit]  # Trim to exact limit
                    break
                    
            except Exception as e:
                self.logger.error(f"[GENERATION ERROR] Attempt {total_attempts} failed: {e}")
                if total_attempts >= max_total_attempts:
                    raise
        
        # Check if we got ANY epics at all
        if len(approved_epics) == 0:
            domain = context.get('domain', 'unknown')
            from config.quality_config import MINIMUM_QUALITY_SCORE
            error_msg = (
                f"Failed to generate any epics meeting quality threshold of {MINIMUM_QUALITY_SCORE} "
                f"after {total_attempts} attempts over {time.time() - start_time:.1f}s. "
                f"This may indicate insufficient input quality or model limitations for the {domain} domain."
            )
            self.logger.error(f"[EPIC FAILURE] {error_msg}")
            raise ValueError(error_msg)
        
        duration = time.time() - start_time
        self.logger.info(f"[DIRECT SUCCESS] Generated {len(approved_epics)} quality epics in {duration:.1f}s after {total_attempts} attempts")
        return approved_epics
    
    def _generate_epics_with_ollama_fallback(self, user_input: str, product_vision: str, context: dict, prompt_context: dict, epic_limit: int = None) -> list[dict]:
        """Generate epics using Ollama with intelligent model fallback."""
        self.logger.info("[OLLAMA FALLBACK] Using intelligent model fallback system for Ollama")
        
        # Reset attempt history for new generation cycle
        self.model_fallback.reset_attempts()
        
        # Try models with intelligent fallback
        while True:
            model_config, attempt_number = self.model_fallback.get_next_model_for_epics()
            
            self.logger.info(f"[MODEL ATTEMPT] Using {model_config.display_name} (attempt {attempt_number})")
            
            # Temporarily switch to this model
            original_model = getattr(self, 'model', None)
            original_timeout = getattr(self, 'timeout_seconds', 300)
            
            try:
                # Update model configuration
                self.model = model_config.name
                self.timeout_seconds = model_config.timeout_seconds
                
                start_time = time.time()
                
                # Generate epics with current model
                epics = self._generate_epics_with_model(user_input, prompt_context, epic_limit)
                
                duration = time.time() - start_time
                
                # Add original inputs to context for replacement generation
                context_with_inputs = {
                    **context,
                    'original_user_input': user_input,
                    'original_prompt_context': prompt_context,
                    'epic_limit': epic_limit
                }
                
                # Assess quality using fallback-aware method
                quality_approved_epics = self._assess_and_improve_quality_with_fallback(
                    epics, product_vision, context_with_inputs, model_config, attempt_number, duration
                )
                
                return quality_approved_epics
                
            except Exception as e:
                duration = time.time() - start_time
                error_message = str(e)
                
                self.model_fallback.record_attempt(
                    model_name=model_config.name,
                    attempt_number=attempt_number,
                    success=False,
                    quality_score=0,
                    error_message=error_message,
                    duration_seconds=duration
                )
                
                self.logger.warning(f"[MODEL FAILURE] {model_config.display_name} failed: {error_message}")
                
                # Check if we should try another model
                if self.model_fallback.should_switch_models():
                    summary = self.model_fallback.get_attempt_summary()
                    if len(summary['models_tried']) >= len(self.model_fallback.epic_models):
                        # All models exhausted
                        self.logger.error("[EPIC GENERATION] All models exhausted, raising final error")
                        raise ValueError(f"Epic generation failed with all models. Final error: {error_message}")
                    else:
                        self.logger.info(f"[MODEL SWITCH] Switching to next model after {attempt_number} attempts")
                        continue
                else:
                    # Continue with same model for next attempt
                    continue
                    
            finally:
                # Restore original model configuration
                if original_model:
                    self.model = original_model
                if original_timeout:
                    self.timeout_seconds = original_timeout
                    
    def _generate_epics_with_model(self, user_input: str, prompt_context: dict, epic_limit: int = None) -> list:
        """Generate epics using the current model configuration."""
        
        # Debug: Check what the actual prompt looks like after template substitution
        try:
            actual_prompt = self.get_prompt(prompt_context)
            self.logger.info(f"[EPIC GEN] Successfully generated prompt for epic_strategist")
            self.logger.info(f"[EPIC GEN] User input: {user_input}")
        except Exception as e:
            self.logger.error(f"[EPIC GEN] Error getting prompt: {e}")
            raise
        
        # Add timeout protection
        try:
            # Use configured timeout from current model
            timeout = self.timeout_seconds if hasattr(self, 'timeout_seconds') and self.timeout_seconds else 600
            self.logger.info(f"[EPIC GEN] Calling LLM with timeout={timeout}s, model={self.model}")
            response = self._run_with_timeout(user_input, prompt_context, timeout=timeout)
        except TimeoutError as e:
            self.logger.warning(f"[EPIC GEN] Epic generation timed out after {timeout} seconds")
            raise TimeoutError(f"Epic generation timed out after {timeout} seconds") from e
        except Exception as e:
            self.logger.error(f"[EPIC GEN] Epic generation failed: {e}")
            raise

        try:
            if not response:
                self.logger.error(f"[EPIC GEN] Empty response from model {self.model}")
                raise ValueError("Empty response from LLM")
            
            # Extract JSON with improved parsing
            cleaned_response = self._extract_json_from_response(response)
            
            # Safety check for empty or invalid JSON
            if not cleaned_response or cleaned_response.strip() == "[]":
                raise ValueError("Empty or invalid JSON response")
            
            try:
                epics = json.loads(cleaned_response)
            except (json.JSONDecodeError, TypeError) as e:
                raise ValueError(f"Failed to parse JSON response: {e}")
                
            if not isinstance(epics, list):
                raise ValueError("LLM response was not a list")
            
            # Apply the epic limit constraint if specified
            if epic_limit and len(epics) > epic_limit:
                limited_epics = epics[:epic_limit]
                self.logger.info(f"[EPIC GEN] Limited output from {len(epics)} to {len(limited_epics)} epics")
                return limited_epics
            
            return epics
            
        except Exception as e:
            raise ValueError(f"Epic parsing error: {e}")
    
    def _assess_and_improve_quality_with_fallback(self, epics: list, product_vision: str, context: dict, 
                                                 model_config, attempt_number: int, duration: float) -> list:
        """Assess epic quality and handle model fallback based on results."""
        from utils.quality_metrics_tracker import quality_tracker
        
        domain = context.get('domain', 'general') if context else 'general'
        approved_epics = []
        best_quality_score = 0
        epic_limit = context.get('epic_limit', len(epics))  # Track requested number
        
        self.logger.info(f"[QUALITY CHECK] Starting quality assessment for {len(epics)} epics (target: {epic_limit})...")
        
        # Track failed epics that need replacement
        failed_epic_count = 0
        
        for i, epic in enumerate(epics):
            epic_title = epic.get('title', f'Epic {i+1}')
            tracking_context = {
                **context,
                'model_provider': self.llm_provider,
                'model_name': model_config.name,
                'template_name': 'epic_strategist'
            }
            
            metrics_id = quality_tracker.start_tracking(
                job_id=context.get('job_id', 'unknown'),
                agent_name='epic_strategist',
                work_item_type='Epic',
                work_item_title=epic_title,
                context=tracking_context
            )
            
            try:
                # Assess quality with improvement attempts
                for attempt in range(1, self.max_quality_retries + 1):
                    assessment = self.quality_assessor.assess_epic(epic, domain, product_vision)
                    
                    self.logger.info(f"[QUALITY] Epic '{epic_title}' attempt {attempt}: {assessment.rating} ({assessment.score}/100)")
                    
                    # Record attempt in quality tracker
                    quality_tracker.record_attempt(
                        metrics_id, attempt, assessment.rating, assessment.score,
                        assessment.strengths, assessment.weaknesses, assessment.improvement_suggestions
                    )
                    
                    # Track best score for fallback decision
                    best_quality_score = max(best_quality_score, assessment.score)
                    
                    # Log assessment details
                    log_output = self.quality_assessor.format_assessment_log(epic, assessment, attempt)
                    print(log_output)
                    
                    if assessment.rating in ["EXCELLENT", "GOOD"]:
                        quality_tracker.complete_tracking(
                            metrics_id, assessment.rating, assessment.score, attempt
                        )
                        approved_epics.append(epic)
                        self.logger.info(f"[QUALITY SUCCESS] Epic '{epic_title}' achieved {assessment.rating} rating")
                        break
                    
                    # Try to improve the epic if not excellent and we have attempts left
                    if attempt < self.max_quality_retries:
                        self.logger.info(f"[QUALITY RETRY] Attempting to improve epic (attempt {attempt + 1}/{self.max_quality_retries})")
                        try:
                            improved_epic = self._improve_epic_quality(epic, assessment, product_vision, domain)
                            if improved_epic:
                                epic = improved_epic
                        except Exception as improve_error:
                            self.logger.warning(f"[QUALITY RETRY] Epic improvement failed: {improve_error}")
                    else:
                        # Final attempt failed
                        quality_tracker.complete_tracking(
                            metrics_id, assessment.rating, assessment.score, None, 
                            failed=True, failure_reason=f"Failed to achieve GOOD or better rating after {self.max_quality_retries} attempts"
                        )
                        self.logger.warning(f"[QUALITY FAIL] Epic failed to reach GOOD or better rating after {self.max_quality_retries} attempts")
                        
                        # Record this attempt for fallback decision
                        self.model_fallback.record_attempt(
                            model_name=model_config.name,
                            attempt_number=attempt_number,
                            success=False,
                            quality_score=assessment.score,
                            error_message=f"Quality assessment failed: '{epic_title}' achieved {assessment.rating} ({assessment.score}/100) instead of GOOD+",
                            duration_seconds=duration
                        )
                        
                        # CHANGED: Skip failed epic and count for replacement generation
                        failed_epic_count += 1
                        self.logger.warning(f"[QUALITY SKIP] Skipping epic '{epic_title}' - failed to achieve GOOD+ rating ({assessment.rating} {assessment.score}/100)")
                        self.logger.info(f"[REPLACEMENT NEEDED] Will generate {failed_epic_count} replacement epic(s) to maintain target of {epic_limit}")
                        
            except Exception as e:
                quality_tracker.complete_tracking(
                    metrics_id, 'FAILED', 0, None, 
                    failed=True, failure_reason=str(e)
                )
                raise e
        
        # Generate replacement epics if we have failures and haven't reached target count
        if failed_epic_count > 0 and len(approved_epics) < epic_limit:
            replacements_needed = min(failed_epic_count, epic_limit - len(approved_epics))
            self.logger.info(f"[REPLACEMENT] Generating {replacements_needed} replacement epics to reach target of {epic_limit}")
            
            try:
                # Generate replacement epics using same context
                user_input = context.get('original_user_input', '')
                prompt_context = context.get('original_prompt_context', {})
                
                replacement_epics = self._generate_epics_with_model(user_input, prompt_context, replacements_needed)
                
                # Assess quality of replacement epics
                for i, replacement_epic in enumerate(replacement_epics):
                    epic_title = replacement_epic.get('title', f'Replacement Epic {i+1}')
                    
                    # Quick quality check (1 attempt only for replacements)
                    assessment = self.quality_assessor.assess_epic(replacement_epic, domain, product_vision)
                    
                    if assessment.rating in ["EXCELLENT", "GOOD"]:
                        approved_epics.append(replacement_epic)
                        self.logger.info(f"[REPLACEMENT SUCCESS] Added replacement epic '{epic_title}' with {assessment.rating} rating")
                        
                        # Stop when we reach target count
                        if len(approved_epics) >= epic_limit:
                            break
                    else:
                        self.logger.warning(f"[REPLACEMENT SKIP] Replacement epic '{epic_title}' also failed ({assessment.rating})")
                        
            except Exception as replacement_error:
                self.logger.warning(f"[REPLACEMENT FAILED] Could not generate replacement epics: {replacement_error}")
        
        # Check if we have any approved epics (EXCELLENT or GOOD rating)
        if approved_epics:
            self.model_fallback.record_attempt(
                model_name=model_config.name,
                attempt_number=attempt_number,
                success=True,
                quality_score=best_quality_score,
                duration_seconds=duration
            )
            
            self.logger.info(f"[EPIC SUCCESS] Generated {len(approved_epics)} GOOD+ rated epics with {model_config.display_name}")
            return approved_epics
        else:
            # Only fail if NO epics achieved GOOD+ rating
            raise ValueError(f"No epics achieved GOOD or better rating. This indicates either insufficient input quality or inadequate LLM training for the {domain} domain. Please review the product vision or consider using a more capable model.")

    def _assess_and_improve_quality(self, epics: list, product_vision: str, context: dict) -> list:
        """Assess epic quality and retry generation if not EXCELLENT."""
        from utils.quality_metrics_tracker import quality_tracker
        
        domain = context.get('domain', 'general') if context else 'general'
        approved_epics = []
        
        print(f"\n[SEARCH] Starting quality assessment for {len(epics)} epics...")
        
        for i, epic in enumerate(epics):
            print(f"\n{'='*60}")
            print(f"ASSESSING EPIC {i+1}/{len(epics)}")
            print(f"{'='*60}")
            
            # Start quality tracking
            epic_title = epic.get('title', f'Epic {i+1}')
            tracking_context = {
                **context,
                'model_provider': self.llm_provider,
                'model_name': getattr(self, 'model', 'unknown'),
                'template_name': 'epic_strategist'
            }
            metrics_id = quality_tracker.start_tracking(
                job_id=context.get('job_id', 'unknown'),
                agent_name='epic_strategist',
                work_item_type='Epic',
                work_item_title=epic_title,
                context=tracking_context
            )
            
            attempt = 1
            current_epic = epic
            
            while attempt <= self.max_quality_retries:
                # Assess current epic quality
                assessment = self.quality_assessor.assess_epic(current_epic, domain, product_vision)
                
                # Record attempt in quality tracker
                quality_tracker.record_attempt(
                    metrics_id, attempt, assessment.rating, assessment.score,
                    assessment.strengths, assessment.weaknesses, assessment.improvement_suggestions
                )
                
                # Log assessment
                log_output = self.quality_assessor.format_assessment_log(current_epic, assessment, attempt)
                print(log_output)
                
                # Use universal quality configuration
                from config.quality_config import get_acceptable_ratings, is_quality_acceptable
                acceptable_ratings = get_acceptable_ratings()
                
                # Check if quality score meets threshold
                if is_quality_acceptable(assessment.score):
                    print(f"[SUCCESS] Epic approved with {assessment.rating} rating ({assessment.score}/100) on attempt {attempt}")
                    # Complete tracking with success
                    quality_tracker.complete_tracking(
                        metrics_id, assessment.rating, assessment.score, attempt
                    )
                    approved_epics.append(current_epic)
                    break
                
                if attempt == self.max_quality_retries:
                    from config.quality_config import MINIMUM_QUALITY_SCORE
                    print(f"[ERROR] Epic failed to reach minimum quality score of {MINIMUM_QUALITY_SCORE} after {self.max_quality_retries} attempts")
                    print(f"   Final rating: {assessment.rating} ({assessment.score}/100)")
                    print("   DISCARDING - Work item does not meet quality threshold")
                    
                    # Complete tracking with failure
                    failure_reason = f"Failed to achieve minimum quality score of {MINIMUM_QUALITY_SCORE} after {self.max_quality_retries} attempts"
                    quality_tracker.complete_tracking(
                        metrics_id, assessment.rating, assessment.score, None, 
                        failed=True, failure_reason=failure_reason
                    )
                    
                    # Don't add this epic to approved list - it will be discarded
                    print(f"[INFO] Epic '{current_epic.get('title', 'Unknown')}' discarded due to low quality")
                
                # Generate improvement prompt
                improvement_prompt = self._create_improvement_prompt(
                    current_epic, assessment, product_vision, context
                )
                
                print(f"[RETRY] Attempting to improve epic (attempt {attempt + 1}/{self.max_quality_retries})")
                
                try:
                    # Re-generate the epic with improvement guidance
                    improved_response = self._generate_improved_epic(improvement_prompt, context)
                    if improved_response:
                        current_epic = improved_response
                    else:
                        print("[WARNING] Failed to generate improvement - using current version")
                        break
                        
                except Exception as e:
                    print(f"[WARNING] Error during epic improvement: {e}")
                    break
                
                attempt += 1
        
        print(f"\n[SUCCESS] Quality assessment complete: {len(approved_epics)} epics approved")
        
        # CRITICAL: If no epics reach required rating, stop the workflow
        if len(approved_epics) == 0:
            from config.quality_config import MINIMUM_QUALITY_SCORE
            domain = context.get('domain', 'unknown') if context else 'unknown'
            raise ValueError(
                f"WORKFLOW STOPPED: No epics achieved the minimum quality score of {MINIMUM_QUALITY_SCORE}. "
                f"This indicates either insufficient input quality or inadequate LLM training "
                f"for the {domain} domain. "
                f"Please review the product vision or consider using a more capable model."
            )
        
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
    
    def _improve_epic_quality(self, epic: dict, assessment, product_vision: str, domain: str) -> dict:
        """Improve epic quality based on assessment feedback."""
        try:
            # Create improvement prompt using existing method
            context = {'domain': domain, 'product_vision': product_vision}
            improvement_prompt = self._create_improvement_prompt(epic, assessment, product_vision, context)
            
            # Generate improved epic using existing method
            improved_epic = self._generate_improved_epic(improvement_prompt, context)
            
            return improved_epic
            
        except Exception as e:
            self.logger.warning(f"Failed to improve epic quality: {e}")
            return None
    
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

    def _run_with_timeout(self, user_input: str, prompt_context: dict, timeout: int = 600):
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
            print(f"[WARNING] Epic generation timed out after {timeout} seconds")
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