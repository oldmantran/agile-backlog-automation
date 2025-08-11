import json
import re
import threading
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator
from utils.feature_quality_assessor_v2 import FeatureQualityAssessor

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

class FeatureDecomposerAgent(Agent):
    """
    Agent responsible for decomposing epics into features.
    Focuses on business value, strategic planning, and high-level feature definition.
    """
    
    def __init__(self, config: Config, user_id: str = None):
        super().__init__("feature_decomposer_agent", config, user_id)
        # Initialize quality validator with current configuration
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)
        self.feature_quality_assessor = FeatureQualityAssessor()
        self.max_quality_retries = 3  # Maximum attempts to achieve GOOD or better rating

    def decompose_epic(self, epic: dict, context: dict = None, max_features: int = None) -> list[dict]:
        """Break down an epic into detailed features with business value and strategic considerations."""
        
        # Apply max_features constraint if specified (null = unlimited)
        feature_limit = max_features if max_features is not None else None  # None = unlimited
        
        # Extract product vision for context cascading
        product_vision = context.get('product_vision', '') if context else ''
        
        # Build context for prompt template - CASCADE FULL CONTEXT
        prompt_context = {
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'integrations': context.get('integrations', 'standard APIs') if context else 'standard APIs',
            'product_vision': product_vision,  # CASCADE PRODUCT VISION
            'max_features': feature_limit if feature_limit else "unlimited"
        }
        
        user_input = f"""
Epic: {epic.get('title', 'Unknown Epic')}
Description: {epic.get('description', 'No description provided')}
Priority: {epic.get('priority', 'Medium')}
Business Value: {epic.get('business_value', 'Not specified')}
Success Criteria: {epic.get('success_criteria', [])}
Dependencies: {epic.get('dependencies', [])}

{f'IMPORTANT: Generate a maximum of {feature_limit} features only.' if feature_limit else ''}
"""
        
        # Remove redundant print - supervisor already logs this
        # print(f"🏗️ [FeatureDecomposerAgent] Decomposing epic: {epic.get('title', 'Unknown')}")
        
        # Smart model selection with fallback strategy
        models_to_try = []
        
        # Use configured model with appropriate timeout (extended for quality)
        if self.model and ("70b" in self.model.lower()):
            # 70B model needs longer timeout
            models_to_try = [(self.model, 600)]
        elif self.model and ("34b" in self.model.lower()):
            # 34B model with extended timeout for quality
            models_to_try = [(self.model, 600)]
        else:
            # 8B, 14B or other models with extended timeout for quality
            models_to_try = [(self.model, 600)]
        
        # Try each model until one succeeds
        for model_name, timeout in models_to_try:
            try:
                print(f"Trying {model_name} with {timeout}s timeout...")
                
                # Temporarily switch to this model
                original_model = self.model
                self.model = model_name
                
                # Update Ollama provider if needed
                if hasattr(self, 'ollama_provider') and self.llm_provider == "ollama":
                    try:
                        from utils.ollama_client import create_ollama_provider
                        self.ollama_provider = create_ollama_provider(preset='balanced')
                    except Exception as e:
                        print(f"Failed to switch to {model_name}: {e}")
                        continue
                
                response = self._run_with_timeout(user_input, prompt_context, timeout=timeout)
                
                # Restore original model
                self.model = original_model
                
                print(f"Successfully generated features using {model_name}")
                break
                
            except TimeoutError:
                print(f"{model_name} timed out after {timeout}s, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
            except Exception as e:
                print(f"{model_name} failed: {e}, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
        else:
            # All models failed
            print("All models failed for feature generation")
            return []

        try:
            # Handle empty response
            if not response or not response.strip():
                print("Empty response from LLM")
                return self._extract_features_from_any_format("", epic, feature_limit)
            
            # Check for markdown code blocks
            # Extract JSON with improved parsing
            cleaned_response = self._extract_json_from_response(response)
            
            # Safety check for empty or invalid JSON
            if not cleaned_response or cleaned_response.strip() == "[]":
                print("Empty or invalid JSON response")
                return self._extract_features_from_any_format(response, epic, feature_limit)
            
            try:
                features = json.loads(cleaned_response)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Raw response length: {len(response)} chars")
                print(f"Cleaned response length: {len(cleaned_response)} chars")
                print(f"Raw response preview (first 500 chars): {response[:500]}")
                print(f"Cleaned response preview (first 500 chars): {cleaned_response[:500]}")
                print(f"Cleaned response ending (last 100 chars): ...{cleaned_response[-100:]}")
                return self._extract_features_from_any_format(response, epic, feature_limit)
            if isinstance(features, list) and len(features) > 0:
                # Apply the feature limit constraint if specified
                if feature_limit:
                    limited_features = features[:feature_limit]
                    if len(features) > feature_limit:
                        print(f"[FeatureDecomposerAgent] Limited output from {len(features)} to {len(limited_features)} features (configuration limit)")
                    
                    # Assess quality of limited features with full context
                    quality_approved_features = self._assess_and_improve_feature_quality(
                        limited_features, epic, context, product_vision
                    )
                    return quality_approved_features
                else:
                    # Assess quality of all features with full context
                    quality_approved_features = self._assess_and_improve_feature_quality(
                        features, epic, context, product_vision
                    )
                    return quality_approved_features
            else:
                print("LLM response was not a valid list")
                return self._extract_features_from_any_format(response, epic, feature_limit)
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Raw response: {response}")
            return self._extract_features_from_any_format(response, epic, feature_limit)

    def _extract_features_from_any_format(self, response: str, epic: dict, max_features: int = None) -> list[dict]:
        """Extract features from LLM response in any format using intelligent parsing."""
        if not response or not response.strip():
            print("Empty response received")
            return []
        
        # Try to extract features from text format
        extracted_features = self._extract_features_from_text(response, epic)
        
        # Apply limit if specified
        if max_features and len(extracted_features) > max_features:
            extracted_features = extracted_features[:max_features]
            print(f"Limited features to {max_features}")
        
        if extracted_features:
            print(f"Successfully extracted {len(extracted_features)} features from response")
            return self._validate_and_enhance_features(extracted_features)
        else:
            print("Failed to extract any features from response")
            return []

    def _extract_features_from_text(self, text: str, epic: dict) -> list[dict]:
        """Extract features from unstructured text using pattern matching."""
        if not text or not text.strip():
            print("Empty text provided for feature extraction")
            return []
        
        print("Attempting to extract features from non-JSON LLM response")
        extracted_features = []
        
        # Try to find feature-like content in the response
        import re
        
        # Pattern 1: Look for numbered lists that might be features
        # Example: "1. User Authentication System"
        numbered_pattern = r'^\s*(\d+)\.?\s*(.+)$'
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            match = re.match(numbered_pattern, line)
            if match and len(match.group(2)) > 10:  # Reasonable length for a feature title
                feature_text = match.group(2).strip()
                
                # Skip if it looks like JSON or code
                if feature_text.startswith(('{', '[', '"')) or 'json' in feature_text.lower():
                    continue
                
                # Create a basic feature structure
                feature = {
                    'title': feature_text,
                    'description': f"Feature extracted from LLM response: {feature_text}",
                    'priority': 'Medium',
                    'estimated_story_points': 8,
                    'dependencies': [],
                    'ui_ux_requirements': ["Responsive design", "Accessibility compliance"],
                    'technical_considerations': ["Performance optimization", "Scalability"],
                    'business_value': f"Delivers value through {feature_text.lower()}",
                    'edge_cases': ["Error handling scenarios", "Edge case validation"]
                }
                extracted_features.append(feature)
        
        # Pattern 2: Look for bullet points
        # Example: "• Feature Management Dashboard"
        if not extracted_features:
            bullet_pattern = r'^\s*[•*-]\s*(.+)$'
            for line in lines:
                line = line.strip()
                match = re.match(bullet_pattern, line)
                if match and len(match.group(1)) > 10:
                    feature_text = match.group(1).strip()
                    
                    # Skip if it looks like JSON or code
                    if feature_text.startswith(('{', '[', '"')) or 'json' in feature_text.lower():
                        continue
                    
                    feature = {
                        'title': feature_text,
                        'description': f"Feature extracted from LLM response: {feature_text}",
                        'priority': 'Medium',
                        'estimated_story_points': 8,
                        'dependencies': [],
                        'ui_ux_requirements': ["Responsive design", "Accessibility compliance"],
                        'technical_considerations': ["Performance optimization", "Scalability"],
                        'business_value': f"Delivers value through {feature_text.lower()}",
                        'edge_cases': ["Error handling scenarios", "Edge case validation"]
                    }
                    extracted_features.append(feature)
        
        if extracted_features:
            print(f"Extracted {len(extracted_features)} features from text response")
        else:
            print("No feature-like content found in LLM response")
        
        return extracted_features

    def _validate_and_enhance_features(self, features: list) -> list[dict]:
        """Validate and enhance features to meet quality standards."""
        enhanced_features = []
        
        for feature in features:
            enhanced_feature = self._enhance_single_feature(feature)
            enhanced_features.append(enhanced_feature)
        
        return enhanced_features

    def _enhance_single_feature(self, feature: dict) -> dict:
        """Enhance a single feature to meet quality standards."""
        enhanced_feature = feature.copy()
        
        # Validate and fix title
        title = feature.get('title', '')
        
        # Ensure title is a string
        if isinstance(title, dict):
            title = str(title)
        elif not isinstance(title, str):
            title = str(title)
            
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "Feature")
        if not title_valid:
            # Only show critical title issues
            if not title or len(title.strip()) < 5:
                print(f"Critical feature title issue: {', '.join(title_issues)}")
            if not title:
                enhanced_feature['title'] = f"Feature: {feature.get('description', 'Undefined')[:50]}..."
        
        # Validate and fix description
        description = feature.get('description', '')
        if not description or len(description.strip()) < 20:
            # Only show critical description issues
            if not description or len(description.strip()) < 10:
                print(f"Critical feature description issue: description too short")
            enhanced_feature['description'] = f"Feature providing: {title}. " + (description or "Details to be defined during user story creation.")
        
        # Ensure required fields exist
        if not enhanced_feature.get('priority'):
            enhanced_feature['priority'] = 'Medium'
        
        if not enhanced_feature.get('estimated_story_points'):
            enhanced_feature['estimated_story_points'] = 8
        
        if not enhanced_feature.get('dependencies'):
            enhanced_feature['dependencies'] = []
        
        if not enhanced_feature.get('ui_ux_requirements'):
            enhanced_feature['ui_ux_requirements'] = ["Responsive design", "Accessibility compliance"]
        
        if not enhanced_feature.get('technical_considerations'):
            enhanced_feature['technical_considerations'] = ["Performance optimization", "Scalability"]
        
        if not enhanced_feature.get('business_value'):
            enhanced_feature['business_value'] = f"Delivers value through {title.lower()}"
        
        if not enhanced_feature.get('edge_cases'):
            enhanced_feature['edge_cases'] = ["Error handling scenarios", "Edge case validation"]
        
        # Add quality metadata
        enhanced_feature['definition_of_ready'] = [
            'Business value clearly defined',
            'Dependencies identified and resolved',
            'UI/UX requirements specified',
            'Technical considerations documented',
            'Ready for user story decomposition'
        ]
        
        return enhanced_feature

    def run_with_template(self, user_input: str, context: dict, template_name: str = None) -> str:
        """Run with a specific prompt template (fallback to default if template doesn't exist)."""
        # Use the template name if provided, otherwise use the agent name
        template_to_use = template_name or "feature_decomposer_agent"
        
        try:
            # Try to use the specific template
            prompt = self.project_context.generate_prompt(template_to_use, context) if hasattr(self, 'project_context') else self.get_prompt(context)
            # Use the proper method based on provider
            if self.llm_provider == "ollama":
                # Use the Ollama provider for local inference
                return self.ollama_provider.generate_response(
                    system_prompt=prompt,
                    user_input=user_input,
                    temperature=0.7,
                    max_tokens=8000
                )
            else:
                # Use direct API call for cloud providers
                url = self.api_url
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_input}
                    ]
                }
                
                import requests
                # Use extended timeout for quality (all models)
                timeout = 600  # 10 minutes for all models
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"Template {template_to_use} failed: {e}")
            print("Falling back to default prompt...")
            # Use timeout protection for fallback call
            try:
                timeout = 600  # 10 minutes for all models
                return self._run_with_timeout(user_input, context, timeout=timeout)
            except TimeoutError:
                print("Fallback generation timed out")
                return ""
            except Exception as fallback_e:
                print(f"Fallback generation failed: {fallback_e}")
                return ""

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON content from AI response with improved parsing."""
        if not response:
            return "[]"
        
        import re
        import json
        
        # Method 1: Try to parse the entire response as JSON first
        try:
            json.loads(response.strip())
            return response.strip()
        except (json.JSONDecodeError, TypeError):
            # Try cleaning common JSON issues and parsing again
            cleaned = self._clean_json_syntax(response.strip())
            try:
                json.loads(cleaned)
                print(f"🧹 Fixed JSON syntax issues, returning cleaned version")
                return cleaned
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Method 2: Look for JSON inside ```json blocks
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, response, re.IGNORECASE)
        
        if json_match:
            content = json_match.group(1).strip()
            try:
                json.loads(content)
                return content
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Method 3: Look for JSON inside ``` blocks (without language specifier)
        code_pattern = r'```\s*([\s\S]*?)\s*```'
        code_match = re.search(code_pattern, response)
        
        if code_match:
            content = code_match.group(1).strip()
            if content.startswith(('{', '[')):
                try:
                    json.loads(content)
                    return content
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Method 4: Find the largest valid JSON structure using regex
        # Look for array patterns first (most common for features)
        array_patterns = [
            r'\[[\s\S]*\]',  # Match from first [ to last ]
        ]
        
        for pattern in array_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            print(f"🔍 Regex found {len(matches)} potential JSON arrays")
            for i, match in enumerate(matches):
                print(f"🔍 Array {i+1}: {len(match)} chars, starts with: {match[:100]}...")
                try:
                    json.loads(match)
                    print(f"🎯 Found valid JSON array: {len(match)} characters")
                    return match
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"❌ Array {i+1} failed JSON validation: {e}")
                    # Try cleaning the JSON and parsing again
                    cleaned_match = self._clean_json_syntax(match)
                    try:
                        json.loads(cleaned_match)
                        print(f"🧹 Fixed JSON syntax in array {i+1}, returning cleaned version")
                        return cleaned_match
                    except (json.JSONDecodeError, TypeError):
                        print(f"❌ Array {i+1} still invalid after cleaning")
                        continue
        
        # Method 5: Try to find object patterns
        object_patterns = [
            r'\{[\s\S]*\}',  # Match from first { to last }
        ]
        
        for pattern in object_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    print(f"🎯 Found valid JSON object: {len(match)} characters")
                    return match
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Method 6: Last resort - try to extract JSON by finding balanced brackets
        print("🔍 Using fallback bracket matching...")
        return self._extract_json_with_balanced_brackets(response)

    def _clean_json_syntax(self, json_str: str) -> str:
        """Clean common JSON syntax issues that LLMs often produce."""
        if not json_str:
            return json_str
        
        import re
        
        # Fix trailing commas before closing brackets/braces
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix missing commas between objects in arrays (less common but possible)
        json_str = re.sub(r'}(\s*){', r'},\1{', json_str)
        
        # Fix missing quotes around property names (though templates should prevent this)
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')
        
        # Remove comments (JSON doesn't support comments but LLMs sometimes add them)
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        return json_str

    def _extract_json_with_balanced_brackets(self, response: str) -> str:
        """Extract JSON using balanced bracket counting as last resort."""
        import json
        
        # Find the start of JSON
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
                            candidate = response[start_idx:i+1]
                            try:
                                json.loads(candidate)
                                return candidate
                            except (json.JSONDecodeError, TypeError):
                                continue
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
                            candidate = response[start_idx:i+1]
                            try:
                                json.loads(candidate)
                                return candidate
                            except (json.JSONDecodeError, TypeError):
                                continue
        
        # If nothing worked, return the remainder and hope for the best
        return response[start_idx:].strip()

    def _run_with_timeout(self, user_input: str, context: dict, timeout: int = 600):
        """Run the agent with a timeout to prevent hanging."""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = self.run(user_input, context)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            print(f"⚠️ Feature generation timed out after {timeout} seconds")
            return None
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def _assess_and_improve_feature_quality(self, features: list, epic: dict, context: dict, product_vision: str) -> list:
        """Assess feature quality and retry generation if not GOOD or better."""
        import time
        start_time = time.time()
        max_duration = 480  # 8 minutes max for quality assessment
        
        domain = context.get('domain', 'general') if context else 'general'
        approved_features = []
        feature_limit = len(features)  # Track original target count
        failed_feature_count = 0  # Track failed features for replacement
        
        print(f"\nStarting feature quality assessment for {len(features)} features (target: {feature_limit})...")
        print(f"Epic Context: {epic.get('title', 'Unknown Epic')}")
        print(f"Domain: {domain}")
        
        for i, feature in enumerate(features):
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > max_duration:
                print(f"\n[TIMEOUT] Feature quality assessment exceeded {max_duration}s time limit")
                break
                
            print(f"\n{'='*60}")
            print(f"ASSESSING FEATURE {i+1}/{len(features)}")
            print(f"{'='*60}")
            
            attempt = 1
            current_feature = feature
            
            while attempt <= self.max_quality_retries:
                # Assess current feature quality
                assessment = self.feature_quality_assessor.assess_feature(
                    current_feature, epic, domain, product_vision
                )
                
                # Log assessment
                log_output = self.feature_quality_assessor.format_assessment_log(
                    current_feature, assessment, attempt
                )
                print(log_output)
                
                if assessment.rating in ["EXCELLENT", "GOOD"]:
                    print(f"+ Feature approved with {assessment.rating} rating on attempt {attempt}")
                    approved_features.append(current_feature)
                    break
                
                if attempt == self.max_quality_retries:
                    failed_feature_count += 1
                    feature_title = feature.get('title', f'Feature {i+1}')
                    print(f"- Feature failed to reach GOOD or better rating after {self.max_quality_retries} attempts")
                    print(f"   Final rating: {assessment.rating} ({assessment.score}/100)")
                    print("   Feature REJECTED - GOOD or better rating required")
                    print(f"[REPLACEMENT NEEDED] Will generate {failed_feature_count} replacement feature(s) to maintain target of {feature_limit}")
                    # Do NOT add to approved_features - only GOOD+ features allowed
                    break
                
                # Generate improvement prompt
                improvement_prompt = self._create_feature_improvement_prompt(
                    current_feature, assessment, epic, product_vision, context
                )
                
                print(f"Attempting to improve feature (attempt {attempt + 1}/{self.max_quality_retries})")
                
                try:
                    # Re-generate the feature with improvement guidance
                    improved_response = self._generate_improved_feature(improvement_prompt, context)
                    if improved_response:
                        current_feature = improved_response
                    else:
                        print("Failed to generate improvement - using current version")
                        break
                        
                except Exception as e:
                    print(f"Error during feature improvement: {e}")
                    break
                
                attempt += 1
        
        # Generate replacement features if we have failures and haven't reached target count
        if failed_feature_count > 0 and len(approved_features) < feature_limit:
            replacements_needed = min(failed_feature_count, feature_limit - len(approved_features))
            print(f"\n[REPLACEMENT] Generating {replacements_needed} replacement features to reach target of {feature_limit}")
            
            try:
                # Build user input for replacement generation
                user_input = f"""
Epic: {epic.get('title', 'Unknown Epic')}
Description: {epic.get('description', 'No description provided')}
Priority: {epic.get('priority', 'Medium')}
Business Value: {epic.get('business_value', 'Not specified')}
Strategic Objectives: {epic.get('strategic_objectives', 'Not specified')}
Success Metrics: {epic.get('success_metrics', 'Not specified')}
Dependencies: {epic.get('dependencies', [])}
"""
                
                # Build context similar to main decomposition
                prompt_context = {
                    'domain': context.get('domain', 'dynamic') if context else 'dynamic',
                    'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
                    'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
                    'target_users': context.get('target_users', 'end users') if context else 'end users',
                    'platform': context.get('platform', 'web application') if context else 'web application',
                    'integrations': context.get('integrations', 'standard APIs') if context else 'standard APIs',
                    'product_vision': context.get('product_vision', '') if context else '',
                    'max_features': replacements_needed
                }
                
                # Generate replacement features
                replacement_response = self.run_with_template(user_input, prompt_context, "feature_decomposer_agent")
                
                if replacement_response:
                    # Parse replacement features
                    from utils.json_extractor import JSONExtractor
                    cleaned_response = JSONExtractor.extract_json_from_response(replacement_response)
                    replacement_features = json.loads(cleaned_response) if cleaned_response else []
                    
                    # Quick quality check for replacements (1 attempt only)
                    for i, replacement_feature in enumerate(replacement_features):
                        feature_title = replacement_feature.get('title', f'Replacement Feature {i+1}')
                        
                        assessment = self.feature_quality_assessor.assess_feature(
                            replacement_feature, epic, domain, product_vision
                        )
                        
                        if assessment.rating in ["EXCELLENT", "GOOD"]:
                            approved_features.append(replacement_feature)
                            print(f"[REPLACEMENT SUCCESS] Added replacement feature '{feature_title}' with {assessment.rating} rating")
                            
                            # Stop when we reach target count
                            if len(approved_features) >= feature_limit:
                                break
                        else:
                            print(f"[REPLACEMENT SKIP] Replacement feature '{feature_title}' also failed ({assessment.rating})")
                            
            except Exception as replacement_error:
                print(f"[REPLACEMENT FAILED] Could not generate replacement features: {replacement_error}")
        
        print(f"\n+ Feature quality assessment complete: {len(approved_features)} features approved")
        return approved_features
    
    def _create_feature_improvement_prompt(self, feature: dict, assessment, epic: dict, product_vision: str, context: dict) -> str:
        """Create a prompt to improve the feature based on quality assessment."""
        title = feature.get('title', '')
        description = feature.get('description', '')
        epic_title = epic.get('title', '')
        epic_description = epic.get('description', '')
        
        improvement_text = f"""FEATURE IMPROVEMENT REQUEST

Current Feature:
Title: {title}
Description: {description}

Parent Epic Context:
Title: {epic_title}
Description: {epic_description}

Product Vision Context:
{product_vision}

Quality Issues Identified:
{chr(10).join('• ' + issue for issue in assessment.specific_issues)}

Improvement Suggestions:
{chr(10).join('• ' + suggestion for suggestion in assessment.improvement_suggestions)}

INSTRUCTIONS:
Rewrite this feature to address the quality issues above. Focus on:
1. Strong alignment with the parent epic "{epic_title}"
2. Including domain-specific terminology from the product vision
3. Adding technical implementation details (APIs, interfaces, databases)
4. Clarifying user interactions and interface components
5. Providing sufficient detail for user story decomposition
6. Maintaining strong connection to the product vision goals

Return only a single improved feature in this JSON format:
{{
  "title": "Improved feature title that aligns with epic and vision",
  "description": "Detailed description that addresses all quality issues, includes technical implementation guidance, specifies user interactions, and provides clear context for user story decomposition.",
  "priority": "High|Medium|Low",
  "estimated_complexity": "XS|S|M|L|XL",
  "category": "core_functionality|user_interface|data_management|integration|security|performance",
  "business_value": "Clear statement of business value and user benefits",
  "acceptance_criteria": ["Specific", "measurable", "acceptance criteria"]
}}"""
        return improvement_text.strip()
    
    def _generate_improved_feature(self, improvement_prompt: str, context: dict) -> dict:
        """Generate an improved version of the feature."""
        try:
            # Use the existing run method to generate improvement
            response = self.run(improvement_prompt, context or {})
            
            if not response:
                return None
            
            # Extract and parse JSON
            cleaned_response = self._extract_json_from_response(response)
            improved_feature = json.loads(cleaned_response)
            
            # Validate that we got a single feature object
            if isinstance(improved_feature, dict):
                return improved_feature
            elif isinstance(improved_feature, list) and len(improved_feature) > 0:
                return improved_feature[0]  # Take first feature if array returned
            else:
                return None
                
        except Exception as e:
            print(f"Error generating improved feature: {e}")
            return None
