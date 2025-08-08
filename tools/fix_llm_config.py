#!/usr/bin/env python3
"""
Emergency fix for LLM configuration in database.
Ensures OpenAI provider uses gpt-5-mini model.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_llm_config():
    """Fix the LLM configuration in the database."""
    db = Database()
    
    # Get all users
    users = db.get_all_users()
    if not users:
        logger.info("No users found in database")
        # Create default user
        db.create_user(
            user_id="default_user",
            email="default@example.com",
            name="Default User"
        )
        users = [{"user_id": "default_user"}]
    
    for user in users:
        user_id = user['user_id']
        logger.info(f"\nChecking configurations for user: {user_id}")
        
        # Get all LLM configurations
        configs = db.get_all_llm_configurations(user_id)
        
        if not configs:
            logger.info("No configurations found, creating defaults")
            db.create_default_llm_configurations(user_id)
            configs = db.get_all_llm_configurations(user_id)
        
        # Fix any OpenAI configurations
        for config in configs:
            if config['provider'] == 'openai':
                logger.info(f"Found OpenAI config: {config['name']} with model: {config['model']}")
                
                if config['model'] != 'gpt-5-mini':
                    logger.info(f"FIXING: Updating model from {config['model']} to gpt-5-mini")
                    db.save_llm_configuration(
                        user_id=user_id,
                        name="OpenAI GPT-5-mini",
                        provider="openai",
                        model="gpt-5-mini",
                        api_key=config.get('api_key', ''),
                        is_default=True,
                        is_active=True
                    )
                
                # Make sure it's the active configuration
                if not config.get('is_active'):
                    logger.info("FIXING: Making OpenAI config active")
                    db.set_active_llm_configuration(user_id, config['config_id'])
        
        # Verify the active configuration
        active_config = db.get_active_llm_configuration(user_id)
        if active_config:
            logger.info(f"\nActive configuration for {user_id}:")
            logger.info(f"  Provider: {active_config['provider']}")
            logger.info(f"  Model: {active_config['model']}")
            logger.info(f"  Name: {active_config['name']}")
            
            if active_config['provider'] != 'openai' or active_config['model'] != 'gpt-5-mini':
                logger.warning("Active configuration is NOT OpenAI gpt-5-mini!")
                
                # Find or create OpenAI config and make it active
                openai_config = None
                for config in configs:
                    if config['provider'] == 'openai':
                        openai_config = config
                        break
                
                if openai_config:
                    logger.info("FIXING: Setting OpenAI config as active")
                    db.set_active_llm_configuration(user_id, openai_config['config_id'])
                else:
                    logger.info("FIXING: Creating new OpenAI config")
                    db.save_llm_configuration(
                        user_id=user_id,
                        name="OpenAI GPT-5-mini",
                        provider="openai",
                        model="gpt-5-mini",
                        api_key='',
                        is_default=True,
                        is_active=True
                    )
        else:
            logger.warning("No active configuration found!")

if __name__ == "__main__":
    print("=== LLM Configuration Fix Tool ===")
    print("This will ensure OpenAI gpt-5-mini is properly configured\n")
    
    fix_llm_config()
    
    print("\n=== Configuration fixed! ===")
    print("Please restart the backend server for changes to take effect.")