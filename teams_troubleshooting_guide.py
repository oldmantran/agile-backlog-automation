#!/usr/bin/env python3
"""
Teams webhook troubleshooting guide and alternative solutions.
"""

def print_troubleshooting_guide():
    """Print comprehensive troubleshooting guide for Teams notifications."""
    
    print("🔍 TEAMS NOTIFICATION TROUBLESHOOTING GUIDE")
    print("="*60)
    
    print("\n📊 CURRENT STATUS:")
    print("✅ Webhook URL is responding (HTTP 202)")
    print("✅ Power Automate is receiving messages")
    print("❌ Messages not appearing in Teams")
    print("🔍 Issue: Power Automate workflow configuration")
    
    print("\n🛠️ IMMEDIATE ACTIONS TO CHECK:")
    print("1. Open Power Automate (https://make.powerautomate.com)")
    print("2. Go to 'My flows' or 'Solutions'")
    print("3. Find the flow with ID: 7714ac49541d42b38fcc79f54a72e64c")
    print("4. Check if the flow is:")
    print("   - ✅ Turned ON")
    print("   - ✅ Not encountering errors")
    print("   - ✅ Actually configured to post to Teams")
    
    print("\n🔧 COMMON POWER AUTOMATE ISSUES:")
    print("• Flow is turned OFF")
    print("• Teams connector is misconfigured")
    print("• Teams channel was deleted/renamed")
    print("• Permissions issues")
    print("• Flow has errors/failures")
    
    print("\n🆕 ALTERNATIVE SOLUTION - DIRECT TEAMS WEBHOOK:")
    print("If Power Automate is problematic, you can create a direct Teams webhook:")
    print("1. Go to your Teams channel")
    print("2. Click '...' > 'Connectors' > 'Incoming Webhook'")
    print("3. Create a new webhook")
    print("4. Replace TEAMS_WEBHOOK_URL in .env with the new direct webhook")
    
    print("\n📝 UPDATED NOTIFIER CODE FOR BETTER TEAMS SUPPORT:")
    print("I can update the notifier.py to support both formats:")
    print("• Power Automate webhooks (current)")
    print("• Direct Teams webhooks (more reliable)")
    print("• Better error handling and logging")

if __name__ == "__main__":
    print_troubleshooting_guide()
