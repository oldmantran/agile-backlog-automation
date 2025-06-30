import os
import smtplib
import requests
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

class Notifier:
    def __init__(self):
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))
        self.use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")

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