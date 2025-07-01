import os
import json
import requests

from config.config_loader import Config
from utils.prompt_manager import prompt_manager

class Agent:
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        self.model = config.get_env("GROK_MODEL")
        self.api_key = config.get_env("GROK_API_KEY")
        
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
        """Send a message to Grok and return the assistant's response."""
        url = "https://api.x.ai/v1/chat/completions"
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

        print(f"📤 Sending to Grok:\n{json.dumps(payload, indent=2)}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()

            print(f"📥 Response:\n{response.text}")

            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"❌ Agent '{self.name}' failed: {e}")
            return ""
        
        

    def __repr__(self):
        return f"<Agent name={self.name}>"