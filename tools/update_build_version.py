#!/usr/bin/env python3
"""
Build Version Update Script

Updates the build version in the database with format: YYYY.MM.DD.BUILD
- Increments build number for same day
- Resets to 001 for new day
- Can be called manually or from git hooks

Usage:
    python tools/update_build_version.py [--commit-message "message"]
"""

import sys
import os
import argparse
from datetime import datetime

# Add the parent directory to Python path to import db
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db

def update_build_version(commit_message: str = None) -> str:
    """Update build version and return new version."""
    try:
        # Get current build version
        old_version = db.get_build_version()
        
        # Increment to new version
        new_version = db.increment_build_version()
        
        print(f"[BUILD] Build version updated: {old_version} -> {new_version}")
        
        if commit_message:
            print(f"[COMMIT] {commit_message[:80]}...")
        
        return new_version
        
    except Exception as e:
        print(f"[ERROR] Failed to update build version: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Update build version in database')
    parser.add_argument('--commit-message', '-m', 
                       help='Commit message that triggered this update')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress output except errors')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("[INFO] Updating build version...")
    
    new_version = update_build_version(args.commit_message)
    
    if new_version:
        if not args.quiet:
            print(f"[SUCCESS] Build version is now: {new_version}")
        sys.exit(0)
    else:
        print("[ERROR] Failed to update build version")
        sys.exit(1)

if __name__ == "__main__":
    main()