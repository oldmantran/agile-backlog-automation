#!/usr/bin/env python3
import re

def test_all_section_headers():
    # Test with multiple section headers found in the system
    test_string = """Enable bidirectional data synchronization between GRIT and enterprise ERP systems to ensure real-time inventory and order data consistency. This feature reduces manual data entry and minimizes discrepancies between systems, providing Logistics Managers with accurate data for decision-making. **Business Value:** This will increase efficiency by 25% and reduce errors. **Success Criteria:** - All data syncs without loss. - Performance meets targets. **Dependencies:** - Database migration completed. - API endpoints available. **Risks:** - Third-party integration delays. **Technical Requirements:** - Use secure API connections. - Implement error handling. **Definition of Done:** - Code review completed. - Tests passing."""
    
    print("Testing all section headers...")
    print(f"Original formatted:\n{test_string}")
    print()
    
    # Start with the original description
    fixed_description = test_string
    
    # Step 1: Handle any remaining escaped newlines
    fixed_description = fixed_description.replace('\\n', '\n')
    
    # Step 2: Add two line breaks before any **Section Headers**
    # This regex should catch ALL section headers like **Business Value:**, **Success Criteria:**, etc.
    fixed_description = re.sub(
        r'([a-zA-Z0-9.,;:!?])\s*(\*\*[^*]+\*\*:?)',
        r'\1\n\n\2',
        fixed_description
    )
    
    print("After adding breaks before **Section Headers**:")
    print(f"Formatted:\n{fixed_description}")
    print()
    
    # Step 3: Add one line break before bullet points
    # Find any text followed immediately by "- " and add proper spacing
    fixed_description = re.sub(
        r'([a-zA-Z0-9.,;:!?\*])\s*(-\s)',
        r'\1\n\2',
        fixed_description
    )
    
    print("After adding breaks before bullet points:")
    print(f"Formatted:\n{fixed_description}")
    print()
    
    # Step 4: Clean up any excessive newlines (more than 2 consecutive)
    fixed_description = re.sub(r'\n{3,}', '\n\n', fixed_description)
    
    print("After cleanup:")
    print(f"Formatted:\n{fixed_description}")
    print()
    
    # List all the section headers we should find
    expected_headers = [
        "**Business Value:**",
        "**Success Criteria:**", 
        "**Dependencies:**",
        "**Risks:**",
        "**Technical Requirements:**",
        "**Definition of Done:**"
    ]
    
    print("Checking that all section headers are properly formatted:")
    for header in expected_headers:
        if f"\n\n{header}" in fixed_description:
            print(f"✅ {header} - properly formatted with double line break")
        elif header in fixed_description:
            print(f"⚠️ {header} - found but may need formatting")
        else:
            print(f"❌ {header} - not found")

if __name__ == "__main__":
    test_all_section_headers()
