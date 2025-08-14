#!/usr/bin/env python3
"""Test async optimization flow"""

import requests
import json
import time

# Login first
login_url = "http://localhost:8000/api/auth/login"
login_data = {"username": "testuser", "password": "Test123!"}

print("Getting auth token...")
login_response = requests.post(login_url, json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["data"]["tokens"]["access_token"]
print(f"Got token: {token[:30]}...")

# Test async optimization
optimize_url = "http://localhost:8000/api/vision/optimize/async"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

test_data = {
    "original_vision": "A simple test vision for a technology product that helps users manage their daily tasks",
    "domains": [{"domain": "technology", "priority": "primary"}]
}

print("\nStarting async optimization...")
response = requests.post(optimize_url, json=test_data, headers=headers)

if response.status_code != 200:
    print(f"Failed to start optimization: {response.status_code}")
    print(response.text)
    exit(1)

response_data = response.json()
print(f"Response: {json.dumps(response_data, indent=2)}")

if "data" in response_data:
    job_id = response_data["data"]["job_id"]
else:
    job_id = response_data["job_id"]
    
print(f"Got job ID: {job_id}")

# Poll for status
status_url = f"http://localhost:8000/api/vision/optimize/status/{job_id}"
max_attempts = 30  # 60 seconds max
attempt = 0

print("\nPolling for status...")
while attempt < max_attempts:
    time.sleep(2)  # Poll every 2 seconds
    
    status_response = requests.get(status_url, headers=headers)
    if status_response.status_code != 200:
        print(f"Status check failed: {status_response.status_code}")
        break
        
    status_response_data = status_response.json()
    if "data" in status_response_data:
        status_data = status_response_data["data"]
    else:
        status_data = status_response_data
        
    print(f"Attempt {attempt + 1}: Status = {status_data['status']}")
    
    if status_data['status'] == 'completed':
        print("\nOptimization completed!")
        print(f"Optimized vision ID: {status_data.get('optimized_vision_id')}")
        print(f"Quality score: {status_data.get('quality_score')}")
        print(f"Quality rating: {status_data.get('quality_rating')}")
        print(f"\nOptimized vision:")
        print(status_data.get('optimized_vision'))
        break
    elif status_data['status'] == 'failed':
        print(f"\nOptimization failed: {status_data.get('error_message')}")
        break
        
    attempt += 1
else:
    print("\nTimeout: Optimization took too long")