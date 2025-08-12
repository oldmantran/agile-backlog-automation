# Production Deployment Guide

## Prerequisites

1. **Domain Setup**
   - Register a domain (e.g., yourdomain.com)
   - Point DNS A records to your server IP
   - Subdomain for API: api.yourdomain.com → server IP

2. **Server Requirements**
   - Ubuntu 20.04+ or similar Linux distribution
   - Minimum 2GB RAM, 2 CPU cores
   - 20GB+ storage
   - Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)

## Step-by-Step Deployment

### 1. Server Setup

```bash
# Connect to your server
ssh root@your-server-ip

# Create a non-root user
adduser deploy
usermod -aG sudo deploy
su - deploy
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx nodejs npm git

# Install PM2 for Node.js process management
sudo npm install -g pm2

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 3. Deploy Backend

```bash
# Create application directory
sudo mkdir -p /opt/agile-backlog
sudo chown deploy:deploy /opt/agile-backlog
cd /opt/agile-backlog

# Clone your repository or upload files
git clone https://github.com/yourusername/agile-backlog-automation.git .
# OR use SCP/SFTP to upload files

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create production .env file
nano .env
# Add all required environment variables (see .env.example)

# Test the backend
python unified_api_server.py
# Press Ctrl+C to stop

# Setup systemd service
sudo nano /etc/systemd/system/agile-backlog-api.service
```

Add this content:
```ini
[Unit]
Description=Agile Backlog API
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/agile-backlog
Environment="PATH=/opt/agile-backlog/venv/bin"
ExecStart=/opt/agile-backlog/venv/bin/python unified_api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable agile-backlog-api
sudo systemctl start agile-backlog-api
sudo systemctl status agile-backlog-api
```

### 4. Deploy Frontend

```bash
# Build frontend
cd /opt/agile-backlog/frontend
npm install
npm run build

# Copy build files to nginx
sudo mkdir -p /var/www/agile-backlog
sudo cp -r build/* /var/www/agile-backlog/
```

### 5. Configure Nginx

```bash
# Backend API configuration
sudo nano /etc/nginx/sites-available/api.agile-backlog
```

Add:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Frontend configuration
sudo nano /etc/nginx/sites-available/agile-backlog
```

Add:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    root /var/www/agile-backlog;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable sites
sudo ln -s /etc/nginx/sites-available/api.agile-backlog /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/agile-backlog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Setup SSL

```bash
# Get SSL certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 7. Database Setup

For production, consider using PostgreSQL instead of SQLite:

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE agilebacklog;
CREATE USER agileuser WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE agilebacklog TO agileuser;
\q

# Update .env file
DATABASE_URL=postgresql://agileuser:your-secure-password@localhost/agilebacklog
```

### 8. Security Hardening

```bash
# Setup firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Fail2ban for brute force protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## Environment Variables (.env)

Create a secure `.env` file:

```bash
# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For JWT_REFRESH_SECRET_KEY
```

Complete `.env` example:
```env
# JWT Configuration (REQUIRED)
JWT_SECRET_KEY=your-generated-secret-here
JWT_REFRESH_SECRET_KEY=your-generated-refresh-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://agileuser:password@localhost/agilebacklog

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# CORS
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Production
DEBUG=False
ENVIRONMENT=production
```

## Monitoring & Maintenance

### 1. Setup Logging

```bash
# Create log directory
sudo mkdir -p /var/log/agile-backlog
sudo chown deploy:deploy /var/log/agile-backlog

# Configure logrotate
sudo nano /etc/logrotate.d/agile-backlog
```

Add:
```
/var/log/agile-backlog/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 deploy deploy
}
```

### 2. Monitor Services

```bash
# Check service status
sudo systemctl status agile-backlog-api
sudo systemctl status nginx

# View logs
sudo journalctl -u agile-backlog-api -f
tail -f /var/log/nginx/error.log
```

### 3. Backup Database

```bash
# Create backup script
nano ~/backup-agile-backlog.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
mkdir -p $BACKUP_DIR
pg_dump agilebacklog > $BACKUP_DIR/agilebacklog-$(date +%Y%m%d-%H%M%S).sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

```bash
chmod +x ~/backup-agile-backlog.sh
# Add to crontab
crontab -e
# Add: 0 2 * * * /home/deploy/backup-agile-backlog.sh
```

## Quick Deploy with Docker

For easier deployment, use Docker:

```bash
# On your server
cd /opt/agile-backlog
docker-compose up -d

# View logs
docker-compose logs -f

# Update
git pull
docker-compose build
docker-compose up -d
```

## Troubleshooting

1. **502 Bad Gateway**: Backend not running
   - Check: `sudo systemctl status agile-backlog-api`
   - Logs: `sudo journalctl -u agile-backlog-api`

2. **CORS errors**: Update CORS_ORIGINS in .env

3. **Database errors**: Check DATABASE_URL and migrations

4. **SSL issues**: Renew certificates
   - `sudo certbot renew --dry-run`

## Support & Monitoring

Consider adding:
- Uptime monitoring (UptimeRobot, Pingdom)
- Error tracking (Sentry)
- Analytics (Plausible, Matomo)
- Status page (Cachet, Upptime)