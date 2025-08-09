# Authentication System

## Overview

The Agile Backlog Automation system uses a secure JWT + Local Users authentication system. All application routes are protected and require user authentication.

## Security Features

### 🔐 **Backend Security**
- **bcrypt Password Hashing**: All passwords securely hashed with salt
- **JWT Access Tokens**: 30-minute expiration with automatic refresh
- **HTTP-Only Refresh Tokens**: 7-day expiration stored in secure cookies
- **SQLite User Database**: Local user storage with proper indexes
- **Session Management**: Automatic cleanup of expired sessions
- **Input Validation**: Comprehensive validation for all user inputs

### 🎨 **Frontend Security**
- **Protected Routes**: All application functionality requires authentication
- **Automatic Token Refresh**: Seamless background token renewal 5 minutes before expiration
- **Secure Storage**: Access tokens in memory, refresh tokens in HTTP-only cookies
- **CSRF Protection**: SameSite cookies prevent cross-site attacks
- **XSS Prevention**: Refresh tokens inaccessible to JavaScript

## User Experience

### 🚀 **First-Time Setup**
1. **Start the Application**: Run `python unified_api_server.py`
2. **Visit the Application**: Navigate to `http://localhost:8000`
3. **Create Account**: Click "Create Account" on the login screen
4. **Register**: Fill out the registration form with:
   - Username (3+ characters, alphanumeric + underscore/hyphen)
   - Email address (valid email format)
   - Password (8+ chars, uppercase, lowercase, number required)
   - Full name (optional)

### 🔑 **Login Process**
1. **Enter Credentials**: Username and password
2. **Automatic Authentication**: JWT tokens issued upon successful login
3. **Session Persistence**: Stay logged in across browser sessions
4. **Access Granted**: Full access to all application features

### 🔄 **Session Management**
- **Automatic Refresh**: Tokens refresh automatically before expiration
- **Logout**: Click "Sign Out" in sidebar to end session
- **Session Expiry**: Inactive sessions expire after 7 days
- **Multi-Browser**: Each browser session managed independently

## Password Requirements

### 🛡️ **Security Standards**
- **Minimum Length**: 8 characters
- **Uppercase**: At least one uppercase letter (A-Z)
- **Lowercase**: At least one lowercase letter (a-z)
- **Number**: At least one number (0-9)
- **Strength Indicator**: Real-time password strength feedback

### 💡 **Password Recommendations**
- Use a unique password not used elsewhere
- Consider using a password manager
- Avoid common words or personal information
- Mix letters, numbers, and special characters

## API Endpoints

### 🔌 **Authentication API**
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Authenticate user
- `POST /api/auth/logout` - End user session
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user information
- `POST /api/auth/verify` - Verify token validity

### 🔒 **Protected Endpoints**
All other API endpoints require authentication:
- Authorization header: `Bearer <access_token>`
- Refresh token cookie automatically included
- 401 responses trigger automatic token refresh

## Database Schema

### 📊 **Users Table**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 🔄 **Sessions Table**
```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    refresh_token_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

## Development

### 🛠️ **Local Development**
- No external dependencies required
- Works completely offline
- SQLite database created automatically
- Self-contained authentication system

### 🔧 **Configuration**
- JWT secret key auto-generated if not provided
- Token expiration times configurable
- Database path configurable
- CORS settings for frontend integration

## Troubleshooting

### ❓ **Common Issues**

**Login Fails:**
- Check username/password combination
- Ensure account was created successfully
- Check browser console for errors

**Session Expires:**
- Sessions expire after 7 days of inactivity
- Simply log in again to create new session
- Clear browser cookies if experiencing issues

**Password Requirements:**
- Must meet all security requirements
- Use password strength indicator for guidance
- Try different password if requirements not met

**Token Refresh Issues:**
- Clear browser localStorage and cookies
- Log out and log in again
- Check browser's cookie settings

### 🐛 **Debug Mode**
Enable debug logging to troubleshoot authentication issues:
```python
import logging
logging.getLogger("auth").setLevel(logging.DEBUG)
```

## Security Best Practices

### 👤 **For Users**
- Use strong, unique passwords
- Log out when finished using the application
- Don't share your credentials
- Report any suspicious activity

### 👨‍💻 **For Developers**
- Keep authentication dependencies updated
- Monitor authentication logs
- Implement proper error handling
- Follow security best practices for JWT

## Future Enhancements

### 🚀 **Planned Features**
- Password reset functionality
- Account email verification
- Multi-factor authentication (MFA)
- OAuth integration (Google, Microsoft, GitHub)
- Role-based access control (RBAC)
- Account lockout after failed attempts

The authentication system provides a solid foundation for secure, local user management while keeping the system lightweight and self-contained.