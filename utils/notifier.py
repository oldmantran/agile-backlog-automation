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
            print("🔇 Notifications disabled in configuration")
            return
        
        print(f"📢 Sending completion notification - enabled channels: {self.channels}")
        print(f"📊 Statistics received: {stats}")
        print(f"📋 Workflow data keys: {list(workflow_data.keys())}")
        
        # Generate summary message
        project_name = workflow_data.get('metadata', {}).get('project_context', {}).get('project_name', 'Unknown Project')
        exec_time = stats.get('execution_time_seconds')
        
        # Format execution time
        if exec_time is not None:
            if exec_time < 60:
                exec_time_str = f"{exec_time:.1f} seconds"
            elif exec_time < 3600:
                minutes = int(exec_time // 60)
                seconds = exec_time % 60
                exec_time_str = f"{minutes}m {seconds:.1f}s"
            else:
                hours = int(exec_time // 3600)
                minutes = int((exec_time % 3600) // 60)
                exec_time_str = f"{hours}h {minutes}m"
        else:
            exec_time_str = "N/A"
        
        # Add warning if any artifacts are missing
        warning = ""
        azure_integration = workflow_data.get('azure_integration', {})
        if azure_integration.get('missing_artifacts'):
            warning = f"\n\n⚠️ *Warning*: The following artifact types were NOT created: {', '.join(azure_integration['missing_artifacts'])}. Please review the logs and agent outputs."
        elif azure_integration.get('warning'):
            warning = f"\n\n⚠️ {azure_integration['warning']}"
        
        # Add Azure DevOps integration info if available
        ado_summary = ""
        if azure_integration.get('work_items_created'):
            ado_summary = f"\n**Azure DevOps Work Items Created:** {azure_integration['work_items_created']}"
        
        message = f"""
🎉 **Agile Backlog Automation Complete**

**Project:** {project_name}
**Epics Generated:** {stats.get('epics_generated', 0)}
**Features Generated:** {stats.get('features_generated', 0)}
**User Stories Generated:** {stats.get('user_stories_generated', 0)}
**Tasks Generated:** {stats.get('tasks_generated', 0)}
**Test Cases Generated:** {stats.get('test_cases_generated', 0)}
**Execution Time:** {exec_time_str}{ado_summary}{warning}

✅ All stages completed. Review above for any warnings.
        """.strip()
        
        success_count = 0
        if 'teams' in self.channels:
            print("📤 Sending Teams notification...")
            try:
                if self.send_teams(message):
                    success_count += 1
                    print("✅ Teams notification sent successfully")
                else:
                    print("❌ Teams notification failed")
            except Exception as e:
                print(f"❌ Teams notification error: {e}")
                
        if 'email' in self.channels:
            print("📧 Sending email notification...")
            try:
                if self.send_email("Backlog Automation Complete", message):
                    success_count += 1
                    print("✅ Email notification sent successfully")
                else:
                    print("❌ Email notification failed")
            except Exception as e:
                print(f"❌ Email notification error: {e}")
                import traceback
                print(f"Email error traceback: {traceback.format_exc()}")
        
        print(f"📊 Notification summary: {success_count}/{len(self.channels)} channels successful")
    
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

    def send_critical_notification(self, notification_data: Dict[str, Any]):
        """Send critical issue notification for high-priority backlog discrepancies."""
        if not self.enabled:
            return
        high_priority_count = notification_data.get('high_priority_count', 0)
        total_discrepancies = notification_data.get('total_discrepancies', 0)
        timestamp = notification_data.get('timestamp', 'Unknown')
        report_summary = notification_data.get('report_summary', {})
        details = ""
        if report_summary:
            details = f"\n\nSummary: {report_summary}"
        message = f"""
🚨 **Critical Backlog Issues Detected**

**High Priority Issues:** {high_priority_count}
**Total Discrepancies:** {total_discrepancies}
**Detection Time:** {timestamp}{details}

**Action Required:** Please review the backlog validation report and address critical issues immediately.

Critical issues may include:
- Missing required work items
- Incomplete hierarchies
- Quality validation failures
- Integration compliance issues

Check the application logs for detailed issue descriptions and remediation steps.
        """.strip()
        if 'teams' in self.channels:
            self.send_teams(message)
        if 'email' in self.channels:
            self.send_email("Critical Backlog Issues Detected", message)

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
            missing_vars = []
            if not self.smtp_server: missing_vars.append("EMAIL_SMTP_SERVER")
            if not self.username: missing_vars.append("EMAIL_USERNAME") 
            if not self.password: missing_vars.append("EMAIL_PASSWORD")
            if not self.email_from: missing_vars.append("EMAIL_FROM")
            if not self.email_to: missing_vars.append("EMAIL_TO")
            print(f"⚠️ Email settings incomplete. Missing: {', '.join(missing_vars)}")
            return False

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.email_from
        msg["To"] = self.email_to

        try:
            print(f"📧 Attempting to send email via {self.smtp_server}:{self.smtp_port} to {self.email_to}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    print("🔒 Starting TLS encryption")
                    server.starttls()
                print("🔐 Logging in to SMTP server")
                server.login(self.username, self.password)
                print("📤 Sending email message")
                server.sendmail(self.email_from, [self.email_to], msg.as_string())
                print("✅ Email notification sent successfully.")
                return True
        except Exception as e:
            print(f"❌ Email exception: {e}")
            print(f"   SMTP Server: {self.smtp_server}:{self.smtp_port}")
            print(f"   TLS Enabled: {self.use_tls}")
            print(f"   From: {self.email_from}")
            print(f"   To: {self.email_to}")
            return False