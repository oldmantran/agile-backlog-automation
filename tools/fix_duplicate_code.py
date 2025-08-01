#!/usr/bin/env python3
"""
Fix duplicate code in unified_api_server.py
"""

import os
import shutil

def fix_duplicate_code():
    """Remove duplicate run_backlog_generation function."""
    
    api_server_path = "unified_api_server.py"
    backup_path = "unified_api_server.py.backup"
    
    # Create backup
    shutil.copy2(api_server_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    with open(api_server_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the duplicate function (starts at line 1227, ends at 1503)
    # The function async def run_backlog_generation is a duplicate of run_backlog_generation_sync
    
    # Remove lines 1227-1503 (0-indexed: 1226-1502)
    start_line = 1226  # Line 1227 in 1-indexed
    end_line = 1503    # Line 1503 in 1-indexed
    
    print(f"Removing duplicate code from lines {start_line+1} to {end_line}")
    
    # Keep everything before the duplicate and after the duplicate
    new_lines = lines[:start_line] + lines[end_line:]
    
    # Write the fixed file
    with open(api_server_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Removed {end_line - start_line} lines of duplicate code")
    print(f"Original file size: {len(lines)} lines")
    print(f"New file size: {len(new_lines)} lines")
    
    return True

if __name__ == "__main__":
    try:
        success = fix_duplicate_code()
        if success:
            print("✅ Duplicate code removal completed successfully")
        else:
            print("❌ Failed to remove duplicate code")
    except Exception as e:
        print(f"❌ Error: {e}")