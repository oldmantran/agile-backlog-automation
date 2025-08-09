#!/usr/bin/env python3
"""
User Authentication System - JWT + Local Users

Provides secure authentication with bcrypt password hashing and JWT tokens.
Designed for local deployment with minimal external dependencies.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sqlite3
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
import re
from utils.safe_logger import get_safe_logger


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreate(BaseModel):
    """User registration model."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str


class User(BaseModel):
    """User model for API responses."""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


class TokenData(BaseModel):
    """JWT token data model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserAuthManager:
    """Handles user authentication, registration, and JWT token management."""
    
    def __init__(self, db_path: str = "agile_backlog.db"):
        self.db_path = db_path
        self.logger = get_safe_logger(__name__)
        self._create_tables()
    
    def _create_tables(self):
        """Create user authentication tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        full_name TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        refresh_token_hash TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)")
                
                conn.commit()
                self.logger.info("User authentication tables created successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to create user tables: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def _create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def _create_refresh_token(self, user_id: int) -> str:
        """Create and store a refresh token."""
        # Generate random refresh token
        refresh_token = secrets.token_urlsafe(32)
        refresh_token_hash = pwd_context.hash(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clean up old refresh tokens for this user
                conn.execute(
                    "DELETE FROM user_sessions WHERE user_id = ? OR expires_at < ?",
                    (user_id, datetime.utcnow())
                )
                
                # Store new refresh token
                conn.execute(
                    "INSERT INTO user_sessions (user_id, refresh_token_hash, expires_at) VALUES (?, ?, ?)",
                    (user_id, refresh_token_hash, expires_at)
                )
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store refresh token: {e}")
            raise
        
        return refresh_token
    
    def register_user(self, user_data: UserCreate) -> User:
        """Register a new user."""
        try:
            # Hash the password
            password_hash = self._hash_password(user_data.password)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Check if username or email already exists
                existing = conn.execute(
                    "SELECT username, email FROM users WHERE username = ? OR email = ?",
                    (user_data.username, user_data.email)
                ).fetchone()
                
                if existing:
                    if existing['username'] == user_data.username:
                        raise ValueError("Username already exists")
                    else:
                        raise ValueError("Email already exists")
                
                # Insert new user
                cursor = conn.execute(
                    """INSERT INTO users (username, email, password_hash, full_name) 
                       VALUES (?, ?, ?, ?) RETURNING *""",
                    (user_data.username, user_data.email, password_hash, user_data.full_name)
                )
                
                user_row = cursor.fetchone()
                conn.commit()
                
                # Convert to User model
                user = User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    full_name=user_row['full_name'],
                    is_active=bool(user_row['is_active']),
                    created_at=datetime.fromisoformat(user_row['created_at'])
                )
                
                self.logger.info(f"User registered successfully: {user.username}")
                return user
                
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to register user: {e}")
            raise ValueError("Failed to create user account")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user and return user data if successful."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                user_row = conn.execute(
                    "SELECT * FROM users WHERE username = ? AND is_active = 1",
                    (username,)
                ).fetchone()
                
                if not user_row:
                    return None
                
                # Verify password
                if not self._verify_password(password, user_row['password_hash']):
                    return None
                
                # Return user data
                return User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    full_name=user_row['full_name'],
                    is_active=bool(user_row['is_active']),
                    created_at=datetime.fromisoformat(user_row['created_at'])
                )
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None
    
    def create_tokens(self, user: User) -> TokenData:
        """Create access and refresh tokens for a user."""
        try:
            # Create access token
            access_token_data = {
                "sub": user.username,
                "user_id": user.id,
                "email": user.email
            }
            access_token = self._create_access_token(access_token_data)
            
            # Create refresh token
            refresh_token = self._create_refresh_token(user.id)
            
            return TokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create tokens: {e}")
            raise ValueError("Failed to create authentication tokens")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            
            if username is None or user_id is None:
                return None
                
            return payload
            
        except JWTError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[TokenData]:
        """Create a new access token using a refresh token."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Find valid refresh token sessions
                sessions = conn.execute(
                    """SELECT s.*, u.username, u.email FROM user_sessions s
                       JOIN users u ON s.user_id = u.id
                       WHERE s.expires_at > ? AND u.is_active = 1""",
                    (datetime.utcnow(),)
                ).fetchall()
                
                # Check if refresh token matches any session
                for session in sessions:
                    if self._verify_password(refresh_token, session['refresh_token_hash']):
                        # Create new access token
                        access_token_data = {
                            "sub": session['username'],
                            "user_id": session['user_id'],
                            "email": session['email']
                        }
                        access_token = self._create_access_token(access_token_data)
                        
                        return TokenData(
                            access_token=access_token,
                            refresh_token=refresh_token,  # Keep the same refresh token
                            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
                        )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return None
    
    def logout_user(self, refresh_token: str) -> bool:
        """Logout a user by invalidating their refresh token."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Find and delete the refresh token session
                sessions = conn.execute(
                    "SELECT * FROM user_sessions WHERE expires_at > ?",
                    (datetime.utcnow(),)
                ).fetchall()
                
                for session in sessions:
                    if self._verify_password(refresh_token, session['refresh_token_hash']):
                        conn.execute(
                            "DELETE FROM user_sessions WHERE id = ?",
                            (session['id'],)
                        )
                        conn.commit()
                        self.logger.info(f"User logged out successfully")
                        return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                user_row = conn.execute(
                    "SELECT * FROM users WHERE id = ? AND is_active = 1",
                    (user_id,)
                ).fetchone()
                
                if user_row:
                    return User(
                        id=user_row['id'],
                        username=user_row['username'],
                        email=user_row['email'],
                        full_name=user_row['full_name'],
                        is_active=bool(user_row['is_active']),
                        created_at=datetime.fromisoformat(user_row['created_at'])
                    )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get user by ID: {e}")
            return None
    
    def cleanup_expired_sessions(self):
        """Clean up expired refresh token sessions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute(
                    "DELETE FROM user_sessions WHERE expires_at < ?",
                    (datetime.utcnow(),)
                )
                conn.commit()
                
                if result.rowcount > 0:
                    self.logger.info(f"Cleaned up {result.rowcount} expired sessions")
                    
        except Exception as e:
            self.logger.error(f"Session cleanup error: {e}")


# Global auth manager instance
auth_manager = UserAuthManager()