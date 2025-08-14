#!/usr/bin/env python3
"""Test optimization timing and response size"""

import requests
import json
import time

# Login first
login_url = "http://localhost:8000/api/auth/login"
login_data = {"username": "testuser", "password": "Test123!"}

print("Getting auth token...")
login_response = requests.post(login_url, json=login_data)
token = login_response.json()["data"]["tokens"]["access_token"]

# Test optimization with timing
optimize_url = "http://localhost:8000/api/vision/optimize"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

test_data = {
    "original_vision": "Simple test vision for a product",
    "domains": [{"domain": "technology", "priority": "primary"}]
}

print("\nTesting optimization with timing...")
start_time = time.time()

try:
    # Test with different timeouts
    response = requests.post(optimize_url, json=test_data, headers=headers, timeout=120)
    end_time = time.time()
    
    print(f"Status: {response.status_code}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    print(f"Response size: {len(response.text)} bytes")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nResponse structure:")
        print(f"- Top level keys: {list(data.keys())}")
        if 'data' in data:
            print(f"- Data keys: {list(data['data'].keys())}")
            print(f"- Optimized vision length: {len(data['data'].get('optimized_vision', ''))}")
            
except requests.exceptions.Timeout:
    end_time = time.time()
    print(f"[TIMEOUT] Request timed out after {end_time - start_time:.2f} seconds")
    
except requests.exceptions.RequestException as e:
    end_time = time.time()
    print(f"[ERROR] Request failed after {end_time - start_time:.2f} seconds: {e}")
    
except Exception as e:
    end_time = time.time()
    print(f"[ERROR] Unexpected error after {end_time - start_time:.2f} seconds: {e}")