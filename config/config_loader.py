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

        # Check for testing limits and warn if found
        self._warn_if_testing_limits()

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
            # Ollama (Local LLM)
            "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL"),
            "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "OLLAMA_PRESET": os.getenv("OLLAMA_PRESET", "balanced"),
            # LLM Provider
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

    def _warn_if_testing_limits(self):
        """Warn if testing limits are detected in configuration."""
        limits = self.settings.get('workflow', {}).get('limits', {})
        max_epics = limits.get('max_epics')
        max_features = limits.get('max_features_per_epic')
        
        if max_epics is not None and max_epics <= 5:
            print(f"⚠️  WARNING: max_epics is set to {max_epics} - this may be a testing configuration!")
            print("   For production use, set max_epics to null in config/settings.yaml")
            
        if max_features is not None and max_features <= 5:
            print(f"⚠️  WARNING: max_features_per_epic is set to {max_features} - this may be a testing configuration!")
            print("   For production use, set max_features_per_epic to null in config/settings.yaml")

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