#!/usr/bin/env python3
"""
Quick test to debug the markdown parsing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.qa_tester_agent import QATesterAgent
from config.config_loader import Config

# Sample markdown response from AI - more realistic format
sample_markdown = """
### **Test Case 1: Display Validation Status for Received Well Data**

**Objective:** Verify that the dashboard displays real-time validation status when well data is received and validation rules are applied.

- **Preconditions:** Well data is received by the system.
- **Test Steps:**
    1. Submit a valid data feed for a well to the system.
    2. Wait for the system to apply predefined validation rules.
    3. Access the Well Data Validation Dashboard as a field engineer.
- **Expected Results:** 
    - Dashboard displays the validation status for the newly received well data in real time.
    - Validation statuses are clear (e.g., Valid, Invalid, Warning).

---

### **Test Case 2: Highlight Specific Errors for Invalid Data**

**Objective:** Confirm that, when invalid data is detected, the dashboard highlights specific errors.

- **Preconditions:** Well data containing intentional errors is received.
- **Test Steps:**
    1. Submit well data with known, intentional validation errors.
    2. Access the Well Data Validation Dashboard.
    3. Observe the display for error highlighting.
- **Expected Results:** 
    - Invalid data records are clearly highlighted.
    - Specific errors are displayed next to the affected data.

---

### **Test Case 3: Generate Validation Summary Report**

**Objective:** Verify that a summary report is generated post-validation upon engineer's request.

- **Preconditions:** Validation process is complete for a set of well data.
- **Test Steps:**
    1. Complete a validation run for received well data.
    2. As a field engineer, request a summary report from the dashboard.
    3. Download or view the generated summary report.
- **Expected Results:** 
    - A report is generated that summarizes validation status.
    - Report is complete, correctly formatted, and reflects the latest validation results.
"""

def test_parsing():
    try:
        config = Config(settings_path="../config/settings.yaml")
        qa_agent = QATesterAgent(config)
        
        print("Testing JSON extraction...")
        result = qa_agent._extract_json_from_response(sample_markdown)
        print(f"Result: {result[:200]}...")
        
        import json
        try:
            parsed = json.loads(result)
            print(f"✅ Successfully parsed {len(parsed)} test cases")
            for i, tc in enumerate(parsed):
                print(f"  {i+1}. {tc.get('title', 'No title')}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parsing()
