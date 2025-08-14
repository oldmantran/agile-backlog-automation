#!/usr/bin/env python3
"""Detailed test of vision optimization to debug the issue"""

import requests
import json
import time

# First login to get a fresh token
login_url = "http://localhost:8000/api/auth/login"
login_data = {
    "username": "testuser",
    "password": "Test123!"
}

print("1. Getting fresh auth token...")
login_response = requests.post(login_url, json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

response_data = login_response.json()
token = response_data.get("data", {}).get("tokens", {}).get("access_token")
print(f"[OK] Got token: {token[:30]}...")

# Test the vision optimization with detailed error capture
optimize_url = "http://localhost:8000/api/vision/optimize"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Test with the exact vision from the browser
test_data = {
    "original_vision": """Conversational Tutoring Assistant for Students
Product Vision
For students and academic support teams seeking on-demand help, TutorBot is a conversational AI assistant that provides real-time tutoring, study guidance, and concept reinforcement across subjects. Unlike static help centers or search-based tools, TutorBot uses natural language understanding and curriculum alignment to deliver contextual, scaffolded support.
Target Audience
    • Students (middle school to college), tutoring centers, edtech platforms
    • Needs: On-demand help, concept reinforcement, engagement
BusGoals
    1. Improve student comprehension scores by 25%
    2. Achieve 90% helpfulness rating acrosions
    3. Integrate with 5 LMS and 3 curriculum providers
    4. Enable multilingual support and accessibility features
    5. Launch in 10K+ student accounts within 6 months
Key Metrics
    • Comprrovement
    • Helpfulness Rating
    • Integration Success
    • Accessibility Coverage
    • Student Adoption
Unique Value Proposition
TutorBot delivers personalized academic support—anytime, anywhere—helping students master concepts and build conf""",
    "domains": [
        {"domain": "education", "priority": "primary"}
    ]
}

print("\nAlso testing if the vision has whitespace issues...")
print(f"Vision length: {len(test_data['original_vision'])} characters")
print(f"Vision starts with: '{test_data['original_vision'][:50]}...'")

print("\n2. Testing vision optimization...")
print(f"Request URL: {optimize_url}")
print(f"Request headers: {headers}")
print(f"Request data: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(optimize_url, json=test_data, headers=headers)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response text: {response.text[:500]}...")
    
    if response.status_code == 400:
        print("\n[ERROR] 400 Bad Request - Server rejected the request")
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Raw error: {response.text}")
    elif response.status_code == 200:
        print("\n[OK] Vision optimization successful!")
        result = response.json()
        if 'data' in result:
            data = result['data']
            print(f"Original Score: {data.get('original_score', 'N/A')}")
            print(f"Optimized Score: {data.get('optimized_score', 'N/A')}")
        else:
            print(f"Result: {json.dumps(result, indent=2)[:200]}...")
            
except Exception as e:
    print(f"\n[ERROR] Request failed with exception: {e}")
    import traceback
    traceback.print_exc()