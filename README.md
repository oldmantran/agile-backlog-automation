# 🧠 Agile Backlog Automation

A sophisticated multi-agent AI system that transforms product visions into structured, actionable backlogs. Built with modern AI models (including local LLM support via Ollama), this system generates epics, features, user stories, developer tasks, and QA test cases with full Azure DevOps integration and advanced work item management capabilities.

## 🚨 Current Project Status (2025-07-19)

### **✅ Major New Features**
- **🚀 Ollama Local LLM Integration**: Full support for local LLM inference using Ollama
  - **95-99% cost reduction** compared to cloud providers
  - **Multiple model support**: 8B (fast), 70B (high quality), CodeLlama 34B (code-focused)
  - **GPU acceleration** with CUDA support
  - **Frontend configuration** in Settings page
  - **Real-time model switching** and preset selection
- **✅ Enhanced Settings Management**: Complete user settings system with database persistence
- **✅ QA Agent Resilience**: Robust fallback mechanisms prevent retry loops
- **✅ Real-time Progress**: SSE implementation with live updates

### **Performance Improvements**
- **✅ Local LLM Support**: Run completely offline with Ollama
- **✅ Cost Optimization**: 95-99% savings with local inference
- **✅ System Defaults Toggle**: Users can choose between system defaults and custom settings
- **✅ Better Error Handling**: Graceful degradation instead of complete failures
- **✅ Cost Control**: User-specific work item limits with database persistence

### **Hardware Requirements for Local LLM**
- **Minimum**: 8GB RAM, any CPU
- **Recommended**: 16GB+ RAM, NVIDIA GPU with 8GB+ VRAM
- **Optimal**: 32GB+ RAM, NVIDIA RTX 4090 (24GB VRAM) - **Perfect for 70B models**

## 🏗️ Architecture Overview

### **Core Components**
```
Frontend (React) ←→ API Server (FastAPI) ←→ AI Agents ←→ Azure DevOps
     ↑                    ↑                    ↑              ↑
  Real-time UI      SSE Progress      Multi-Agent      Work Items
  Monitoring        Streaming         Pipeline         Creation
     ↑                    ↑                    ↑              ↑
  Settings UI       Settings API      LLM Providers    Database
  Management        (Database)        (Ollama/Cloud)   Storage
```

### **LLM Provider Support**
- **🤖 Ollama (Local)**: llama3.1:8b, llama3.1:70b, codellama:34b, mistral:7b
- **☁️ OpenAI**: GPT-4, GPT-3.5-turbo
- **☁️ Grok (xAI)**: grok-4-latest

### **AI Agent Pipeline**
1. **Epic Strategist** - Transforms product vision into high-level epics
2. **Feature Decomposer** - Breaks epics into features with business value focus
3. **User Story Decomposer** - Creates user stories with acceptance criteria
4. **Developer Agent** - Generates technical tasks with time estimates
5. **QA Lead Agent** - Orchestrates test generation with sub-agents:
   - **Test Plan Agent** - Creates test plans for features
   - **Test Suite Agent** - Creates test suites for user stories  
   - **Test Case Agent** - Creates individual test cases

### **Work Item Hierarchy (Azure DevOps)**
```
Epic
├── Feature (Business Value Focus)
│   ├── User Story (with Acceptance Criteria)
│   │   ├── Task (Development Work)
│   │   └── Test Case (QA Validation)
│   └── User Story (with Acceptance Criteria)
│       ├── Task (Development Work)
│       └── Test Case (QA Validation)
└── Feature (Business Value Focus)
    └── ...
```

## 📁 Project Structure

```
agile-backlog-automation/
├── agents/                    # AI Agent implementations
│   ├── base_agent.py         # Base agent class with LLM provider support
│   ├── epic_strategist.py    # Epic generation agent
│   ├── feature_decomposer_agent.py
│   ├── user_story_decomposer_agent.py
│   ├── developer_agent.py    # Task generation agent
│   ├── qa_lead_agent.py      # QA orchestration agent (supervisor)
│   └── qa/                   # QA sub-agents
│       ├── test_plan_agent.py    # Test plan creation agent
│       ├── test_suite_agent.py   # Test suite creation agent
│       └── test_case_agent.py    # Test case creation agent
├── supervisor/               # Workflow orchestration
│   ├── supervisor.py        # Main workflow supervisor
│   └── main.py              # Supervisor entry point
├── frontend/                # React-based UI
│   ├── src/
│   │   ├── screens/         # Application screens
│   │   │   ├── settings/    # Settings management screens
│   │   │   └── ... (other screens)
│   │   ├── components/      # Reusable components
│   │   ├── services/        # API services
│   │   └── hooks/           # Custom React hooks
│   └── package.json
├── docs/                    # Documentation and analysis files
│   ├── OLLAMA_LOCAL_LLM_IMPLEMENTATION_GUIDE.md
│   ├── COMPREHENSIVE_APPLICATION_ANALYSIS.md
│   └── ... (other documentation)
├── unified_api_server.py    # Main FastAPI server (consolidated)
├── db.py                    # Database operations (jobs + user settings)
├── config/                  # Configuration management
│   ├── config_loader.py     # Environment and YAML config loader
│   └── settings.yaml        # Default settings
├── utils/                   # Utility functions
│   ├── ollama_client.py     # Ollama client and provider
│   ├── settings_manager.py  # Database-based settings management
│   ├── user_id_resolver.py  # User identification from .env
│   └── ... (other utilities)
├── tools/                   # Development and debugging tools
│   ├── test_ollama_integration.py    # Ollama integration tests
│   ├── test_vision_with_ollama.py    # Vision statement testing
│   ├── test_ollama_api.py           # API endpoint testing
│   ├── debug_ollama_path.py         # Ollama path debugging
│   ├── test_ado_connection.py       # Azure DevOps connection test
│   └── ... (other tools)
├── integrators/             # External integrations
├── clients/                 # API clients
├── data/                    # All data files
│   ├── database/           # Database files
│   ├── logs/               # Application logs
│   └── output/             # Generated outputs
├── samples/                 # Sample configuration files
├── quick_start.bat          # Quick startup script
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- Node.js 16+ (for frontend)
- Azure DevOps account with PAT
- **For Local LLM**: Ollama installed (optional but recommended)

### **1. Installation**

```bash
# Clone repository
git clone https://github.com/oldmantran/agile-backlog-automation.git
cd agile-backlog-automation

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux  
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### **2. Configuration**

Create a `.env` file in the project root:

```env
# LLM Provider Configuration (choose one)
LLM_PROVIDER=ollama                    # Use local Ollama (recommended)
# LLM_PROVIDER=openai                  # Use OpenAI
# LLM_PROVIDER=grok                    # Use Grok (xAI)

# Ollama Configuration (for local LLM)
OLLAMA_MODEL=llama3.1:8b              # 8B for testing, 70B for production
OLLAMA_PRESET=fast                    # fast, balanced, high_quality, code_focused
OLLAMA_BASE_URL=http://localhost:11434

# Cloud LLM Configuration (if using cloud providers)
OPENAI_API_KEY=your_openai_api_key_here
GROK_API_KEY=your_grok_api_key_here

# Azure DevOps Configuration
AZURE_DEVOPS_ORG=your_organization
AZURE_DEVOPS_PROJECT=your_project
AZURE_DEVOPS_PAT=your_personal_access_token
```

### **3. Local LLM Setup (Optional but Recommended)**

```bash
# Install Ollama
# Download from: https://ollama.ai/download

# Download recommended models
ollama pull llama3.1:8b      # Fast model for testing
ollama pull llama3.1:70b     # High-quality model for production
ollama pull codellama:34b    # Code-focused model

# Test Ollama integration
python tools/test_ollama_integration.py
```

### **4. Start the Application**

```bash
# Start the backend server
python unified_api_server.py

# In another terminal, start the frontend
cd frontend
npm start
```

## 🎯 Usage

### **1. Configure LLM Provider**
- Go to **Settings** → **LLM Configuration**
- Select your preferred provider (Ollama recommended for cost savings)
- Choose model and preset based on your needs

### **2. Create a Project**
- Navigate to **Projects** → **Create New Project**
- Enter project basics and vision statement
- Configure Azure DevOps settings

### **3. Generate Backlog**
- Click **Generate Backlog** on your project
- Monitor real-time progress
- Review generated epics, features, user stories, tasks, and test cases

### **4. Export to Azure DevOps**
- Generated work items are automatically created in Azure DevOps
- Full traceability from epics down to test cases
- Proper parent-child relationships maintained

## 💰 Cost Analysis

### **Local LLM (Ollama) - Recommended**
- **Power**: ~$0.02-0.05 per backlog job
- **Hardware**: One-time cost (your existing hardware)
- **Privacy**: Complete data privacy
- **Speed**: Comparable to cloud (with good hardware)

### **Cloud LLM (OpenAI/Grok)**
- **API Costs**: $5-15 per backlog job
- **Privacy**: Data sent to cloud provider
- **Speed**: Fast, but depends on API availability

### **Savings with Local LLM**: 95-99% cost reduction! 🎉

## 🔧 Advanced Configuration

### **Model Selection Guide**

#### **For Development/Testing**
- **Model**: `llama3.1:8b`
- **Preset**: `fast`
- **Speed**: ⚡⚡⚡⚡⚡
- **Quality**: ⭐⭐⭐

#### **For Production Quality**
- **Model**: `llama3.1:70b`
- **Preset**: `high_quality`
- **Speed**: ⚡⚡
- **Quality**: ⭐⭐⭐⭐⭐

#### **For Code-Focused Tasks**
- **Model**: `codellama:34b`
- **Preset**: `code_focused`
- **Speed**: ⚡⚡⚡
- **Quality**: ⭐⭐⭐⭐

### **Work Item Limits**
Configure limits in Settings to control costs and generation scope:
- Max Epics: 2-10
- Max Features per Epic: 3-8
- Max User Stories per Feature: 5-15
- Max Tasks per User Story: 5-20
- Max Test Cases per User Story: 3-10

## 🧪 Testing

### **Test Ollama Integration**
```bash
python tools/test_ollama_integration.py
```

### **Test Vision Statement Processing**
```bash
python tools/test_vision_with_ollama.py
```

### **Test Azure DevOps Connection**
```bash
python tools/test_ado_connection.py
```

## 🚨 Troubleshooting

### **Common Issues**

#### **Ollama Not Found**
```bash
# Check if Ollama is installed
ollama --version

# Add to PATH if needed
# Windows: Add C:\Users\%USERNAME%\AppData\Local\Programs\Ollama to PATH
```

#### **Model Not Downloaded**
```bash
# List available models
ollama list

# Download missing model
ollama pull llama3.1:8b
```

#### **Out of Memory**
```bash
# Use smaller model
OLLAMA_MODEL=llama3.1:8b

# Or use quantized version
ollama pull llama3.1:8b-q4_0
```

### **Performance Optimization**

#### **For RTX 4090 (Optimal Setup)**
- **Model**: `llama3.1:70b`
- **Preset**: `high_quality`
- **Batch Size**: 1-2
- **Context Length**: 4096 tokens

#### **For General Hardware**
- **Model**: `llama3.1:8b`
- **Preset**: `balanced`
- **Memory**: 8GB+ RAM recommended

## 📊 Monitoring & Logging

### **Enable Detailed Logging**
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### **Monitor Performance**
- Check generation times in the UI
- Monitor GPU usage with `nvidia-smi`
- Review logs in `data/logs/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### **Documentation**
- [Ollama Implementation Guide](docs/OLLAMA_LOCAL_LLM_IMPLEMENTATION_GUIDE.md)
- [Comprehensive Application Analysis](docs/COMPREHENSIVE_APPLICATION_ANALYSIS.md)

### **Resources**
- **Ollama Documentation**: https://ollama.ai/docs
- **Azure DevOps API**: https://docs.microsoft.com/en-us/azure/devops/integrate/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

---

## 🎉 Ready to Transform Your Product Visions!

With local LLM support, you can now generate complete backlogs at 95-99% cost savings while maintaining full data privacy. Start with the 8B model for testing, then switch to the 70B model for production-quality results.

**Expected timeline**: 30-60 minutes for initial setup, then immediate cost savings and high-quality backlog generation!