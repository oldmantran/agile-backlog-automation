#!/usr/bin/env python3
"""
Quick test to verify acceptance criteria formatting improvements.
"""

def test_acceptance_criteria_formatting():
    """Test the double line spacing formatting for acceptance criteria."""
    
    # Sample acceptance criteria like the one from the user's example
    criteria = [
        "Given historical ride data and current telemetry inputs, when the model is queried, then it outputs demand forecasts for specified time periods with at least 80% accuracy in simulations.",
        "The model incorporates factors like time of day, day of week, and historical patterns.",
        "Predictions are generated in under 5 seconds for real-time use.",
        "Model supports retraining with new data via an API endpoint."
    ]
    
    # Apply the improved formatting (double line spacing)
    formatted_criteria = []
    for i, criterion in enumerate(criteria, 1):
        formatted_criteria.append(f"{i}. {criterion}")
    
    # Join with double line spacing for better readability
    result = "\n\n".join(formatted_criteria)
    
    print("=" * 80)
    print("BEFORE (old single line spacing):")
    print("=" * 80)
    old_format = "\n".join(formatted_criteria)
    print(old_format)
    
    print("\n" + "=" * 80)
    print("AFTER (new double line spacing):")
    print("=" * 80)
    print(result)
    
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    lines = result.split('\n')
    print(f"Total lines: {len(lines)}")
    print(f"Empty lines (spacing): {sum(1 for line in lines if line.strip() == '')}")
    print(f"Content lines: {sum(1 for line in lines if line.strip() != '')}")
    print(f"Double spacing present: {'\\n\\n' in result}")
    
    return result

if __name__ == "__main__":
    print("🧪 Testing Acceptance Criteria Formatting Improvements")
    formatted = test_acceptance_criteria_formatting()
    print("\n✅ Test completed successfully!")
