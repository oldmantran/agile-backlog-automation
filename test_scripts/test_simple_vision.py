#!/usr/bin/env python3
"""Simple test to check if the issue is with Pydantic validation"""

from pydantic import BaseModel
from typing import List, Dict

class VisionOptimizationRequest(BaseModel):
    original_vision: str
    domains: List[Dict[str, str]]

# Test data
test_data = {
    "original_vision": "Test vision",
    "domains": [{"domain": "education", "priority": "primary"}]
}

# Try to create the model
try:
    request = VisionOptimizationRequest(**test_data)
    print(f"[OK] Model created successfully")
    print(f"  - original_vision: {request.original_vision}")
    print(f"  - domains: {request.domains}")
except Exception as e:
    print(f"[ERROR] Model validation failed: {e}")