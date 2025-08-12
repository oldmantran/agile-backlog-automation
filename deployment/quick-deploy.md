# Quick Deployment Guide

## Easiest Deployment: Vercel + Railway

### Frontend (Vercel)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy Frontend**
   ```bash
   cd frontend
   vercel
   ```
   - Follow prompts to create account/login
   - Select "Create new project"
   - Use default settings
   - Add environment variable: `REACT_APP_API_URL` = your Railway backend URL

### Backend (Railway)

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend**
   - Click "New Project" → "Deploy from GitHub repo"
   - Or use CLI:
   ```bash
   npm i -g @railway/cli
   railway login
   railway init
   railway up
   ```

3. **Add Environment Variables in Railway Dashboard**
   ```
   JWT_SECRET_KEY=<generate-secure-key>
   JWT_REFRESH_SECRET_KEY=<generate-secure-key>
   OPENAI_API_KEY=<your-key>
   CORS_ORIGINS=["https://your-app.vercel.app"]
   ```

4. **Get Public URL**
   - Railway will provide a URL like: `https://your-app.railway.app`
   - Update frontend's `REACT_APP_API_URL` in Vercel

## Alternative: One-Click Heroku Deploy

### Add to your repository:

1. **app.json** (for Heroku button)
```json
{
  "name": "Agile Backlog Automation",
  "description": "AI-powered backlog generation system",
  "repository": "https://github.com/yourusername/agile-backlog-automation",
  "keywords": ["agile", "ai", "backlog", "automation"],
  "env": {
    "JWT_SECRET_KEY": {
      "description": "Secret key for JWT tokens",
      "generator": "secret"
    },
    "JWT_REFRESH_SECRET_KEY": {
      "description": "Secret key for JWT refresh tokens",
      "generator": "secret"
    },
    "OPENAI_API_KEY": {
      "description": "Your OpenAI API key",
      "required": true
    }
  },
  "formation": {
    "web": {
      "quantity": 1,
      "size": "free"
    }
  },
  "buildpacks": [
    {
      "url": "heroku/python"
    },
    {
      "url": "heroku/nodejs"
    }
  ]
}
```

2. **Add Deploy Button to README**
```markdown
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/agile-backlog-automation)
```

## Deploy with Render.com

1. **Create account at [render.com](https://render.com)**

2. **Deploy Backend**
   - New → Web Service
   - Connect GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python unified_api_server.py`
   - Add environment variables

3. **Deploy Frontend**
   - New → Static Site
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/build`

## Docker Deployment to DigitalOcean

1. **Create Droplet**
   - Choose Docker from Marketplace
   - Select $20/month droplet (2GB RAM minimum)

2. **Deploy with Docker Compose**
   ```bash
   ssh root@your-droplet-ip
   git clone your-repo
   cd agile-backlog-automation
   
   # Create .env file
   nano .env
   
   # Run with Docker Compose
   docker-compose up -d
   ```

3. **Setup Domain**
   - Point domain to droplet IP
   - Use Caddy for automatic SSL:
   ```yaml
   # Add to docker-compose.yml
   caddy:
     image: caddy:alpine
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./Caddyfile:/etc/caddy/Caddyfile
       - caddy_data:/data
     restart: unless-stopped
   ```

   **Caddyfile:**
   ```
   yourdomain.com {
     reverse_proxy frontend:80
   }
   
   api.yourdomain.com {
     reverse_proxy backend:8000
   }
   ```

## Post-Deployment Checklist

1. **Test User Registration**
   - Create test account
   - Verify email if enabled
   - Test login/logout

2. **Test Core Features**
   - Create project
   - Generate backlog
   - Check Azure DevOps integration

3. **Monitor**
   - Check logs: `docker-compose logs -f`
   - Monitor resource usage
   - Set up uptime monitoring

4. **Security**
   - Ensure HTTPS is working
   - Check CORS settings
   - Verify JWT tokens expire properly
   - Rate limiting is active

5. **Backup**
   - Database backups
   - Environment variables backed up
   - Code repository up to date