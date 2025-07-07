# Setting Up the Frontend and Backend Integration

This guide explains how to set up and run both the frontend and backend components of the Agile Backlog Automation system.

## 1. Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Azure DevOps account with PAT

## 2. Backend Setup

The backend consists of Python-based AI agents that generate and enhance backlog content.

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

3. **Start the backend server**:
```bash
python supervisor/main.py
```

The backend server will run on http://localhost:8000 by default.

## 3. Frontend Setup

The frontend is a React application that provides a user interface for creating and managing backlogs.

1. **Install frontend dependencies**:
```bash
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
