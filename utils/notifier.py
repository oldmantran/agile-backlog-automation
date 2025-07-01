import os
import smtplib
import requests
from email.mime.text import MIMEText
from dotenv import load_dotenv
from typing import Dict, Any
from config.config_loader import Config

# Load environment variables once
load_dotenv()

class Notifier:
    def __init__(self, config: Config = None):
        self.config = config
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))
        self.use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")
        
        # Get notification settings from config
        if config:
            notification_settings = config.settings.get('notifications', {})
            self.enabled = notification_settings.get('enabled', True)
            self.channels = notification_settings.get('channels', ['teams', 'email'])
        else:
            self.enabled = True
            self.channels = ['teams', 'email']

    def send_completion_notification(self, workflow_data: Dict[str, Any], stats: Dict[str, Any]):
        """Send workflow completion notification."""
        if not self.enabled:
            return
        
        # Generate summary message
        project_name = workflow_data.get('metadata', {}).get('project_context', {}).get('project_name', 'Unknown Project')
        
        message = f"""
🎉 **Agile Backlog Automation Complete**

**Project:** {project_name}
**Epics Generated:** {stats.get('epics_generated', 0)}
**Features Generated:** {stats.get('features_generated', 0)}
**Tasks Generated:** {stats.get('tasks_generated', 0)}
**Execution Time:** {stats.get('execution_time_seconds', 0):.1f} seconds

✅ All stages completed successfully!
        """.strip()
        
        if 'teams' in self.channels:
            self.send_teams(message)
        if 'email' in self.channels:
            self.send_email("Backlog Automation Complete", message)
    
    def send_error_notification(self, error: Exception, metadata: Dict[str, Any]):
        """Send error notification."""
        if not self.enabled:
            return
        
        stages_completed = metadata.get('stages_completed', [])
        
        message = f"""
❌ **Agile Backlog Automation Failed**

**Error:** {str(error)}
**Stages Completed:** {', '.join(stages_completed) if stages_completed else 'None'}
**Time:** {metadata.get('start_time', 'Unknown')}

Please check the logs for more details.
        """.strip()
        
        if 'teams' in self.channels:
            self.send_teams(message)
        if 'email' in self.channels:
            self.send_email("Backlog Automation Failed", message)

    def send_teams(self, message: str):
        if not self.teams_webhook:
            print("⚠️ Teams webhook not configured.")
            return False

        payload = { "text": message }
        try:
            response = requests.post(self.teams_webhook, json=payload)
            if response.status_code in [200, 202]:
                print("✅ Teams notification sent.")
                return True
            else:
                print(f"❌ Teams error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Teams exception: {e}")
            return False

    def send_email(self, subject: str, body: str):
        if not all([self.smtp_server, self.username, self.password, self.email_from, self.email_to]):
            print("⚠️ Email settings incomplete.")
            return False

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.email_from
        msg["To"] = self.email_to

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.email_from, [self.email_to], msg.as_string())
                print("✅ Email notification sent.")
                return True
        except Exception as e:
            print(f"❌ Email exception: {e}")
            return False