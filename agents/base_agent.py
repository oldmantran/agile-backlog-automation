import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from config.config_loader import Config
from utils.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class PromptError(AgentError):
    """Exception raised when prompt generation fails."""
    pass

class CommunicationError(AgentError):
    """Exception raised when agent communication fails."""
    pass

class Agent:
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        self.llm_provider = config.get_env("LLM_PROVIDER") or "openai"
        
        # Initialize LLM configuration
        self._setup_llm_config()
        
        # Validate prompt template
        self._validate_prompt_template()
        
        # Agent state tracking
        self.execution_count = 0
        self.last_execution_time = None
        self.error_count = 0
        self.success_count = 0
        
        logger.info(f"Initialized agent: {name} with provider: {self.llm_provider}")
    
    def _setup_llm_config(self):
        """Setup LLM provider configuration."""
        if self.llm_provider == "openai":
            self.model = self.config.get_env("OPENAI_MODEL") or "gpt-4"
            self.api_key = self.config.get_env("OPENAI_API_KEY")
            self.api_url = "https://api.openai.com/v1/chat/completions"
        elif self.llm_provider == "grok":
            self.model = self.config.get_env("GROK_MODEL") or "grok-beta"
            self.api_key = self.config.get_env("GROK_API_KEY")
            self.api_url = "https://api.x.ai/v1/chat/completions"
        else:
            raise AgentError(f"Unsupported LLM provider: {self.llm_provider}")
        
        # Validate API key
        if not self.api_key:
            raise AgentError(f"API key not found for provider: {self.llm_provider}")
    
    def _validate_prompt_template(self):
        """Validate that the prompt template exists and is properly formatted."""
        try:
            validation = prompt_manager.validate_template(self.name)
            if not validation["valid"]:
                logger.warning(f"Template validation failed for {self.name}: {validation.get('error', 'Unknown error')}")
                # Don't raise error, use fallback prompt instead
                self.required_variables = []
                self.template_valid = False
            else:
                self.required_variables = validation.get("required_variables", [])
                self.template_valid = True
                logger.info(f"Template validation successful for {self.name}")
        except Exception as e:
            logger.error(f"Template validation error for {self.name}: {e}")
            self.required_variables = []
            self.template_valid = False
    
    def get_prompt(self, context: dict = None) -> str:
        """Generate the prompt with dynamic context and error handling."""
        try:
            if not self.template_valid:
                logger.warning(f"Using fallback prompt for {self.name} due to template validation failure")
                return self._get_fallback_prompt(context)
            
            return prompt_manager.get_prompt(self.name, context)
        except Exception as e:
            logger.error(f"Failed to generate prompt for {self.name}: {e}")
            return self._get_fallback_prompt(context)
    
    def _get_fallback_prompt(self, context: dict = None) -> str:
        """Generate a fallback prompt when template fails."""
        context = context or {}
        project_name = context.get('project_name', 'Unknown Project')
        domain = context.get('domain', 'software development')
        
        # Agent-specific fallback prompts
        fallback_prompts = {
            'epic_strategist': f"""You are an Epic Strategist working on {project_name} in the {domain} domain.
Your role is to analyze product visions and create high-level epics that align with business objectives.
Focus on strategic thinking and business value.""",
            
            'feature_decomposer_agent': f"""You are a Feature Decomposer working on {project_name} in the {domain} domain.
Your role is to break down epics into manageable features with clear business value.
Focus on user-centric design and business outcomes.""",
            
            'user_story_decomposer_agent': f"""You are a User Story Decomposer working on {project_name} in the {domain} domain.
Your role is to create detailed user stories with acceptance criteria.
Focus on user value and testable requirements.""",
            
            'developer_agent': f"""You are a Developer Agent working on {project_name} in the {domain} domain.
Your role is to create technical tasks and provide time estimates.
Focus on implementation details and technical feasibility.""",
            
            'qa_lead_agent': f"""You are a QA Lead Agent working on {project_name} in the {domain} domain.
Your role is to create test cases and validate requirements.
Focus on quality assurance and test coverage."""
        }
        
        return fallback_prompts.get(self.name, f"You are a {self.name.replace('_', ' ')} agent working on {project_name}.")
    
    def run(self, user_input: str, context: dict = None) -> str:
        """Send a message to the selected LLM and return the assistant's response with comprehensive error handling."""
        start_time = datetime.now()
        
        try:
            # Update execution tracking
            self.execution_count += 1
            self.last_execution_time = start_time
            
            # Generate prompt with context
            system_prompt = self.get_prompt(context)
            
            # Prepare request payload
            payload = self._prepare_request_payload(system_prompt, user_input)
            
            logger.info(f"Executing {self.name} (attempt {self.execution_count})")
            logger.debug(f"Request payload for {self.name}: {json.dumps(payload, indent=2)}")
            
            # Make API request with retry logic
            response = self._make_api_request(payload)
            
            # Process response
            result = self._process_response(response)
            
            # Update success tracking
            self.success_count += 1
            
            logger.info(f"Successfully executed {self.name} in {(datetime.now() - start_time).total_seconds():.2f}s")
            
            return result
            
        except Exception as e:
            # Update error tracking
            self.error_count += 1
            
            logger.error(f"Error executing {self.name}: {e}")
            raise CommunicationError(f"Agent {self.name} failed: {str(e)}")
    
    def _prepare_request_payload(self, system_prompt: str, user_input: str) -> dict:
        """Prepare the request payload for the LLM API."""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
    
    def _make_api_request(self, payload: dict) -> requests.Response:
        """Make API request with retry logic and comprehensive error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 5
        base_delay = 2      
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=60                )
                
                # Handle different response status codes
                if response.status_code == 200:
                    return response
                elif response.status_code == 401:
                    raise CommunicationError(f"Authentication failed for {self.llm_provider}")
                elif response.status_code == 403:
                    raise CommunicationError(f"Access denied for {self.llm_provider}")
                elif response.status_code == 429:
                    # Rate limit - wait longer with increased multiplier
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    import time
                    time.sleep(wait_time)
                    continue
                elif response.status_code >= 500:
                    # Server error - retry with exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                        import time
                        time.sleep(wait_time)
                        continue
                    else:
                        raise CommunicationError(f"Server error after {max_retries} attempts")
                else:
                    # Other client errors
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                    raise CommunicationError(f"API error: {error_msg}")
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Timeout, retrying in {wait_time}s")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    raise CommunicationError(f"Request timeout after {max_retries} attempts")
                    
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Connection error, retrying in {wait_time}s")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    raise CommunicationError("Failed to connect to API server")
        
        raise CommunicationError(f"Request failed after {max_retries} attempts")
    
    def _process_response(self, response: requests.Response) -> str:
        """Process the API response and extract the content."""
        try:
            data = response.json()
            
            # Validate response structure
            if "choices" not in data or not data["choices"]:
                raise CommunicationError("Invalid response format: no choices")
            
            content = data["choices"][0].get("message", {}).get("content", "")
            
            if not content:
                raise CommunicationError("Empty response from LLM")
            
            return content.strip()
            
        except json.JSONDecodeError as e:
            raise CommunicationError(f"Failed to parse JSON response: {e}")
        except KeyError as e:
            raise CommunicationError(f"Missing key in response: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        return {
            "name": self.name,
            "provider": self.llm_provider,
            "model": self.model,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / max(self.execution_count, 1),
            "last_execution_time": self.last_execution_time,
            "template_valid": self.template_valid,
            "required_variables": self.required_variables
        }
    
    def reset_stats(self):
        """Reset agent execution statistics."""
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_execution_time = None
        logger.info(f"Reset statistics for agent: {self.name}")
    
    def __repr__(self):
        return f"<Agent name={self.name} provider={self.llm_provider} model={self.model}>"