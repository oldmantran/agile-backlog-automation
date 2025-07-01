#!/usr/bin/env python3
"""
Debug the epic strategist output format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config.config_loader import Config
from agents.epic_strategist import EpicStrategist

def test_epic_output():
    """Test what the epic strategist actually outputs."""
    print("🔍 Debug Epic Strategist Output")
    print("=" * 40)
    
    try:
        # Initialize
        config = Config()
        agent = EpicStrategist(config)
        print("✅ EpicStrategist initialized")
        
        # Simple test vision
        vision = "Create a simple task management app for personal productivity."
        
        context = {
            "domain": "productivity software",
            "project_name": "Simple Task Manager",
            "methodology": "Agile/Scrum",
            "target_users": "individual users",
            "platform": "web application"
        }
        
        print(f"\\n📋 Test Vision: {vision}")
        print(f"\\n🔄 Calling Epic Strategist...")
        
        # Call the agent and capture raw response
        raw_response = agent.run(f"Product Vision: {vision}", context)
        
        print(f"\\n📄 Raw Response:")
        print("=" * 60)
        print(raw_response)
        print("=" * 60)
        
        print(f"\\n🔍 Analyzing Response:")
        print(f"  Length: {len(raw_response)}")
        print(f"  Type: {type(raw_response)}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(raw_response)
            print(f"  ✅ Valid JSON")
            print(f"  Parsed Type: {type(parsed)}")
            
            if isinstance(parsed, list):
                print(f"  📋 List with {len(parsed)} items")
                if parsed:
                    first_item = parsed[0]
                    print(f"  First item keys: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
            elif isinstance(parsed, dict):
                print(f"  📋 Dict with keys: {list(parsed.keys())}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON: {e}")
            
            # Check if it's wrapped in markdown code blocks
            if "```json" in raw_response:
                print("  🔍 Found markdown code blocks, extracting...")
                start = raw_response.find("```json") + 7
                end = raw_response.find("```", start)
                json_content = raw_response[start:end].strip()
                
                print(f"  Extracted JSON:")
                print(json_content)
                
                try:
                    parsed = json.loads(json_content)
                    print(f"  ✅ Valid JSON after extraction")
                    return parsed
                except json.JSONDecodeError as e:
                    print(f"  ❌ Still invalid JSON: {e}")
            
            return None
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    result = test_epic_output()
    
    if result:
        print(f"\\n🎉 Epic strategist output successfully parsed!")
    else:
        print(f"\\n❌ Epic strategist output needs fixing.")

if __name__ == "__main__":
    main()
