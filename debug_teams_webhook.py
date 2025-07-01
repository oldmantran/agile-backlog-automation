#!/usr/bin/env python3
"""
Debug script to test Teams webhook notifications with detailed logging.
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_teams_webhook_detailed():
    """Test Teams webhook with detailed debugging information."""
    print("🔍 Debugging Teams webhook notification...")
    
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    print(f"🔗 Webhook URL: {webhook_url[:50]}..." if webhook_url else "❌ No webhook URL found")
    
    if not webhook_url:
        print("❌ TEAMS_WEBHOOK_URL not found in environment variables")
        return
    
    # Test different payload formats
    test_payloads = [
        # Simple text format (current format)
        {
            "name": "Simple Text",
            "payload": {"text": "🧪 Test message from Agile Backlog Automation - Simple Text Format"}
        },
        # MessageCard format (legacy but more compatible)
        {
            "name": "MessageCard Format",
            "payload": {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "summary": "Test from Agile Backlog Automation",
                "themeColor": "0076D7",
                "title": "🧪 Test Notification",
                "text": "This is a test message from Agile Backlog Automation using MessageCard format."
            }
        },
        # Adaptive Card format (modern)
        {
            "name": "Adaptive Card Format",
            "payload": {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "type": "AdaptiveCard",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "size": "Medium",
                                    "weight": "Bolder",
                                    "text": "🧪 Test Notification"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "This is a test message from Agile Backlog Automation using Adaptive Card format.",
                                    "wrap": True
                                }
                            ],
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "version": "1.2"
                        }
                    }
                ]
            }
        }
    ]
    
    for test in test_payloads:
        print(f"\n📤 Testing {test['name']}...")
        print(f"📋 Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            response = requests.post(
                webhook_url, 
                json=test['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            print(f"📝 Response Text: {response.text}")
            
            if response.status_code in [200, 202]:
                print(f"✅ {test['name']} sent successfully!")
            elif response.status_code == 400:
                print(f"❌ {test['name']} failed - Bad Request (webhook might be expecting different format)")
            elif response.status_code == 404:
                print(f"❌ {test['name']} failed - Webhook URL not found or expired")
            elif response.status_code == 429:
                print(f"⚠️ {test['name']} rate limited - too many requests")
            else:
                print(f"❌ {test['name']} failed with status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ {test['name']} timed out")
        except requests.exceptions.ConnectionError:
            print(f"🔌 {test['name']} connection error")
        except Exception as e:
            print(f"💥 {test['name']} exception: {e}")
    
    print("\n" + "="*60)
    print("🔍 TROUBLESHOOTING TIPS:")
    print("1. Check if the webhook URL is still valid in Teams")
    print("2. Verify the webhook hasn't expired")
    print("3. Check if the Teams channel still exists")
    print("4. Ensure you have permissions to post to the channel")
    print("5. Try creating a new webhook connector in Teams")
    print("="*60)

if __name__ == "__main__":
    test_teams_webhook_detailed()
