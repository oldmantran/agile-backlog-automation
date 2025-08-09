"""
Authentication module for JWT + Local Users system.
"""

from .user_auth import UserAuthManager, auth_manager
from .auth_routes import router as auth_router

__all__ = ['UserAuthManager', 'auth_manager', 'auth_router']