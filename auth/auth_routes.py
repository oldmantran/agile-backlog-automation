#!/usr/bin/env python3
"""
Authentication API Routes for FastAPI

Provides secure login/register/logout endpoints with JWT authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from auth.user_auth import (
    UserAuthManager, UserCreate, UserLogin, User, TokenData,
    auth_manager
)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# HTTP Bearer token scheme
security = HTTPBearer()

logger = logging.getLogger(__name__)


class AuthResponse:
    """Standardized authentication response format."""
    
    @staticmethod
    def success(data=None, message="Success"):
        return {"success": True, "message": message, "data": data}
    
    @staticmethod
    def error(message="Authentication failed", status_code=401):
        return HTTPException(
            status_code=status_code,
            detail={"success": False, "message": message}
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user from JWT token."""
    
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    if payload is None:
        raise AuthResponse.error("Invalid or expired token")
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise AuthResponse.error("Invalid token payload")
    
    user = auth_manager.get_user_by_id(user_id)
    if user is None:
        raise AuthResponse.error("User not found")
    
    return user


@router.post("/register", response_model=dict)
async def register_user(user_data: UserCreate):
    """Register a new user account."""
    try:
        # Create the user
        user = auth_manager.register_user(user_data)
        
        # Create authentication tokens
        tokens = auth_manager.create_tokens(user)
        
        # Return success response with user data and tokens
        response_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat()
            },
            "tokens": {
                "access_token": tokens.access_token,
                "token_type": tokens.token_type,
                "expires_in": tokens.expires_in
            }
        }
        
        # Create response with refresh token in httpOnly cookie
        response = JSONResponse(
            content=AuthResponse.success(response_data, "User registered successfully")
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,  # Use HTTPS in production
            samesite="lax"
        )
        
        logger.info(f"User registered and authenticated: {user.username}")
        return response
        
    except ValueError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise AuthResponse.error(str(e), status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise AuthResponse.error("Registration failed", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/login", response_model=dict)
async def login_user(login_data: UserLogin):
    """Authenticate user and return JWT tokens."""
    try:
        # Authenticate user
        user = auth_manager.authenticate_user(login_data.username, login_data.password)
        if user is None:
            logger.warning(f"Failed login attempt for username: {login_data.username}")
            raise AuthResponse.error("Invalid username or password")
        
        # Create authentication tokens
        tokens = auth_manager.create_tokens(user)
        
        # Return success response with user data and access token
        response_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat()
            },
            "tokens": {
                "access_token": tokens.access_token,
                "token_type": tokens.token_type,
                "expires_in": tokens.expires_in
            }
        }
        
        # Create response with refresh token in httpOnly cookie
        response = JSONResponse(
            content=AuthResponse.success(response_data, "Login successful")
        )
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=True,  # Use HTTPS in production
            samesite="lax"
        )
        
        logger.info(f"User authenticated successfully: {user.username}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise AuthResponse.error("Login failed", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: Optional[str] = Cookie(None)):
    """Refresh access token using refresh token."""
    if refresh_token is None:
        raise AuthResponse.error("Refresh token required")
    
    try:
        # Create new access token
        tokens = auth_manager.refresh_access_token(refresh_token)
        if tokens is None:
            raise AuthResponse.error("Invalid or expired refresh token")
        
        response_data = {
            "tokens": {
                "access_token": tokens.access_token,
                "token_type": tokens.token_type,
                "expires_in": tokens.expires_in
            }
        }
        
        logger.info("Access token refreshed successfully")
        return AuthResponse.success(response_data, "Token refreshed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise AuthResponse.error("Token refresh failed", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/logout", response_model=dict)
async def logout_user(refresh_token: Optional[str] = Cookie(None)):
    """Logout user by invalidating refresh token."""
    if refresh_token is None:
        raise AuthResponse.error("No active session found", status.HTTP_400_BAD_REQUEST)
    
    try:
        # Invalidate refresh token
        success = auth_manager.logout_user(refresh_token)
        
        # Create response
        response = JSONResponse(
            content=AuthResponse.success(message="Logged out successfully")
        )
        
        # Clear refresh token cookie
        response.delete_cookie(key="refresh_token", httponly=True)
        
        if success:
            logger.info("User logged out successfully")
        else:
            logger.warning("Logout attempted with invalid refresh token")
        
        return response
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise AuthResponse.error("Logout failed", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    try:
        user_data = {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat()
        }
        
        return AuthResponse.success(user_data, "User information retrieved")
        
    except Exception as e:
        logger.error(f"Get user info error: {str(e)}")
        raise AuthResponse.error("Failed to get user information", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/verify", response_model=dict)
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """Verify if the current token is valid."""
    try:
        return AuthResponse.success(
            {"valid": True, "username": current_user.username},
            "Token is valid"
        )
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise AuthResponse.error("Token verification failed")


@router.post("/cleanup-sessions", response_model=dict)
async def cleanup_expired_sessions():
    """Clean up expired refresh token sessions (admin endpoint)."""
    try:
        auth_manager.cleanup_expired_sessions()
        return AuthResponse.success(message="Expired sessions cleaned up")
    except Exception as e:
        logger.error(f"Session cleanup error: {str(e)}")
        raise AuthResponse.error("Session cleanup failed", status.HTTP_500_INTERNAL_SERVER_ERROR)


# Optional: Protected route dependency for easier use
async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Simplified dependency for protected routes."""
    return current_user