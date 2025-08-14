#!/usr/bin/env python3
"""Test the fixed vision optimization endpoint"""

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

# Test the vision optimization with fixed endpoint
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

print("\n2. Testing vision optimization...")
print(f"Request URL: {optimize_url}")
print(f"Request data: {json.dumps(test_data, indent=2)[:200]}...")

try:
    response = requests.post(optimize_url, json=test_data, headers=headers)
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        print("\n[SUCCESS] Vision optimization working!")
        result = response.json()
        print(f"Original Score: {result.get('original_score', 'N/A')}")
        print(f"Optimized Score: {result.get('optimized_score', 'N/A')}")
        print(f"Score Improvement: {result.get('score_improvement', 'N/A')}")
        print(f"Rating Change: {result.get('rating_change', 'N/A')}")
        
        # Check if educational data is included
        if 'original_assessment' in result:
            print("\n[OK] Educational report data included:")
            assessment = result['original_assessment']
            print(f"  - Strengths: {len(assessment.get('strengths', []))} items")
            print(f"  - Weaknesses: {len(assessment.get('weaknesses', []))} items")
            print(f"  - Missing Elements: {len(assessment.get('missing_elements', []))} items")
            print(f"  - Improvement Suggestions: {len(assessment.get('improvement_suggestions', []))} items")
        else:
            print("\n[WARNING] Educational report data missing")
            
    else:
        print("\n[ERROR] Optimization failed")
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"\n[ERROR] Request failed with exception: {e}")
    import traceback
    traceback.print_exc()