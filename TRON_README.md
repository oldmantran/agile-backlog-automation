# 🎮 TRON Backlog Automation

> *A futuristic, AI-powered Azure DevOps backlog management system with a Tron Legacy-inspired interface*

## ✨ Features

### 🔧 **Configuration Management**
- **Environment Variables**: Configure Azure DevOps PAT, Organization, Project
- **AI Providers**: Support for OpenAI and Grok (xAI) 
- **Area Paths**: Set target areas for work item management
- **Real-time Validation**: Test connections before saving

### 🎯 **Core Operations**
- **🆕 Create New Backlog**: Generate comprehensive backlogs from vision statements using AI
- **🔄 Backlog Sweeper**: AI-powered validation and enhancement of existing work items
- **🗑️ Cleanup Work Items**: Bulk delete Azure DevOps work items with search and filter
- **🧪 Cleanup Test Cases**: Remove test cases, suites, and plans efficiently

### 🎨 **Tron-Themed Interface**
- **Cyan Glow Effects**: Authentic Tron Legacy visual design
- **Grid Background**: Matrix-style animated backgrounds
- **Pulse Animations**: Dynamic glowing elements
- **Scan Lines**: Retro-futuristic scanning animations
- **Sound-Responsive**: Visual elements that react to system activity

### 🚀 **Executable Distribution**
- **Standalone Build**: Create Windows/macOS/Linux executables
- **No Dependencies**: Run without Python or Node.js installation
- **Browser-Based UI**: Automatically opens in default browser
- **Local Server**: Self-contained backend API

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Azure DevOps** account with PAT token
- **OpenAI API Key** or **Grok API Key**

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd agile-backlog-automation

# Run the setup script (Windows)
setup_and_start_tron.bat

# Or manual setup:
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install and build frontend
cd frontend
npm install
npm run build
cd ..

# 3. Start the Tron API server
python tron_api_server.py
```

### Configuration
1. **Open** http://localhost:8000 in your browser
2. **Navigate** to Configuration → Azure DevOps
3. **Enter** your Azure DevOps details:
   - Organization name
   - Project name  
   - Personal Access Token (with Work Items read/write scope)
4. **Configure** AI Provider:
   - Select OpenAI or Grok
   - Enter your API key
5. **Validate** connections and save

## 🎮 Usage Guide

### Environment Setup
```bash
# Required environment variables (set via UI or .env file)
AZURE_DEVOPS_PAT=your_personal_access_token
AZURE_DEVOPS_ORG=your_organization
AZURE_DEVOPS_PROJECT=your_project_name
LLM_PROVIDER=openai  # or 'grok'
OPENAI_API_KEY=your_openai_key  # if using OpenAI
GROK_API_KEY=your_grok_key      # if using Grok
```

### Creating New Backlogs
1. Click **"Create New Backlog"**
2. Enter comprehensive vision statement including:
   - Project goals and objectives
   - Target audience
   - Success metrics
   - Key features and requirements
3. Configure AI settings
4. Review generated backlog
5. Deploy to Azure DevOps

### Running Backlog Sweeper
1. Navigate to **"Backlog Sweeper"**
2. Set target area path
3. Configure enhancement options:
   - ✅ Acceptance Criteria Enhancement
   - ✅ Task Decomposition  
   - ✅ Quality Validation
   - ✅ Requirements Enhancement
4. Start sweeper and monitor progress
5. Review completed actions and errors

### Cleanup Operations
- **Work Items**: Search, filter, and bulk delete work items
- **Test Cases**: Manage test cases, suites, and plans
- **Bulk Operations**: Select multiple items for efficient cleanup
- **Progress Tracking**: Real-time deletion progress with logs

## 🏗️ Architecture

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── screens/           # Tron-themed UI screens
│   ├── components/        # shadcn/ui components  
│   ├── styles/           # Tron CSS animations
│   └── utils/            # Helper functions
├── public/               # Static assets
└── build/               # Production build
```

### Backend (Python FastAPI)
```
backend/
├── tron_api_server.py    # Main API server
├── agents/              # AI agent modules
├── integrators/         # Azure DevOps integration
├── config/              # Configuration management
└── utils/               # Utility functions
```

### Key Technologies
- **Frontend**: React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3.8+, Azure DevOps API
- **AI**: OpenAI GPT-4 / Grok integration
- **UI Theme**: Tron Legacy inspired design system
- **Build**: React Scripts, PyInstaller for executables

## 🎯 API Endpoints

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Save configuration  
- `POST /api/validate-azure` - Validate Azure DevOps connection
- `POST /api/validate-ai` - Validate AI provider connection

### Work Items
- `GET /api/workitems` - List work items
- `POST /api/workitems/delete` - Delete selected work items

### Test Management  
- `GET /api/testcases` - List test cases
- `GET /api/testsuites` - List test suites
- `GET /api/testplans` - List test plans
- `POST /api/test/delete` - Delete test items

### Backlog Sweeper
- `GET /api/sweeper/config` - Get sweeper configuration
- `POST /api/sweeper/config` - Save sweeper configuration
- `POST /api/sweeper/start` - Start sweeper process
- `POST /api/sweeper/stop` - Stop sweeper process
- `GET /api/sweeper/status` - Get sweeper status

## 🎨 Tron Theme Customization

### CSS Variables
```css
:root {
  --tron-cyan: 180 100% 50%;
  --tron-blue: 200 100% 50%; 
  --tron-orange: 25 100% 50%;
  --tron-grid: 180 50% 15%;
  --tron-glow: 180 100% 50%;
}
```

### Custom Classes
- `.tron-grid` - Animated grid background
- `.tron-border` - Glowing cyan borders
- `.tron-glow` - Pulsing glow effect
- `.tron-button` - Futuristic button styling
- `.tron-card` - Glass-effect cards
- `.scan-line` - Scanning animation
- `.pulse-glow` - Breathing glow effect

## 🚀 Building Executables

### Windows Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --noconsole --add-data "frontend/build;frontend/build" tron_api_server.py

# Output: dist/tron_api_server.exe
```

### Cross-Platform Options
- **Windows**: `.exe` via PyInstaller
- **macOS**: `.app` bundle via PyInstaller  
- **Linux**: Binary via PyInstaller
- **Electron**: For true cross-platform desktop app

## 🔧 Development

### Running in Development Mode
```bash
# Backend (hot reload)
python tron_api_server.py

# Frontend (separate terminal)
cd frontend
npm start

# Access at http://localhost:3000 (frontend) 
# API at http://localhost:8000 (backend)
```

### Testing
```bash
# Python tests
pytest

# Frontend tests  
cd frontend
npm test
```

## 📦 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN cd frontend && npm install && npm run build
EXPOSE 8000
CMD ["python", "tron_api_server.py"]
```

### Environment Variables
```bash
# Production environment
ENVIRONMENT=production
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

## 🛡️ Security Considerations

- **API Keys**: Store securely, never commit to version control
- **PAT Tokens**: Use minimal required scopes for Azure DevOps
- **CORS**: Configure appropriate origins for production
- **Input Validation**: All user inputs are validated
- **Rate Limiting**: Implement for production API usage

## 📊 Monitoring & Logging

- **Real-time Status**: Live progress tracking for all operations
- **Error Handling**: Comprehensive error reporting and recovery
- **Audit Logs**: Track all Azure DevOps modifications
- **Performance**: Monitor AI API usage and response times

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/tron-enhancement`)
3. Follow Tron theme guidelines
4. Add tests for new functionality  
5. Submit pull request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🎮 Credits

- **Theme Inspiration**: Tron Legacy (2010) visual design
- **UI Components**: shadcn/ui component library
- **Icons**: React Icons (Feather icon set)
- **AI**: OpenAI GPT-4 and Grok integration
- **Azure**: Microsoft Azure DevOps API

---

*"The Grid. A digital frontier. I tried to picture clusters of information as they moved through the computer..."*

**Built with ⚡ by the Agile Automation Team**
