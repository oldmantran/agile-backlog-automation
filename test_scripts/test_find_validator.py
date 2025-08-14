#!/usr/bin/env python3
"""Search for the source of 'Vision statement is required' error"""

import os
import re

def search_in_file(filepath, pattern):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if pattern in content.lower():
                # Find the line number
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if pattern in line.lower():
                        return f"Found in {filepath} at line {i+1}: {line.strip()}"
    except:
        pass
    return None

# Search pattern
pattern = "vision statement is required"

# Search in Python files
for root, dirs, files in os.walk("X:\\Programs\\agile-backlog-automation"):
    # Skip venv directory
    if 'venv' in root:
        continue
    
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            result = search_in_file(filepath, pattern)
            if result:
                print(result)