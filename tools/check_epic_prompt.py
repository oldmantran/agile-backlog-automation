#!/usr/bin/env python3
"""
Check what prompt is being sent to the LLM for epic generation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.prompt_manager import PromptManager
from utils.safe_logger import safe_print

def main():
    safe_print("[CHECK] Epic Strategist Prompt Analysis")
    safe_print("=" * 80)
    
    # Load the prompt
    pm = PromptManager()
    
    # Test context
    context = {
        'product_vision': "Warehouse Asset Survey application is an iPad-based platform...",
        'domain': 'logistics',
        'project_name': 'Backlog Automation',
        'target_users': 'managers',
        'timeline': '3-6 months',
        'budget_constraints': 'Moderate budget',
        'methodology': 'Agile/Scrum',
        'max_epics': 3
    }
    
    try:
        prompt = pm.get_prompt('epic_strategist', context)
        
        # Find key sections
        safe_print("\n[SECTIONS] Looking for key requirements in prompt:")
        
        # Check for product name requirement
        if "product/solution name" in prompt.lower():
            safe_print("✓ Found product name requirement")
        else:
            safe_print("✗ Missing product name requirement")
            
        # Check for target users requirement
        if "who will use it" in prompt.lower():
            safe_print("✓ Found target users requirement")
        else:
            safe_print("✗ Missing target users requirement")
            
        # Check for platform requirement
        if "platform/technology" in prompt.lower():
            safe_print("✓ Found platform requirement")
        else:
            safe_print("✗ Missing platform requirement")
            
        # Check for CRITICAL REQUIREMENT section
        if "CRITICAL REQUIREMENT" in prompt:
            safe_print("✓ Found CRITICAL REQUIREMENT section")
            # Extract and show it
            start = prompt.find("CRITICAL REQUIREMENT")
            end = prompt.find("###", start + 1)
            if end == -1:
                end = start + 500
            safe_print("\n[CRITICAL SECTION]")
            safe_print(prompt[start:end])
        else:
            safe_print("✗ Missing CRITICAL REQUIREMENT section")
            
        # Show first 1000 chars to verify
        safe_print("\n[PROMPT START] First 1000 characters:")
        safe_print(prompt[:1000])
        
    except Exception as e:
        safe_print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()