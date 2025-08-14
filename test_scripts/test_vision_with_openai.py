#!/usr/bin/env python3
"""Test vision optimization with OpenAI configuration"""

import requests
import json
import sqlite3

# First update the LLM config to use OpenAI
conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# Check current config
cursor.execute("""
    SELECT * FROM llm_configurations 
    WHERE user_id = '2' AND agent_name = 'vision_optimizer_agent'
    AND is_active = 1
""")
current_config = cursor.fetchone()
print(f"Current config: {current_config}")

# Update to use OpenAI
cursor.execute("""
    UPDATE llm_configurations 
    SET provider = 'openai', model = 'gpt-4o-mini', preset = 'balanced'
    WHERE user_id = '2' AND agent_name = 'vision_optimizer_agent'
""")
conn.commit()
print("Updated to OpenAI configuration")

# Login to get token
login_url = "http://localhost:8000/api/auth/login"
login_data = {
    "username": "testuser",
    "password": "Test123!"
}

print("\n1. Getting fresh auth token...")
login_response = requests.post(login_url, json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

response_data = login_response.json()
token = response_data.get("data", {}).get("tokens", {}).get("access_token")
print(f"[OK] Got token: {token[:30]}...")

# Test vision optimization
optimize_url = "http://localhost:8000/api/vision/optimize"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

test_data = {
    "original_vision": """AI-Powered Study Assistant
Product Vision: Create an intelligent tutoring system that helps students learn more effectively.
Target Audience: Students from high school to college level
Key Features: Personalized learning paths, real-time feedback, progress tracking
Success Metrics: Improved test scores, increased engagement, better retention rates""",
    "domains": [
        {"domain": "education", "priority": "primary"}
    ]
}

print("\n2. Testing vision optimization with OpenAI...")
print(f"Request URL: {optimize_url}")

try:
    response = requests.post(optimize_url, json=test_data, headers=headers)
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        print("\n[SUCCESS] Vision optimization working!")
        result = response.json()
        data = result.get('data', result)  # Handle both wrapped and unwrapped responses
        
        print(f"\nOriginal Score: {data.get('original_score', 'N/A')}")
        print(f"Optimized Score: {data.get('optimized_score', 'N/A')}")
        print(f"Score Improvement: {data.get('score_improvement', 'N/A')}")
        rating_change = data.get('rating_change', 'N/A')
        if '→' in rating_change:
            rating_change = rating_change.replace('→', '->')
        print(f"Rating Change: {rating_change}")
        
        # Check if educational data is included
        if 'original_assessment' in data:
            print("\n[OK] Educational report data included:")
            assessment = data['original_assessment']
            print(f"  - Strengths: {len(assessment.get('strengths', []))} items")
            if assessment.get('strengths'):
                print(f"    Example: {assessment['strengths'][0]}")
            print(f"  - Weaknesses: {len(assessment.get('weaknesses', []))} items")
            if assessment.get('weaknesses'):
                print(f"    Example: {assessment['weaknesses'][0]}")
            print(f"  - Missing Elements: {len(assessment.get('missing_elements', []))} items")
            if assessment.get('missing_elements'):
                print(f"    Example: {assessment['missing_elements'][0]}")
            print(f"  - Improvement Suggestions: {len(assessment.get('improvement_suggestions', []))} items")
            if assessment.get('improvement_suggestions'):
                print(f"    Example: {assessment['improvement_suggestions'][0]}")
        else:
            print("\n[WARNING] Educational report data missing")
            
        # Show a snippet of the optimized vision
        if 'optimized_vision' in data:
            print(f"\nOptimized Vision Preview:")
            print(data['optimized_vision'][:200] + "...")
            
    else:
        print("\n[ERROR] Optimization failed")
        print(f"Error response: {response.text[:500]}")
        
except Exception as e:
    print(f"\n[ERROR] Request failed with exception: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Clean up - restore original config if needed
    conn.close()