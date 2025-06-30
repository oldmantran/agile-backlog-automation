import os
import json
import requests

from config.config_loader import Config

class Agent:
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        self.prompt_path = config.get_agent_prompt_path(name)
        self.model = config.get_env("GROK_MODEL")
        self.api_key = config.get_env("GROK_API_KEY")
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")

    def run(self, user_input: str) -> str:
        """Send a message to Grok and return the assistant's response."""
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                { "role": "system", "content": self.prompt },
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