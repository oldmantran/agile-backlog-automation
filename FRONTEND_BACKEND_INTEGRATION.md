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

Use the provided startup scripts to run both servers simultaneously:

**Windows:**
```bash
start_dev.bat
```

**Cross-platform:**
```bash
python start_dev_servers.py
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

1. Start both servers using `start_dev.bat` or `python start_dev_servers.py`
2. Navigate to http://localhost:3000
3. Click "Get Started" to begin the project wizard
4. Fill out the project forms with your details
5. Complete the wizard and watch the real-time generation progress
6. View the results on the dashboard

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

**Generation fails:**
- Check backend logs for error details
- Verify Azure DevOps configuration
- Ensure OpenAI API key is valid

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
