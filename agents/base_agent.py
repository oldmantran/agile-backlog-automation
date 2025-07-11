import os
import json
import requests

from config.config_loader import Config
from utils.prompt_manager import prompt_manager

class Agent:
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        self.llm_provider = config.get_env("LLM_PROVIDER") or "openai"
        if self.llm_provider == "openai":
            self.model = config.get_env("OPENAI_MODEL")
            self.api_key = config.get_env("OPENAI_API_KEY")
            self.api_url = "https://api.openai.com/v1/chat/completions"
        else:
            self.model = config.get_env("GROK_MODEL")
            self.api_key = config.get_env("GROK_API_KEY")
            self.api_url = "https://api.x.ai/v1/chat/completions"
        # Validate that template exists
        try:
            validation = prompt_manager.validate_template(name)
            if not validation["valid"]:
                raise FileNotFoundError(f"Prompt template not found: {name}")
            self.required_variables = validation["required_variables"]
        except Exception as e:
            print(f"⚠️ Template validation failed for {name}: {e}")
            self.required_variables = []

    def get_prompt(self, context: dict = None) -> str:
        """Generate the prompt with dynamic context."""
        try:
            return prompt_manager.get_prompt(self.name, context)
        except Exception as e:
            print(f"⚠️ Failed to generate prompt for {self.name}: {e}")
            # Fallback to empty prompt
            return f"You are a {self.name.replace('_', ' ')} agent."

    def run(self, user_input: str, context: dict = None) -> str:
        """Send a message to the selected LLM and return the assistant's response."""
        url = self.api_url
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Generate prompt with context
        system_prompt = self.get_prompt(context)
        payload = {
            "model": self.model,
            "messages": [
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": user_input }
            ]
        }
        print(f"📤 Sending to {self.llm_provider.capitalize()} (model: {self.model}):\n{json.dumps(payload, indent=2)}")
        
        # Retry logic for timeout and rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                print(f"📥 Response:\n{response.text}")
                # OpenAI and Grok both return choices/message structure
                return data["choices"][0]["message"]["content"].strip()
            except requests.exceptions.Timeout as e:
                print(f"⏱️ Timeout on attempt {attempt + 1}/{max_retries} for agent '{self.name}': {e}")
                if attempt == max_retries - 1:
                    print(f"❌ Agent '{self.name}' failed after {max_retries} attempts: {e}")
                    return ""
                # Wait before retrying
                import time
                time.sleep(5 * (attempt + 1))  # Exponential backoff
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    print(f"🚦 Rate limit on attempt {attempt + 1}/{max_retries} for agent '{self.name}': {e}")
                    if attempt == max_retries - 1:
                        print(f"❌ Agent '{self.name}' failed after {max_retries} attempts: {e}")
                        return ""
                    import time
                    time.sleep(10 * (attempt + 1))  # Longer wait for rate limits
                else:
                    print(f"❌ Agent '{self.name}' failed: {e}")
                    return ""
            except Exception as e:
                print(f"❌ Agent '{self.name}' failed: {e}")
                return ""
        

    def __repr__(self):
        return f"<Agent name={self.name}>"