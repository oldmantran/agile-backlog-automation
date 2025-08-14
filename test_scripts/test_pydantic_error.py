#!/usr/bin/env python3
"""Test what error Pydantic gives for missing fields"""

from pydantic import BaseModel, ValidationError
from typing import List, Dict

class VisionOptimizationRequest(BaseModel):
    original_vision: str
    domains: List[Dict[str, str]]

# Test with empty dict
print("1. Testing with empty dict:")
try:
    request = VisionOptimizationRequest(**{})
except ValidationError as e:
    print(f"Error: {e}")
    for error in e.errors():
        print(f"  - Field: {error['loc']}, Type: {error['type']}, Message: {error['msg']}")

# Test with None values
print("\n2. Testing with None values:")
try:
    request = VisionOptimizationRequest(original_vision=None, domains=None)
except ValidationError as e:
    print(f"Error: {e}")
    
# Test with empty string
print("\n3. Testing with empty string:")
try:
    request = VisionOptimizationRequest(original_vision="", domains=[])
    print("Success! Empty string is valid")
except ValidationError as e:
    print(f"Error: {e}")