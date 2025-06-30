import os
import smtplib
import requests
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# === Microsoft Teams Webhook Test ===
def test_teams_webhook():
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("❌ TEAMS_WEBHOOK_URL not set.")
        return

    payload = {
        "text": "✅ Test message from Agile Backlog Automation system (Teams Webhook)"
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code in [200, 202]:
            # Teams accepts 200 or 202 as success responses:
            print("✅ Teams webhook test sent successfully.")
        else:
            print(f"❌ Teams webhook failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Teams webhook error: {e}")

# === SMTP Email Test ===
def test_email():
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))
    use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    username = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")
    email_from = os.getenv("EMAIL_FROM")
    email_to = os.getenv("EMAIL_TO")

    if not all([smtp_server, username, password, email_from, email_to]):
        print("❌ Missing one or more email environment variables.")
        return

    msg = MIMEText("✅ Test email from Agile Backlog Automation system.")
    msg["Subject"] = "Test Notification"
    msg["From"] = email_from
    msg["To"] = email_to

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.sendmail(email_from, [email_to], msg.as_string())
            print("✅ Test email sent successfully.")
    except Exception as e:
        print(f"❌ Email test failed: {e}")

# === Run Tests ===
if __name__ == "__main__":
    print("🔧 Testing notification channels...\n")
    test_teams_webhook()
    test_email()