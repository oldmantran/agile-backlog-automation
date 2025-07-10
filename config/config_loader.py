import os
import yaml
from dotenv import load_dotenv

class Config:
    def __init__(self, env_path=".env", settings_path="config/settings.yaml"):
        # Load .env
        load_dotenv(dotenv_path=env_path)

        # Load YAML settings
        with open(settings_path, "r") as f:
            self.settings = yaml.safe_load(f)

        # Load environment variables
        self.env = {
            "AZURE_DEVOPS_PAT": os.getenv("AZURE_DEVOPS_PAT"),
            "AZURE_DEVOPS_ORG": os.getenv("AZURE_DEVOPS_ORG"),
            "AZURE_DEVOPS_PROJECT": os.getenv("AZURE_DEVOPS_PROJECT"),
            # Grok (xAI)
            "GROK_API_KEY": os.getenv("GROK_API_KEY"),
            "GROK_MODEL": os.getenv("GROK_MODEL", "grok-3-latest"),
            # OpenAI
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4.1"),
            # LLM Provider (set to openai or grok)
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "openai"),
            # Notifications
            "TEAMS_WEBHOOK_URL": os.getenv("TEAMS_WEBHOOK_URL"),
            "EMAIL_SMTP_SERVER": os.getenv("EMAIL_SMTP_SERVER"),
            "EMAIL_SMTP_PORT": os.getenv("EMAIL_SMTP_PORT", "587"),
            "EMAIL_USE_TLS": os.getenv("EMAIL_USE_TLS", "true"),
            "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME"),
            "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
            "EMAIL_FROM": os.getenv("EMAIL_FROM"),
            "EMAIL_TO": os.getenv("EMAIL_TO"),
        }

    def get_agent_prompt_path(self, agent_name):
        return self.settings["agents"][agent_name]["prompt_file"]

    def get_workflow_sequence(self):
        return self.settings["workflow"]["sequence"]

    def get_project_paths(self):
        return {
            "area": self.settings["project"]["default_area_path"],
            "iteration": self.settings["project"]["default_iteration_path"]
        }

    def get_notification_settings(self):
        return self.settings.get("notifications", {})

    def get_env(self, key):
        return self.env.get(key)

    def get_setting(self, *keys):
        """Access nested YAML settings with dot-style keys."""
        value = self.settings
        for key in keys:
            value = value.get(key, {})
        return value or None