# Production Deployment Guide

## 🚀 Overview

This guide covers secure production deployment of the Agile Backlog Automation system with enterprise-grade security features.

## 🛡️ Security Hardening Checklist

### 1. Environment Configuration

**Required Environment Variables:**
```bash
# CRITICAL: Set these for production
ENVIRONMENT=production
JWT_SECRET_KEY=your-super-secure-random-key-here
```

**Generate Secure JWT Secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. JWT Security Features

✅ **Implemented Security Features:**
- **Audience/Issuer Validation**: All tokens verified against `agile-backlog-automation` issuer
- **JTI (JWT ID)**: Unique token IDs for blacklisting and tracking
- **Token Blacklisting**: Immediate invalidation on logout/password change
- **Conditional Secure Cookies**: `secure=True` only in production (HTTP-only in dev)
- **Strong Claims**: iat, exp, iss, aud, jti included in all tokens

### 3. Authentication Security

✅ **Rate Limiting & Lockout Protection:**
- **Rate Limits**: 10 login attempts per IP per minute
- **Account Lockout**: 5 failed attempts = 15 minute lockout
- **IP Tracking**: Failed attempts logged with client IP
- **Automatic Cleanup**: Old login attempts purged after 30 days

✅ **Password Security:**
- **bcrypt Hashing**: Industry-standard with automatic salting
- **Token Rotation**: All tokens invalidated on password change
- **Session Management**: Automatic cleanup of expired sessions

### 4. CORS Configuration

✅ **Production CORS Settings:**
```python
# Production - Restricted origins
cors_origins = [
    "https://yourdomain.com",     # Your production domain
    "http://localhost:3000",      # Development only
    "http://localhost:8000"       # Development only
]
```

**⚠️ Important**: Update `yourdomain.com` in `unified_api_server.py` with your actual production domain.

### 5. Cookie Security

✅ **Secure Cookie Configuration:**
- **Production**: `secure=True`, `httpOnly=True`, `samesite="lax"`
- **Development**: `secure=False` (allows HTTP), `httpOnly=True`
- **Automatic Detection**: Based on `ENVIRONMENT` variable

## 🔧 Deployment Steps

### 1. Environment Setup

```bash
# Copy template and configure
cp .env.example .env
nano .env
```

**Required Production Settings:**
```bash
ENVIRONMENT=production
JWT_SECRET_KEY=<32-character-random-key>
AZURE_DEVOPS_PAT=<your-pat>
OPENAI_API_KEY=<your-key>
NOTIFICATION_EMAIL=admin@yourdomain.com
```

### 2. Update CORS Origins

**Edit `unified_api_server.py`:**
```python
# Line ~187-191 in unified_api_server.py
cors_origins = [
    "https://agile-backlog.yourdomain.com",  # Replace with your actual domain
    "https://api.yourdomain.com",            # API subdomain if used  
    # Add additional production domains as needed
]
```

**⚠️ Critical**: Update the TODO comment with your actual production domains before deployment.

### 3. HTTPS Configuration

**Nginx Proxy Example:**
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Database Security

```bash
# Secure database file permissions
chmod 600 agile_backlog.db
chown app_user:app_group agile_backlog.db
```

### 5. Process Management

**Systemd Service Example:**
```ini
[Unit]
Description=Agile Backlog Automation API
After=network.target

[Service]
Type=simple
User=app_user
WorkingDirectory=/path/to/app
Environment=ENVIRONMENT=production
ExecStart=/path/to/venv/bin/python unified_api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🔒 Security Best Practices

### 1. Token Management
- **Rotation**: Tokens auto-rotate every 30 minutes
- **Blacklisting**: Immediate invalidation on logout/password change
- **Cleanup**: Expired tokens and sessions cleaned automatically

### 2. Rate Limiting
- **Login Endpoint**: 10 attempts/minute per IP
- **Account Lockout**: 5 failed attempts = 15 min lockout
- **Production**: Consider Redis for distributed rate limiting

### 3. Monitoring & Logging
```bash
# Enable authentication debug logging
export AUTH_DEBUG=1

# Monitor failed attempts
tail -f logs/auth.log | grep "Failed login"
```

### 4. Rate Limiting & Production Scaling

**Current Implementation (Development/Small Scale):**
- **In-Memory Storage**: Rate limits reset on server restart
- **Single Server**: Works for single-instance deployments  
- **Login Limits**: 10 attempts/minute per IP, 5 failures = 15-minute lockout

**Production Scaling with Redis:**
```python
# Add to requirements.txt: redis>=4.5.0
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_rate_limit_redis(ip: str, endpoint: str = "login") -> bool:
    key = f"rate_limit:{ip}:{endpoint}"
    current = redis_client.get(key)
    if current and int(current) >= RATE_LIMIT_REQUESTS:
        return False
    
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, RATE_LIMIT_WINDOW)
    pipe.execute()
    return True
```

**Redis Benefits:**
- **Persistent**: Survives server restarts and maintains rate limits
- **Distributed**: Works across multiple server instances/load balancers
- **High Performance**: Sub-millisecond operations with Redis clustering
- **Automatic Cleanup**: TTL-based expiration prevents memory leaks

### 4. Database Backups
```bash
# Automated backup script
#!/bin/bash
sqlite3 agile_backlog.db ".backup backup-$(date +%Y%m%d).db"
```

## ⚠️ Security Warnings

### NEVER in Production:
1. **Default JWT Secret**: Auto-generated secrets don't survive restarts
2. **HTTP-Only**: Always use HTTPS with secure cookies
3. **Open CORS**: Never use `allow_origins=["*"]` in production
4. **Debug Mode**: Disable debug logging in production
5. **Default Passwords**: Change all default credentials

### Required for Production:
1. **Fixed JWT Secret**: Set `JWT_SECRET_KEY` environment variable
2. **HTTPS**: Secure cookies require HTTPS
3. **Restricted CORS**: Whitelist only your domains
4. **Rate Limiting**: Implement proper rate limiting (Redis recommended)
5. **Log Monitoring**: Monitor authentication failures

## 🚨 Incident Response

### Account Compromise:
```bash
# Reset all user tokens
curl -X POST http://localhost:8000/api/auth/invalidate-all-tokens \
  -H "Content-Type: application/json" \
  -d '{"user_id": "compromised_user"}'
```

### Security Breach:
1. **Rotate JWT Secret**: Update `JWT_SECRET_KEY`
2. **Invalidate Sessions**: Clear all user sessions
3. **Review Logs**: Check for suspicious activity
4. **Update Passwords**: Force password resets

## 📊 Monitoring Endpoints

```bash
# Health check
curl https://yourdomain.com/api/health

# Authentication status
curl https://yourdomain.com/api/auth/verify \
  -H "Authorization: Bearer <token>"

# System metrics
curl https://yourdomain.com/api/build-version
```

## 🆘 Troubleshooting

### Common Issues:

**1. Cookies Not Working:**
- Check HTTPS configuration
- Verify `secure` flag settings
- Confirm domain matches

**2. CORS Errors:**
- Update `cors_origins` in code
- Check request origin header
- Verify preflight handling

**3. Token Issues:**
- Confirm JWT secret is fixed
- Check token expiration
- Verify audience/issuer claims

**4. Rate Limiting:**
- Clear IP restrictions: Delete login_attempts table
- Adjust limits in `auth_routes.py`
- Consider Redis for production scaling

This production deployment provides enterprise-grade security with proper token management, rate limiting, and secure cookie handling.