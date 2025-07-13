# Setting Up the Frontend and Backend Integration

This guide explains how to set up and run both the frontend and backend components of the Agile Backlog Automation system.

## 1. Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Azure DevOps account with PAT

## 2. Backend Setup

The backend consists of Python-based AI agents that generate and enhance backlog content, plus a FastAPI server for frontend integration.

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables** (create a `.env` file in the project root):
```
AZURE_DEVOPS_ORG=your-org-name
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_PAT=your-personal-access-token
OPENAI_API_KEY=your-openai-api-key
```

3. **Start the backend API server**:
```bash
python api_server.py
```

The backend server will run on http://localhost:8000 by default.

## 3. Frontend Setup

The frontend is a React application that provides a user interface for creating and managing backlogs.

1. **Install frontend dependencies**:
```bash
cd frontend
npm install
```

2. **Start the frontend development server**:
```bash
npm start
```

The frontend will run on http://localhost:3000 by default.

## 4. Quick Start (Both Servers)

### Automated Setup (Recommended):
```bash
setup_and_start.bat
```

This script will:
- Install Python dependencies
- Check for Node.js installation
- Guide you through Node.js installation if needed
- Start both servers in separate windows

### Alternative Methods:
```bash
# Original method (if Node.js is installed)
start_dev.bat

# Cross-platform
python start_dev_servers.py
```

### If Node.js is not installed:
```bash
# Get installation help
install_nodejs.bat

# Or start backend only
start_backend_only.bat
```

## 5. API Integration

The frontend communicates with the backend through REST API endpoints:

- `POST /api/projects` - Create new project
- `POST /api/backlog/generate/{project_id}` - Start backlog generation  
- `GET /api/backlog/status/{job_id}` - Check generation status
- `GET /api/backlog/templates` - Get available templates
- `GET /api/projects/{project_id}` - Get project details
- `GET /api/projects/{project_id}/backlog` - Get generated backlog

## 6. User Flow

1. **Welcome Screen** - Introduction and getting started
2. **Project Wizard** - Multi-step form to configure project:
   - Project Basics (name, domain, team size)
   - Vision & Objectives (goals, metrics, audience)
   - Azure DevOps Setup (connection details)
   - AI Configuration (generation options)
   - Review & Generate (final confirmation)
3. **Generation Progress** - Real-time status of backlog generation
4. **Dashboard** - View projects, active jobs, and results
5. **Project View** - Detailed view of generated backlog items

## 7. Development Features

### Frontend Features:
- ✅ Mobile-first responsive design
- ✅ Chakra UI component library
- ✅ Multi-step wizard form
- ✅ Real-time progress tracking
- ✅ Error handling and validation
- ✅ TypeScript for type safety

### Backend Features:
- ✅ FastAPI REST API server
- ✅ Background job processing
- ✅ Integration with existing agents
- ✅ CORS support for frontend
- ✅ Project data persistence
- ✅ Generation status tracking

### Integration Features:
- ✅ Real-time status polling
- ✅ Job queue management
- ✅ Error handling and retry logic
- ✅ Data validation and sanitization

## 8. Testing the Integration

1. **Use the automated setup (Recommended):**
   ```bash
   setup_and_start.bat
   ```

2. **Or start backend only for API testing:**
   ```bash
   start_backend_only.bat
   ```

3. **Manual approach (if automated scripts fail):**
   ```bash
   # Create virtual environment (first time only)
   python -m venv .venv
   
   # Install backend dependencies
   .venv\Scripts\pip.exe install -r requirements.txt
   
   # Start backend
   .venv\Scripts\python.exe api_server.py
   ```

4. **Then for frontend (in a separate terminal):**
   ```bash
   cd frontend
   npm install
   npm start
   ```

5. **Access the application:**
   - Navigate to http://localhost:3000
   - Click "Get Started" to begin the project wizard
   - Fill out the project forms with your details
   - Complete the wizard and watch the real-time generation progress
   - View the results on the dashboard

## 9. Troubleshooting

### Common Issues:

**Backend server won't start:**
- Ensure all Python dependencies are installed: `pip install -r requirements.txt`
- Check if port 8000 is available
- Verify Python version is 3.8+

**Frontend won't connect to backend:**
- Ensure backend is running on http://localhost:8000
- Check browser console for CORS errors
- Verify API URLs in frontend configuration

**npm/Node.js not found error:**
- Install Node.js from https://nodejs.org/ (use the LTS version)
- Run `install_nodejs.bat` for installation guidance
- Restart your command prompt after installation
- Use `setup_and_start.bat` for automated setup and startup
- Alternatively, start backend only with: `start_backend_only.bat`

**Backend multiprocessing errors:**
- Use `setup_and_start.bat` which starts servers in separate windows
- Or disable reload in api_server.py (already done)
- Or start backend manually: `python api_server.py`

**Generation fails:**
- Check backend logs for error details
- Verify Azure DevOps configuration
- Ensure OpenAI API key is valid

**FastAPI deprecation warnings:**
- These are informational and don't affect functionality
- The code uses modern lifespan event handlers

### Alternative Startup Methods:

If the main startup script fails, try these alternatives:

1. **Automated Setup (Recommended):**
   ```bash
   setup_and_start.bat
   ```

2. **Install Node.js Helper:**
   ```bash
   install_nodejs.bat
   ```

3. **Manual Frontend Start:**
   ```bash
   start_frontend_manual.bat
   ```

4. **Backend Only:**
   ```bash
   start_backend_only.bat
   ```

5. **Separate Terminals:**
   ```bash
   # Terminal 1 - Backend
   python api_server.py
   
   # Terminal 2 - Frontend (if Node.js is installed)
   cd frontend
   npm install
   npm start
   ```

### Log Files:
- Backend logs: Console output from `api_server.py`
- Generation logs: `logs/supervisor.log`
- Frontend logs: Browser developer console

## 10. Production Deployment

For production deployment:

1. **Backend**: Deploy FastAPI server using Gunicorn or similar WSGI server
2. **Frontend**: Build production bundle with `npm run build` and serve with nginx/Apache
3. **Database**: Replace in-memory job storage with Redis or database
4. **Environment**: Use proper environment variables and secrets management
5. **Monitoring**: Add logging, metrics, and health checks
# Method 1: Using the setup script
node frontend/install.js

# Method 2: Manual setup
cd frontend
npm install
```

2. **Start the development server**:
```bash
cd frontend
npm start
```

The frontend will run on http://localhost:3000 by default.

## 4. Working with Both Components

For full functionality, you'll need to run both the backend and frontend simultaneously:

1. Start the backend server in one terminal
2. Start the frontend development server in another terminal
3. Access the UI at http://localhost:3000

## 5. Development Workflow

1. Create a project using the frontend wizard
2. The frontend sends project details to the backend
3. AI agents generate backlog content
4. Generated content is pushed to Azure DevOps
5. The frontend displays status and allows modifications

## 6. Troubleshooting

- **API Connection Issues**: Verify the backend is running on port 8000
- **Azure DevOps Integration**: Check that your PAT has sufficient permissions
- **Frontend Not Loading**: Check for JavaScript console errors in the browser

For more details, refer to the documentation in the `docs/` directory.
