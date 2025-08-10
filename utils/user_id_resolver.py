#!/usr/bin/env python3
"""
User ID Resolver - Handles user identification in the absence of authentication.
"""

import os
import hashlib
from typing import Optional
from config.config_loader import Config

class UserIdResolver:
    """Resolves user IDs from environment variables and provides consistent user identification."""
    
    def __init__(self):
        self.config = Config()
        self._default_user_id = None
    
    def get_default_user_id(self) -> str:
        """Get the default user ID from environment variables.
        
        This should only be used for background processes or legacy code.
        For request handlers, use the authenticated user from JWT instead.
        """
        if self._default_user_id is None:
            # Try to get from EMAIL_TO first
            email = self.config.get_env('EMAIL_TO')
            if email:
                self._default_user_id = self._normalize_email(email)
            else:
                # Fallback to EMAIL_FROM
                email = self.config.get_env('EMAIL_FROM')
                if email:
                    self._default_user_id = self._normalize_email(email)
                else:
                    # Raise error instead of fallback
                    raise ValueError("No user ID could be determined from environment variables (EMAIL_TO or EMAIL_FROM)")
        
        return self._default_user_id
    
    def _normalize_email(self, email: str) -> str:
        """Normalize email to a consistent user ID format."""
        if not email:
            raise ValueError("Cannot normalize empty email address")
        
        # Remove any whitespace and convert to lowercase
        email = email.strip().lower()
        
        # Create a hash of the email for consistency
        email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
        
        # Return a user-friendly ID
        return f"user_{email_hash}"
    
    def get_user_email(self) -> Optional[str]:
        """Get the user's email address."""
        return self.config.get_env('EMAIL_TO') or self.config.get_env('EMAIL_FROM')
    
    def get_user_display_name(self) -> str:
        """Get a display name for the user."""
        email = self.get_user_email()
        if email:
            # Extract name from email (e.g., "kevin.tran@c4workx.com" -> "kevin.tran")
            name = email.split('@')[0]
            return name.replace('.', ' ').title()
        raise ValueError("No user email available to generate display name")
    
    def is_valid_user_id(self, user_id: str) -> bool:
        """Check if a user ID is valid."""
        if not user_id:
            return False
        
        # For now, accept any non-empty string
        # In the future, this could validate against a user database
        return len(user_id.strip()) > 0
    
    def get_session_id(self, user_id: str) -> str:
        """Generate a session ID for a user."""
        import time
        timestamp = int(time.time())
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:6]
        return f"session_{user_hash}_{timestamp}"

# Global instance
user_id_resolver = UserIdResolver() 