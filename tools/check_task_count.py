#!/usr/bin/env python3
"""
Quick script to check task count from recent process.
"""

import sqlite3
import os
import re
from datetime import datetime

def check_database():
    """Check the database for job information."""
    print("🔍 Checking database...")
    
    if not os.path.exists('backlog_jobs.db'):
        print("   ❌ Database file not found")
        return
    
    try:
        conn = sqlite3.connect('backlog_jobs.db')
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   📋 Available tables: {[table[0] for table in tables]}")
        
        # Try to find job information
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 3")
                rows = cursor.fetchall()
                if rows:
                    print(f"   📊 Table '{table_name}' has {len(rows)} recent entries")
                    for row in rows:
                        print(f"      {row}")
            except Exception as e:
                print(f"   ⚠️ Could not read table '{table_name}': {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")

def check_logs():
    """Check recent logs for task generation information."""
    print("\n📋 Checking recent logs...")
    
    log_files = [
        'logs/supervisor.log',
        'logs/supervisor_main.log'
    ]
    
    task_count = 0
    recent_activity = []
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"   📄 Reading: {log_file}")
            
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # Look for recent task-related activity
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    for line in recent_lines:
                        if 'task' in line.lower() or 'developer' in line.lower():
                            recent_activity.append(line.strip())
                            
                        # Look for task count patterns
                        if 'tasks_generated' in line or 'task.*generated' in line:
                            print(f"      🎯 Found task count info: {line.strip()}")
                            
                        # Look for completion stats
                        if 'stats' in line and 'tasks' in line:
                            print(f"      📊 Found stats: {line.strip()}")
                            
            except Exception as e:
                print(f"   ❌ Error reading {log_file}: {e}")
    
    print(f"\n   📈 Recent task-related activity ({len(recent_activity)} entries):")
    for activity in recent_activity[-10:]:  # Show last 10
        print(f"      {activity}")

def check_output_files():
    """Check output files for task information."""
    print("\n📁 Checking output files...")
    
    if os.path.exists('output'):
        output_files = [f for f in os.listdir('output') if f.endswith('.json') or f.endswith('.yaml')]
        output_files.sort(key=lambda x: os.path.getmtime(os.path.join('output', x)), reverse=True)
        
        print(f"   📂 Found {len(output_files)} output files")
        
        for file in output_files[:3]:  # Check 3 most recent
            file_path = os.path.join('output', file)
            print(f"   📄 Recent file: {file} (modified: {datetime.fromtimestamp(os.path.getmtime(file_path))})")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'task' in content.lower():
                        # Count task occurrences
                        task_matches = re.findall(r'task', content.lower())
                        print(f"      🎯 Contains {len(task_matches)} task references")
            except Exception as e:
                print(f"      ❌ Error reading file: {e}")

def main():
    """Main function to check task count."""
    print("🔍 Checking Task Count from Recent Process")
    print("=" * 50)
    
    check_database()
    check_logs()
    check_output_files()
    
    print("\n💡 To get exact task count:")
    print("   1. Check the completion notification in your logs")
    print("   2. Look for 'stats' or 'tasks_generated' in recent log entries")
    print("   3. Check the output files in the 'output' directory")
    print("   4. Monitor the current process completion")

if __name__ == "__main__":
    main() 