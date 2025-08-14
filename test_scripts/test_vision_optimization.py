#!/usr/bin/env python3
"""Test the vision optimization endpoint"""

import requests
import json

# First, we need to login to get a token
login_url = "http://localhost:8000/api/auth/login"
login_data = {
    "username": "testuser",
    "password": "Test123!"
}

print("1. Attempting login...")
login_response = requests.post(login_url, json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

response_data = login_response.json()
print(f"Login response: {response_data}")
token = response_data.get("data", {}).get("tokens", {}).get("access_token") or response_data.get("access_token")
if not token:
    print("Could not find access token in response")
    exit(1)
print(f"[OK] Login successful, got token: {token[:20]}...")

# Now test the vision optimization endpoint
optimize_url = "http://localhost:8000/api/vision/optimize"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

test_data = {
    "original_vision": "We want to build a mobile app for ordering food from local restaurants with delivery tracking.",
    "domains": [
        {"domain": "retail", "priority": "primary"},
        {"domain": "logistics", "priority": "secondary"}
    ]
}

print("\n2. Testing vision optimization...")
print(f"Request data: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(optimize_url, json=test_data, headers=headers)
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n[OK] Vision optimization successful!")
        print(f"\nOriginal Score: {result['data']['original_score']}")
        print(f"Optimized Score: {result['data']['optimized_score']}")
        print(f"Improvement: +{result['data']['score_improvement']}")
        print(f"\nOptimized Vision Preview (first 200 chars):")
        print(result['data']['optimized_vision'][:200] + "...")
    else:
        print(f"\n[ERROR] Vision optimization failed!")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"\n[ERROR] Request failed with exception: {e}")