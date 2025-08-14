#!/usr/bin/env python3
"""Test with raw request to see the exact error"""

import requests
import json

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

# Test the test endpoint first
test_url = "http://localhost:8000/api/vision/optimize-test"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

test_data = {
    "original_vision": "Test vision",
    "domains": [{"domain": "education", "priority": "primary"}]
}

print("\n2. Testing test endpoint...")
try:
    response = requests.post(test_url, json=test_data, headers=headers)
    print(f"Test endpoint status: {response.status_code}")
    print(f"Test endpoint response: {response.text}")
except Exception as e:
    print(f"Test endpoint failed: {e}")

# Now test the actual endpoint with various data formats
print("\n3. Testing actual endpoint with dict data...")
try:
    response = requests.post("http://localhost:8000/api/vision/optimize", json=test_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    print(f"Headers: {dict(response.headers)}")
except Exception as e:
    print(f"Failed: {e}")

# Test with empty data
print("\n4. Testing with empty data...")
try:
    response = requests.post("http://localhost:8000/api/vision/optimize", json={}, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Failed: {e}")

# Test with missing fields
print("\n5. Testing with missing domains...")
try:
    response = requests.post("http://localhost:8000/api/vision/optimize", 
                           json={"original_vision": "test"}, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Failed: {e}")