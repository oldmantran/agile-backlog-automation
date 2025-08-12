#!/bin/bash
# Backend deployment script for Ubuntu/Debian servers

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx

# Install supervisor for process management
sudo apt install -y supervisor

# Create application directory
sudo mkdir -p /opt/agile-backlog-automation
sudo chown $USER:$USER /opt/agile-backlog-automation

# Clone or copy your application
cd /opt/agile-backlog-automation
# git clone <your-repo> . # If using git
# Or copy files manually

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file for production
cat > .env << EOL
# JWT Configuration (REQUIRED - Generate secure secrets!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_REFRESH_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database (for production, consider PostgreSQL)
DATABASE_URL=sqlite:///./backlog_jobs.db

# Email Configuration (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_FROM_EMAIL=noreply@yourdomain.com

# LLM Provider Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# Optional: Other LLM providers
# GROK_API_KEY=your-grok-key
# OLLAMA_BASE_URL=http://localhost:11434

# CORS (update with your frontend domain)
CORS_ORIGINS=["https://yourdomain.com","http://localhost:3000"]

# Production Settings
DEBUG=False
ENVIRONMENT=production
EOL

# Create supervisor configuration
sudo tee /etc/supervisor/conf.d/agile-backlog.conf << EOL
[program:agile-backlog-api]
command=/opt/agile-backlog-automation/venv/bin/python unified_api_server.py
directory=/opt/agile-backlog-automation
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/agile-backlog/api.log
environment="PATH=/opt/agile-backlog-automation/venv/bin"
EOL

# Create log directory
sudo mkdir -p /var/log/agile-backlog
sudo chown $USER:$USER /var/log/agile-backlog

# Configure Nginx as reverse proxy
sudo tee /etc/nginx/sites-available/agile-backlog << EOL
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable site
sudo ln -s /etc/nginx/sites-available/agile-backlog /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start agile-backlog-api

# Setup SSL with Let's Encrypt
# sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

echo "Backend deployment complete!"
echo "Don't forget to:"
echo "1. Update CORS_ORIGINS in .env with your frontend domain"
echo "2. Set up SSL with: sudo certbot --nginx -d yourdomain.com"
echo "3. Configure your firewall to allow ports 80 and 443"