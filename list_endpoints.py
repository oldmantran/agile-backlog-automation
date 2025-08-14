#!/usr/bin/env python3
"""List all vision optimize endpoints in the API"""

import re

with open("unified_api_server.py", "r", encoding="utf-8") as f:
    content = f.read()
    
# Find all vision/optimize endpoints
pattern = r'@app\.post\("([^"]*vision/optimize[^"]*)"\)'
matches = re.findall(pattern, content)

print("Found vision/optimize endpoints:")
for i, match in enumerate(matches, 1):
    print(f"{i}. {match}")
    
# Also find the line numbers
lines = content.split('\n')
for i, line in enumerate(lines):
    if '@app.post' in line and 'vision/optimize' in line:
        print(f"\nLine {i+1}: {line.strip()}")