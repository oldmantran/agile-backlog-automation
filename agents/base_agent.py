import os
import json
import requests
import logging
import time
import signal
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps

from config.config_loader import Config
from utils.prompt_manager import prompt_manager
from utils.llm_config_manager import get_llm_provider_config

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

class TimeoutError(AgentError):
    """Exception raised when agent execution times out."""
    pass

class CircuitBreakerError(AgentError):
    """Exception raised when circuit breaker is open."""
    pass

def timeout_handler(signum, frame):
    """Handler for timeout signals."""
    raise TimeoutError("Agent execution timed out")

def with_timeout(timeout_seconds: int):
    """Decorator to add timeout to agent methods."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # For Windows compatibility, we'll use a different approach
            import threading
            import time
            
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            
            # Use instance timeout if available, otherwise use decorator timeout
            actual_timeout = timeout_seconds
            if len(args) > 0 and hasattr(args[0], 'timeout_seconds'):
                actual_timeout = args[0].timeout_seconds
            
            thread.join(actual_timeout)
            
            if thread.is_alive():
                logger.error(f"Function {func.__name__} timed out after {actual_timeout} seconds")
                raise TimeoutError(f"Function {func.__name__} timed out after {actual_timeout} seconds")
            
            if exception[0]:
                raise exception[0]
                
            return result[0]
        return wrapper
    return decorator

class CircuitBreaker:
    """Circuit breaker pattern implementation for agent reliability."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

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
        
        # Initialize circuit breaker for reliability
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        # Get timeout configuration from settings
        agent_config = config.settings.get('agents', {}).get(name, {})
        self.timeout_seconds = agent_config.get('timeout_seconds', 120)  # Default 2 minutes
        
        # Check for agent-specific model override
        agent_model_override = agent_config.get('model')
        if agent_model_override:
            print(f"[MODEL] Agent {name} using model override: {agent_model_override}")
            self.model = agent_model_override
        
        logger.info(f"Initialized agent: {name} with provider: {self.llm_provider}, timeout: {self.timeout_seconds}s")
    
    def _setup_llm_config(self):
        """Setup LLM provider configuration from database with environment fallback."""
        try:
            # Try to get configuration from database first (force refresh for latest config)
            from utils.llm_config_manager import LLMConfigManager
            from utils.user_id_resolver import user_id_resolver
            config_manager = LLMConfigManager()
            user_id = user_id_resolver.get_default_user_id()
            logger.info(f"Debug: Using user_id: {user_id}")
            provider_config = config_manager.force_refresh_configuration(user_id)
            logger.info(f"Debug: Loaded provider_config: {provider_config}")
            self.llm_provider = provider_config['provider']
            
            if self.llm_provider == "openai":
                # Use model from database if available, otherwise from environment
                self.model = provider_config.get('model') or self.config.get_env("OPENAI_MODEL") or 'gpt-5-mini'
                # Always get OpenAI API key from environment for security
                self.api_key = self.config.get_env("OPENAI_API_KEY")
                self.api_url = "https://api.openai.com/v1/chat/completions"
            elif self.llm_provider == "grok":
                # Use model from database if available, otherwise from environment
                self.model = provider_config.get('model') or self.config.get_env("GROK_MODEL") or 'grok-4-latest'
                # Always get Grok API key from environment for security
                self.api_key = self.config.get_env("GROK_API_KEY")
                self.api_url = "https://api.x.ai/v1/chat/completions"
            elif self.llm_provider == "ollama":
                self.model = provider_config.get('model') or self.config.get_env("OLLAMA_MODEL") or 'qwen2.5:14b-instruct-q4_K_M'
                self.api_key = None  # No API key needed for local Ollama
                self.api_url = provider_config.get('base_url', 'http://localhost:11434')
                # Import Ollama provider
                try:
                    from utils.ollama_client import create_ollama_provider
                    preset = provider_config.get('preset', 'high_quality')
                    self.ollama_provider = create_ollama_provider(preset=preset)
                except ImportError:
                    raise AgentError("Ollama client not available. Install with: pip install ollama-python")
            else:
                raise AgentError(f"Unsupported LLM provider: {self.llm_provider}")
            
            logger.info(f"[CONFIG] Loaded LLM config from database: {self.llm_provider} ({self.model})")
            
        except Exception as e:
            logger.warning(f"Failed to load LLM config from database: {e}. Falling back to environment variables.")
            
            # Fallback to environment variables
            self.llm_provider = self.config.get_env("LLM_PROVIDER") or "openai"
            
            if self.llm_provider == "openai":
                self.model = self.config.get_env("OPENAI_MODEL") or "gpt-5-mini"
                self.api_key = self.config.get_env("OPENAI_API_KEY")
                self.api_url = "https://api.openai.com/v1/chat/completions"
            elif self.llm_provider == "grok":
                self.model = self.config.get_env("GROK_MODEL") or "grok-beta"
                self.api_key = self.config.get_env("GROK_API_KEY")
                self.api_url = "https://api.x.ai/v1/chat/completions"
            elif self.llm_provider == "ollama":
                self.model = self.config.get_env("OLLAMA_MODEL") or "qwen2.5:14b-instruct-q4_K_M"
                self.api_key = None  # No API key needed for local Ollama
                self.api_url = self.config.get_env("OLLAMA_BASE_URL") or "http://localhost:11434"
                # Import Ollama provider
                try:
                    from utils.ollama_client import create_ollama_provider
                    self.ollama_provider = create_ollama_provider(
                        preset=self.config.get_env("OLLAMA_PRESET") or "balanced"
                    )
                except ImportError:
                    raise AgentError("Ollama client not available. Install with: pip install ollama-python")
            else:
                raise AgentError(f"Unsupported LLM provider: {self.llm_provider}")
            
            logger.info(f"[CONFIG] Loaded LLM config from environment: {self.llm_provider} ({self.model})")
        
        # Validate API key (except for Ollama)
        if self.llm_provider != "ollama" and not self.api_key:
            raise AgentError(f"API key not found for provider: {self.llm_provider}")
    
    def _validate_prompt_template(self):
        """Validate that the prompt template exists and is properly formatted."""
        try:
            validation = prompt_manager.validate_template(self.name)
            logger.info(f"DEBUG: Template validation for {self.name}: {validation}")
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
        if not self.template_valid:
            raise PromptError(f"Template validation failed for {self.name} - cannot generate prompt")
        
        try:
            # Ensure context is not None
            context = context or {}
            
            # Add debug logging for context variables
            # Generate prompt using template system
            logger.debug(f"Generating prompt for {self.name} with {len(context)} context variables")
            
            return prompt_manager.get_prompt(self.name, context)
        except Exception as e:
            logger.error(f"Failed to generate prompt for {self.name}: {e}")
            raise PromptError(f"Failed to generate prompt for {self.name}: {e}")
    
    
    def run(self, user_input: str, context: dict = None) -> str:
        """Send a message to the selected LLM and return the assistant's response with comprehensive error handling."""
        start_time = datetime.now()
        
        try:
            # Update execution tracking
            self.execution_count += 1
            self.last_execution_time = start_time
            
            # Use circuit breaker to protect against repeated failures
            result = self.circuit_breaker.call(self._execute_with_timeout, user_input, context)
            
            # Update success tracking
            self.success_count += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"[SUCCESS] {self.name} completed successfully in {execution_time:.2f}s")
            
            return result
            
        except CircuitBreakerError as e:
            self.error_count += 1
            error_msg = f"[ERROR] {self.name} circuit breaker is open - too many recent failures"
            logger.error(error_msg)
            raise AgentError(error_msg) from e
            
        except TimeoutError as e:
            self.error_count += 1
            error_msg = f"[ERROR] {self.name} timed out after {self.timeout_seconds} seconds"
            logger.error(error_msg)
            raise AgentError(error_msg) from e
            
        except Exception as e:
            self.error_count += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"[ERROR] {self.name} failed after {execution_time:.2f}s: {str(e)}"
            logger.error(error_msg)
            raise AgentError(error_msg) from e
    
    @with_timeout(120)  # This will be overridden by instance timeout
    def _execute_with_timeout(self, user_input: str, context: dict = None) -> str:
        """Execute the agent with timeout protection."""
        # Override timeout dynamically
        import threading
        current_thread = threading.current_thread()
        if hasattr(current_thread, '_timeout'):
            current_thread._timeout = self.timeout_seconds
        
        # Generate prompt with context
        system_prompt = self.get_prompt(context)
        
        logger.info(f"Executing {self.name} (attempt {self.execution_count}) with {self.llm_provider}")
        
        # Handle Ollama differently
        if self.llm_provider == "ollama":
            result = self._run_ollama(system_prompt, user_input)
        else:
            # Prepare request payload for cloud providers
            payload = self._prepare_request_payload(system_prompt, user_input)
            logger.debug(f"Request payload for {self.name}: {json.dumps(payload, indent=2)}")
            
            # Make API request with retry logic
            response = self._make_api_request(payload)
            
            # Process response
            result = self._process_response(response)
        
        return result
    
    def _run_ollama(self, system_prompt: str, user_input: str) -> str:
        """Run inference using local Ollama."""
        try:
            logger.info(f"[OLLAMA] Using local Ollama model: {self.model}")
            return self.ollama_provider.generate_response(
                system_prompt=system_prompt,
                user_input=user_input,
                temperature=0.7,
                max_tokens=4000  # Reduced for consistency
            )
        except Exception as e:
            logger.error(f"[ERROR] Ollama inference failed: {e}")
            raise CommunicationError(f"Ollama inference failed: {str(e)}")
    
    def _prepare_request_payload(self, system_prompt: str, user_input: str) -> dict:
        """Prepare the request payload for the LLM API."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }
        
        # GPT-5 models have different API requirements
        if self.model and 'gpt-5' in self.model.lower():
            # GPT-5 models use 'max_completion_tokens' instead of 'max_tokens'
            payload["max_completion_tokens"] = 4000
            # GPT-5 models only support default temperature (1.0), don't set custom temperature
        else:
            # All other models (GPT-4, GPT-3.5, Grok, etc.)
            payload["temperature"] = 0.7
            payload["max_tokens"] = 4000
        
        return payload
    
    def _make_api_request(self, payload: dict) -> requests.Response:
        """Make API request with retry logic and comprehensive error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 3  # Reduced from 5 to prevent long hangs
        base_delay = 1   # Reduced from 2 to faster recovery
        timeout = 30     # Reduced from 60 to prevent long hangs
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Making API request to {self.llm_provider} (attempt {attempt + 1}/{max_retries})")
                response = requests.post(
                    self.api_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=timeout
                )
                
                # Handle different response status codes
                if response.status_code == 200:
                    logger.info(f"[SUCCESS] API request successful on attempt {attempt + 1}")
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
                    try:
                        error_data = response.json() if response.content else {}
                        # Handle string responses (some APIs return plain text errors)
                        if isinstance(error_data, str):
                            error_msg = error_data
                        else:
                            # Handle nested error structure
                            error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                    except:
                        # If JSON parsing fails, use response text
                        error_msg = response.text if response.text else f"HTTP {response.status_code}"
                    
                    raise CommunicationError(f"API error: {error_msg}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Timeout, retrying in {wait_time}s")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    raise CommunicationError(f"Request timeout after {max_retries} attempts (timeout: {timeout}s)")
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}")
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