"""
Model-Aware Prompt Formatting System

Provides intelligent prompt formatting based on the specific LLM model being used.
Includes token counting, prompt optimization, and context window management.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from utils.safe_logger import get_safe_logger

logger = get_safe_logger(__name__)

@dataclass
class ModelCapabilities:
    """Defines capabilities and limits for a specific model."""
    context_window: int
    supports_system_prompt: bool
    supports_functions: bool
    optimal_format: str  # 'xml', 'markdown', 'plain', 'chatml'
    token_buffer: int = 500  # Safety buffer for response
    
class TokenCounter(ABC):
    """Abstract base class for model-specific token counting."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens for the given text."""
        pass
    
    @abstractmethod
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        pass

class TiktokenCounter(TokenCounter):
    """Token counter for OpenAI models using tiktoken."""
    
    def __init__(self, model: str):
        self.model = model
        self._encoder = None
        
    def _get_encoder(self):
        """Lazy load tiktoken to avoid import issues."""
        if self._encoder is None:
            try:
                import tiktoken
                # Map model to encoding
                if 'gpt-4' in self.model or 'gpt-3.5' in self.model:
                    self._encoder = tiktoken.get_encoding("cl100k_base")
                elif 'gpt-5' in self.model:
                    # GPT-5 likely uses same encoding as GPT-4
                    self._encoder = tiktoken.get_encoding("cl100k_base")
                else:
                    # Fallback for older models
                    self._encoder = tiktoken.get_encoding("p50k_base")
            except ImportError:
                logger.warning("tiktoken not installed, using approximation")
                return None
        return self._encoder
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken or approximation."""
        encoder = self._get_encoder()
        if encoder:
            return len(encoder.encode(text))
        else:
            # Approximation: ~4 characters per token
            return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        encoder = self._get_encoder()
        if encoder:
            tokens = encoder.encode(text)
            if len(tokens) <= max_tokens:
                return text
            truncated_tokens = tokens[:max_tokens]
            return encoder.decode(truncated_tokens)
        else:
            # Character-based approximation
            max_chars = max_tokens * 4
            return text[:max_chars]

class ClaudeTokenCounter(TokenCounter):
    """Token counter for Anthropic Claude models."""
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count for Claude models."""
        # Claude's tokenization is similar to GPT but slightly different
        # Use conservative estimate: ~3.5 characters per token
        return len(text) // 3.5
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text for Claude."""
        max_chars = int(max_tokens * 3.5)
        return text[:max_chars]

class LlamaTokenCounter(TokenCounter):
    """Token counter for Llama/Ollama models."""
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count for Llama models."""
        # Llama uses SentencePiece tokenization
        # Conservative estimate: ~4 characters per token
        return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text for Llama."""
        max_chars = max_tokens * 4
        return text[:max_chars]

class PromptFormatter(ABC):
    """Abstract base class for model-specific prompt formatting."""
    
    @abstractmethod
    def format_messages(self, system: str, user: str, assistant: Optional[str] = None) -> List[Dict[str, str]]:
        """Format messages for the specific model."""
        pass
    
    @abstractmethod
    def optimize_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt for better model performance."""
        pass

class GPTPromptFormatter(PromptFormatter):
    """Formatter for OpenAI GPT models."""
    
    def format_messages(self, system: str, user: str, assistant: Optional[str] = None) -> List[Dict[str, str]]:
        """Standard OpenAI message format."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
        if assistant:
            messages.append({"role": "assistant", "content": assistant})
        return messages
    
    def optimize_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt for GPT models."""
        # GPT performs well with structured markdown
        optimized = prompt
        
        # Add clear section headers if not present
        if "##" not in prompt and len(prompt) > 500:
            # Auto-structure long prompts
            sections = prompt.split('\n\n')
            if len(sections) > 3:
                optimized = "\n\n".join([
                    f"## Section {i+1}\n{section}" 
                    for i, section in enumerate(sections)
                ])
        
        # GPT responds well to explicit instructions
        if context.get('needs_json_output'):
            optimized += "\n\nRespond with valid JSON only."
        
        return optimized

class ClaudePromptFormatter(PromptFormatter):
    """Formatter for Anthropic Claude models."""
    
    def format_messages(self, system: str, user: str, assistant: Optional[str] = None) -> List[Dict[str, str]]:
        """Claude's preferred message format."""
        # Claude performs better with XML-style tags
        formatted_user = f"<user_request>\n{user}\n</user_request>"
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": formatted_user}
        ]
        if assistant:
            messages.append({"role": "assistant", "content": assistant})
        return messages
    
    def optimize_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt for Claude models using XML tags."""
        # Claude responds well to XML-style structuring
        optimized = prompt
        
        # Add thinking tags for complex reasoning
        if context.get('requires_reasoning'):
            optimized = f"<thinking>\nLet me analyze this step by step.\n</thinking>\n\n{optimized}"
        
        # Use clear XML sections for structured data
        if context.get('has_examples'):
            optimized = re.sub(
                r'Example:?\s*\n',
                '<example>\n',
                optimized
            )
            optimized = re.sub(
                r'\n(?=\n|$)',
                '\n</example>\n',
                optimized
            )
        
        return optimized

class OllamaPromptFormatter(PromptFormatter):
    """Formatter for Ollama/Llama models."""
    
    def format_messages(self, system: str, user: str, assistant: Optional[str] = None) -> List[Dict[str, str]]:
        """Format for Ollama API."""
        # Ollama uses similar format to OpenAI
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
        if assistant:
            messages.append({"role": "assistant", "content": assistant})
        return messages
    
    def optimize_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt for Llama models."""
        # Llama models often need more explicit instructions
        optimized = prompt
        
        # Add clear task boundaries
        if not prompt.startswith("Task:"):
            optimized = f"Task: {optimized}"
        
        # Llama benefits from examples in specific format
        if context.get('has_examples'):
            optimized = optimized.replace("Example:", "### Example:")
        
        return optimized

class ModelAwareFormatter:
    """Main class for model-aware prompt formatting."""
    
    # Model capabilities database
    MODEL_CAPABILITIES = {
        # OpenAI models
        "gpt-4": ModelCapabilities(128000, True, True, "markdown"),
        "gpt-4-turbo": ModelCapabilities(128000, True, True, "markdown"),
        "gpt-3.5-turbo": ModelCapabilities(16384, True, True, "markdown"),
        "gpt-5": ModelCapabilities(200000, True, True, "markdown"),  # Estimated
        "gpt-5-mini": ModelCapabilities(128000, True, True, "markdown"),
        "gpt-5-nano": ModelCapabilities(64000, True, True, "markdown"),
        
        # Anthropic models
        "claude-3-opus": ModelCapabilities(200000, True, False, "xml"),
        "claude-3-sonnet": ModelCapabilities(200000, True, False, "xml"),
        "claude-3-haiku": ModelCapabilities(200000, True, False, "xml"),
        
        # Ollama/Llama models
        "llama2": ModelCapabilities(4096, True, False, "plain"),
        "llama3": ModelCapabilities(8192, True, False, "plain"),
        "mistral": ModelCapabilities(8192, True, False, "plain"),
        "mixtral": ModelCapabilities(32768, True, False, "plain"),
        "codellama": ModelCapabilities(16384, True, False, "plain"),
        
        # Default fallback
        "default": ModelCapabilities(4096, True, False, "plain")
    }
    
    def __init__(self):
        self.token_counters = {}
        self.formatters = {}
        
    def get_token_counter(self, provider: str, model: str) -> TokenCounter:
        """Get appropriate token counter for the model."""
        key = f"{provider}:{model}"
        
        if key not in self.token_counters:
            if provider == "openai" or provider == "grok":
                self.token_counters[key] = TiktokenCounter(model)
            elif provider == "anthropic":
                self.token_counters[key] = ClaudeTokenCounter()
            else:  # ollama and others
                self.token_counters[key] = LlamaTokenCounter()
        
        return self.token_counters[key]
    
    def get_formatter(self, provider: str) -> PromptFormatter:
        """Get appropriate formatter for the provider."""
        if provider not in self.formatters:
            if provider == "openai" or provider == "grok":
                self.formatters[provider] = GPTPromptFormatter()
            elif provider == "anthropic":
                self.formatters[provider] = ClaudePromptFormatter()
            else:  # ollama and others
                self.formatters[provider] = OllamaPromptFormatter()
        
        return self.formatters[provider]
    
    def get_capabilities(self, model: str) -> ModelCapabilities:
        """Get model capabilities."""
        # Try exact match first
        if model in self.MODEL_CAPABILITIES:
            return self.MODEL_CAPABILITIES[model]
        
        # Try prefix match (e.g., "gpt-4-0613" matches "gpt-4")
        for key, capabilities in self.MODEL_CAPABILITIES.items():
            if model.startswith(key):
                return capabilities
        
        # Return default
        return self.MODEL_CAPABILITIES["default"]
    
    def format_prompt(self, 
                     provider: str,
                     model: str,
                     system_prompt: str,
                     user_prompt: str,
                     context: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, str]], int]:
        """
        Format prompt optimally for the given model.
        
        Returns:
            Tuple of (formatted_messages, estimated_tokens)
        """
        context = context or {}
        
        # Get components
        formatter = self.get_formatter(provider)
        counter = self.get_token_counter(provider, model)
        capabilities = self.get_capabilities(model)
        
        # Optimize prompts
        optimized_system = formatter.optimize_prompt(system_prompt, context)
        optimized_user = formatter.optimize_prompt(user_prompt, context)
        
        # Check token limits
        total_tokens = counter.count_tokens(optimized_system + optimized_user)
        available_tokens = capabilities.context_window - capabilities.token_buffer
        
        if total_tokens > available_tokens:
            # Need to truncate - prioritize user prompt
            system_budget = int(available_tokens * 0.3)  # 30% for system
            user_budget = available_tokens - system_budget
            
            optimized_system = counter.truncate_to_tokens(optimized_system, system_budget)
            optimized_user = counter.truncate_to_tokens(optimized_user, user_budget)
            
            logger.warning(
                f"Truncated prompts for {model}: {total_tokens} -> {available_tokens} tokens"
            )
        
        # Format messages
        messages = formatter.format_messages(optimized_system, optimized_user)
        
        # Final token count
        final_tokens = counter.count_tokens(optimized_system + optimized_user)
        
        return messages, final_tokens
    
    def estimate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for the given model and token counts."""
        # Cost per 1K tokens (approximate)
        COSTS = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "gpt-5": {"prompt": 0.05, "completion": 0.10},  # Estimated
            "gpt-5-mini": {"prompt": 0.02, "completion": 0.04},
            "gpt-5-nano": {"prompt": 0.01, "completion": 0.02},
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "grok": {"prompt": 0.01, "completion": 0.02},
        }
        
        if model in COSTS:
            cost_info = COSTS[model]
        else:
            # Try prefix match
            cost_info = None
            for key, info in COSTS.items():
                if model.startswith(key):
                    cost_info = info
                    break
            
            if not cost_info:
                # Default/unknown model
                cost_info = {"prompt": 0.001, "completion": 0.002}
        
        prompt_cost = (prompt_tokens / 1000) * cost_info["prompt"]
        completion_cost = (completion_tokens / 1000) * cost_info["completion"]
        
        return prompt_cost + completion_cost

# Global instance
model_formatter = ModelAwareFormatter()