from pydantic import BaseModel, validator
from typing import List, Dict

class VisionOptimizationRequest(BaseModel):
    original_vision: str
    domains: List[Dict[str, str]]
    
    @validator('original_vision')
    def vision_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Vision statement is required')
        return v

# Test with empty string
try:
    test1 = VisionOptimizationRequest(original_vision="", domains=[])
    print("Empty string passed validation")
except Exception as e:
    print(f"Empty string failed: {e}")

# Test with whitespace
try:
    test2 = VisionOptimizationRequest(original_vision="   ", domains=[])
    print("Whitespace passed validation")
except Exception as e:
    print(f"Whitespace failed: {e}")

# Test with valid data
try:
    test3 = VisionOptimizationRequest(
        original_vision="Test vision", 
        domains=[{"domain": "retail", "priority": "primary"}]
    )
    print(f"Valid data passed: {test3}")
except Exception as e:
    print(f"Valid data failed: {e}")