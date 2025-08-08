#!/usr/bin/env python3
"""
Emergency database fix to correct the OpenAI configuration.
"""

import sqlite3

# Connect to the correct database
conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

print("=== EMERGENCY DATABASE FIX ===")
print("Fixing incorrect OpenAI configuration...\n")

# First, deactivate all configurations for the user
cursor.execute("""
    UPDATE llm_configurations 
    SET is_default = 0, is_active = 0 
    WHERE user_id = 'user_d918da6e'
""")
print(f"Deactivated all configurations")

# Check if we already have a correct gpt-5-mini configuration
cursor.execute("""
    SELECT id FROM llm_configurations 
    WHERE user_id = 'user_d918da6e' 
    AND provider = 'openai' 
    AND model = 'gpt-5-mini'
""")
existing = cursor.fetchone()

if existing:
    # Update existing configuration
    config_id = existing[0]
    cursor.execute("""
        UPDATE llm_configurations 
        SET is_default = 1, is_active = 1, name = 'OpenAI GPT-5-mini'
        WHERE id = ?
    """, (config_id,))
    print(f"Updated existing gpt-5-mini configuration (id={config_id})")
else:
    # Create new configuration
    cursor.execute("""
        INSERT INTO llm_configurations 
        (user_id, name, provider, model, api_key, base_url, preset, is_default, is_active, created_at, updated_at)
        VALUES 
        ('user_d918da6e', 'OpenAI GPT-5-mini', 'openai', 'gpt-5-mini', '', 
         'https://api.openai.com/v1/chat/completions', NULL, 1, 1, 
         datetime('now'), datetime('now'))
    """)
    print("Created new gpt-5-mini configuration")

# Delete the bad configuration
cursor.execute("""
    DELETE FROM llm_configurations 
    WHERE user_id = 'user_d918da6e' 
    AND provider = 'openai' 
    AND model = 'qwen2.5:14b-instruct-q4_K_M'
""")
print("Deleted incorrect OpenAI/qwen configuration")

# Commit changes
conn.commit()

# Verify the fix
print("\n=== VERIFICATION ===")
cursor.execute("""
    SELECT name, provider, model, is_default, is_active 
    FROM llm_configurations 
    WHERE user_id = 'user_d918da6e' 
    AND is_active = 1
""")
active = cursor.fetchone()
if active:
    print(f"Active configuration: {active[0]}")
    print(f"  Provider: {active[1]}")
    print(f"  Model: {active[2]}")
    print(f"  Is Default: {active[3]}")
    print(f"  Is Active: {active[4]}")
else:
    print("ERROR: No active configuration found!")

conn.close()

print("\n=== FIX COMPLETE ===")
print("Please restart the backend server for changes to take effect.")