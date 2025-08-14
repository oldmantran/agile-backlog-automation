#!/usr/bin/env python3
"""Setup proper LLM configuration for vision optimizer agent"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# First check if we have any configurations
cursor.execute("SELECT * FROM llm_configurations WHERE user_id = '2'")
configs = cursor.fetchall()
print(f"Found {len(configs)} existing configurations")

# Insert or update configuration for vision_optimizer_agent
cursor.execute("""
    INSERT OR REPLACE INTO llm_configurations 
    (user_id, name, agent_name, provider, model, preset, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    '2',  # user_id for testuser
    'Vision Optimizer Config',
    'vision_optimizer_agent',
    'openai',
    'gpt-4o-mini',
    'balanced',
    1,
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

conn.commit()
print("Inserted/updated vision_optimizer_agent configuration")

# Verify it was saved
cursor.execute("""
    SELECT * FROM llm_configurations 
    WHERE user_id = '2' AND agent_name = 'vision_optimizer_agent' AND is_active = 1
""")
result = cursor.fetchone()
print(f"Verified configuration: {result}")

conn.close()