#!/usr/bin/env python3
"""
Test the exact string you provided to debug the regex issue.
"""

import re

def test_exact_string():
    # Your exact example
    test_string = "in real-time and take preventive actions. **Acceptance Criteria:** - Dashboard loads in under 3 seconds"
    
    print("Original string:")
    print(repr(test_string))
    print()
    
    # Test Pattern 1: sentence. **Section**: -> sentence.\n\n**Section**:
    pattern1 = r'([a-z]\.)\s(\*\*[^*]+\*\*:)'  # Changed \s+ to \s (exactly one space)
    
    print("Testing Pattern 1:")
    print(f"Pattern: {pattern1}")
    
    match = re.search(pattern1, test_string)
    if match:
        print(f"✅ MATCH found!")
        print(f"Group 1: {repr(match.group(1))}")
        print(f"Group 2: {repr(match.group(2))}")
        
        # Apply the substitution
        fixed = re.sub(pattern1, r'\1\n\n\2', test_string)
        print(f"\nAfter substitution:")
        print(repr(fixed))
        print("\nFormatted:")
        print(fixed)
    else:
        print("❌ No match found with single space")
        
        # Try a more specific pattern
        pattern1_alt = r'([a-z]\.)\s(\*\*[A-Za-z\s]+\*\*:)'
        print(f"\nTrying alternative pattern: {pattern1_alt}")
        
        match = re.search(pattern1_alt, test_string)
        if match:
            print(f"✅ ALTERNATIVE MATCH found!")
            print(f"Group 1: {repr(match.group(1))}")
            print(f"Group 2: {repr(match.group(2))}")
            
            # Apply the substitution
            fixed = re.sub(pattern1_alt, r'\1\n\n\2', test_string)
            print(f"\nAfter substitution:")
            print(repr(fixed))
            print("\nFormatted:")
            print(fixed)
        else:
            print("❌ Alternative pattern also failed")
        
        # Let's debug character by character around the critical area
        print("\nDebugging around 'actions. **Acceptance':")
        start_idx = test_string.find('actions.')
        if start_idx >= 0:
            debug_section = test_string[start_idx:start_idx+30]
            print(f"Debug section: {repr(debug_section)}")
            
            # Check each character
            for i, char in enumerate(debug_section):
                print(f"  {i}: {repr(char)} ({ord(char)})")

if __name__ == "__main__":
    test_exact_string()
