import json
import re
import threading
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

class FeatureDecomposerAgent(Agent):
    """
    Agent responsible for decomposing epics into features.
    Focuses on business value, strategic planning, and high-level feature definition.
    """
    
    def __init__(self, config: Config):
        super().__init__("feature_decomposer_agent", config)
        # Initialize quality validator with current configuration
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)

    def decompose_epic(self, epic: dict, context: dict = None, max_features: int = None) -> list[dict]:
        """Break down an epic into detailed features with business value and strategic considerations."""
        
        # Apply max_features constraint if specified (null = unlimited)
        feature_limit = max_features if max_features is not None else None  # None = unlimited
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',  # Will be determined by vision analysis
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'integrations': context.get('integrations', 'standard APIs') if context else 'standard APIs',
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
        
        # Smart model selection optimized for 8B model
        if self.model and ("70b" in self.model.lower() or "34b" in self.model.lower()):
            # Large models detected - use 8B due to memory constraints
            models_to_try = [
                ("llama3.1:8b", 30),    # 8B model: 30 seconds (works with 15GB RAM)
            ]
        else:
            # Use current model with standard timeout
            models_to_try = [(self.model, 60)]
        
        # Try each model until one succeeds
        for model_name, timeout in models_to_try:
            try:
                print(f"🔄 Trying {model_name} with {timeout}s timeout...")
                
                # Temporarily switch to this model
                original_model = self.model
                self.model = model_name
                
                # Update Ollama provider if needed
                if hasattr(self, 'ollama_provider') and self.llm_provider == "ollama":
                    try:
                        from utils.ollama_client import create_ollama_provider
                        self.ollama_provider = create_ollama_provider(preset='balanced')
                    except Exception as e:
                        print(f"⚠️ Failed to switch to {model_name}: {e}")
                        continue
                
                response = self._run_with_timeout(user_input, prompt_context, timeout=timeout)
                
                # Restore original model
                self.model = original_model
                
                print(f"✅ Successfully generated features using {model_name}")
                break
                
            except TimeoutError:
                print(f"⏱️ {model_name} timed out after {timeout}s, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
            except Exception as e:
                print(f"❌ {model_name} failed: {e}, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
        else:
            # All models failed
            print("❌ All models failed for feature generation")
            return []

        try:
            # Handle empty response
            if not response or not response.strip():
                print("⚠️ Empty response from LLM")
                return self._extract_features_from_any_format("", epic, feature_limit)
            
            # Check for markdown code blocks
            # Extract JSON with improved parsing
            cleaned_response = self._extract_json_from_response(response)
            features = json.loads(cleaned_response)
            if isinstance(features, list) and len(features) > 0:
                # Apply the feature limit constraint if specified
                if feature_limit:
                    limited_features = features[:feature_limit]
                    if len(features) > feature_limit:
                        print(f"🔧 [FeatureDecomposerAgent] Limited output from {len(features)} to {len(limited_features)} features (configuration limit)")
                    enhanced_features = self._validate_and_enhance_features(limited_features)
                else:
                    enhanced_features = self._validate_and_enhance_features(features)
                return enhanced_features
            else:
                print("⚠️ LLM response was not a valid list")
                return self._extract_features_from_any_format(response, epic, feature_limit)
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Raw response: {response}")
            return self._extract_features_from_any_format(response, epic, feature_limit)

    def _extract_features_from_any_format(self, response: str, epic: dict, max_features: int = None) -> list[dict]:
        """Extract features from LLM response in any format using intelligent parsing."""
        if not response or not response.strip():
            print("❌ Empty response received")
            return []
        
        # Try to extract features from text format
        extracted_features = self._extract_features_from_text(response, epic)
        
        # Apply limit if specified
        if max_features and len(extracted_features) > max_features:
            extracted_features = extracted_features[:max_features]
            print(f"ℹ️ Limited features to {max_features}")
        
        if extracted_features:
            print(f"✅ Successfully extracted {len(extracted_features)} features from response")
            return self._validate_and_enhance_features(extracted_features)
        else:
            print("❌ Failed to extract any features from response")
            return []

    def _extract_features_from_text(self, text: str, epic: dict) -> list[dict]:
        """Extract features from unstructured text using pattern matching."""
        # No fallback - return empty list instead of creating generic work items
        print("ℹ️ No features extracted from text, returning empty list")
        return []

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
                print(f"⚠️ Critical feature title issue: {', '.join(title_issues)}")
            if not title:
                enhanced_feature['title'] = f"Feature: {feature.get('description', 'Undefined')[:50]}..."
        
        # Validate and fix description
        description = feature.get('description', '')
        if not description or len(description.strip()) < 20:
            # Only show critical description issues
            if not description or len(description.strip()) < 10:
                print(f"⚠️ Critical feature description issue: description too short")
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
                    max_tokens=4000
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
                # Use longer timeout for 70B models
                timeout = 300 if self.model and "70b" in self.model.lower() else 60
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"⚠️ Template {template_to_use} failed: {e}")
            print("🔄 Falling back to default prompt...")
            # Use timeout protection for fallback call
            try:
                timeout = 180 if self.model and "70b" in self.model.lower() else 60
                return self._run_with_timeout(user_input, context, timeout=timeout)
            except TimeoutError:
                print("⚠️ Fallback generation timed out")
                return ""
            except Exception as fallback_e:
                print(f"❌ Fallback generation failed: {fallback_e}")
                return ""

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

    def _run_with_timeout(self, user_input: str, context: dict, timeout: int = 60):
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
