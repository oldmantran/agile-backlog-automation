# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend
- Start the main API server: `python unified_api_server.py`
- Run a single test: `python -m pytest <test_file.py>::<test_function>`
- Install dependencies: `pip install -r requirements.txt`

### Frontend 
- Start development server: `cd frontend && npm start`
- Build for production: `cd frontend && npm run build`
- Run tests: `cd frontend && npm test`
- Install dependencies: `cd frontend && npm install`

### Testing
- Test Ollama integration: `python tools/test_ollama_integration.py`
- Test Azure DevOps connection: `python tools/test_ado_connection.py`
- Test complete workflow: `python tools/test_complete_workflow.py`
- **🛡️ REGRESSION PREVENTION**: Run full regression test suite: `tools/run_regression_tests.bat`
- **🚨 CRITICAL**: Run pre-commit checks: `python tools/pre_commit_check.py`
- **💨 SMOKE TESTS**: Validate core functionality: `python tests/test_core_smoke.py`
- **🔄 INTEGRATION**: Test vision processing pipeline: `python tests/test_vision_integration.py`

### Development Scripts
- Start application: `tools/quick_start.bat` (Windows)
- Kill development processes: `tools/kill_dev_processes.bat` (Windows)
- Debug QA agents: `python tools/debug_qa_lead_agent.py`
- Scan test artifacts: `python tools/scan_remaining_test_artifacts.py`
- Debug parallel processing: `python tools/debug_parallel_processing.py`
- **Retry failed uploads**: `python tools/retry_failed_uploads.py <job_id> [retry|summary|details|cleanup]`

## 🛡️ REGRESSION PREVENTION PROTOCOL (August 4, 2025)

**CRITICAL**: To prevent breaking core functionality, ALWAYS follow this protocol:

### Before Making Any Changes:
1. **Run regression tests**: `tools/run_regression_tests.bat`
2. **Document what you're changing** and why
3. **Identify potential impact areas** (vision processing, template system, context flow)

### After Making Changes:
1. **MANDATORY**: Run `python tools/pre_commit_check.py` - must pass 100%
2. **Test specific functionality** you modified with targeted tests
3. **Run full regression suite** before considering changes complete
4. **Verify in browser** that basic project creation still works

### Core Functions That Must NEVER Break:
- ✅ Vision statement processing from API → Supervisor → Agents
- ✅ Template variable resolution (especially `product_vision`)
- ✅ Agent prompt generation and LLM communication  
- ✅ Project context flow through all stages
- ✅ Domain selection and basic project creation
- ✅ Settings persistence and retrieval

**If ANY regression test fails, STOP and fix before proceeding.**

### Regression Test Files:
- `tests/test_core_smoke.py` - Critical path validation
- `tests/test_vision_integration.py` - End-to-end vision processing
- `tools/pre_commit_check.py` - Pre-commit safety checks
- `tools/run_regression_tests.bat` - Complete test suite

## Recent Major Updates (August 2025)

### 🔄 Outbox Pattern Implementation (August 3-4, 2025)
- **Zero Data Loss Architecture**: Local SQLite staging prevents loss of 2+ hour generation work
- **Resumable Operations**: Retry 360 failed uploads without regenerating 796 total items
- **Cascading Failure Prevention**: Epic failure no longer causes loss of 200+ child work items
- **Enterprise Reliability**: HTTP timeouts, exponential backoff, rate limiting, comprehensive retry tools
- **Performance Protection**: Generation investment is fully protected, upload becomes separate concern

### Performance Optimizations (40-45% faster)
- **Parallel Processing**: Re-enabled limited task generation parallelism (2 workers)
- **Timeout Optimization**: Reduced qwen2.5:32B timeout from 90s to 45s 
- **Generation Speed**: Improved from 44 minutes to ~20-25 minutes for 217 work items

### User Story Quality Fixes
- **Duplicate Prevention**: Fixed triplicate user stories with similar descriptions
- **Template Cleanup**: Removed malformed "As a user, I want X so that Y" placeholder text
- **Anti-Decomposition**: Enhanced logic to prevent over-splitting of related functionality

### Domain Selection Enhancement
- **Grid-Based UI**: Replaced dropdown with intuitive 31-domain grid selection
- **API Reliability**: Fixed domains endpoint to consistently return all database entries
- **AI Integration**: Clear toggle between AI-detected and manual domain selection

## Architecture Overview

This is a multi-agent AI system that transforms product visions into structured Azure DevOps backlogs.

**Current Status**: Beta/Development Ready - Core functionality working, but requires additional testing and hardening before production deployment.

### Core Components

**Frontend**: React TypeScript application with Tailwind CSS and shadcn/ui components. Uses React Query for API state management and provides real-time progress updates via Server-Sent Events.

**Backend**: FastAPI server (`unified_api_server.py`) that orchestrates the AI agent pipeline and provides REST endpoints for the frontend.

**AI Agent Pipeline**: Multi-stage workflow managed by `supervisor/supervisor.py`:
1. `epic_strategist.py` - Creates high-level epics from product vision
2. `feature_decomposer_agent.py` - Breaks epics into features
3. `user_story_decomposer_agent.py` - Creates user stories with acceptance criteria
4. `developer_agent.py` - Generates technical tasks with time estimates
5. `qa_lead_agent.py` - Orchestrates QA sub-agents for test generation (optional)

**LLM Provider Support**: 
- Local LLM via Ollama (recommended for cost savings, Qwen2.5:32B recommended)
- Cloud providers: OpenAI, Grok (xAI)
- Configuration managed through `utils/settings_manager.py`
- **Template System**: Comprehensive prompt template system with variable validation and proper context injection

### Key Directories

- `agents/` - AI agent implementations with base agent class
- `agents/qa/` - QA-specific sub-agents for test management
- `supervisor/` - Workflow orchestration and stage management
- `frontend/src/` - React application with screens, components, and services
- `utils/` - Shared utilities including LLM client management
- `config/` - Configuration files and settings management
- `tools/` - Development and debugging scripts
- `prompts/` - Agent prompt templates

### Database & Configuration

**Database**: SQLite database (`db.py`) for job tracking and user settings persistence.

**Configuration**: YAML-based configuration (`config/settings.yaml`) with support for:
- Agent settings and timeouts
- Work item limits and presets (small/medium/large/unlimited)
- Parallel processing configuration
- QA test organization requirements

**Settings Management**: User-specific settings stored in database with fallback to system defaults, managed through the frontend Settings page.

### Azure DevOps Integration

**🔄 Outbox Pattern Architecture (NEW - August 2025)**: Enterprise-grade integration with zero data loss:
- **Local Staging**: All work items stored in SQLite before upload (`models/work_item_staging.py`)
- **Resumable Uploads**: Failed items can be retried without regenerating content (`integrators/outbox_uploader.py`)
- **Cascading Failure Prevention**: Individual failures don't affect other work items
- **HTTP Reliability**: Timeouts (30s/60s), retry logic (3x exponential backoff), rate limiting (100ms)
- **Management Tools**: Comprehensive retry utilities (`tools/retry_failed_uploads.py`)
- **Performance**: Protects 2-hour generation investment, enables selective retry of failed items

Full integration with Azure DevOps Test Management API:
- Creates proper work item hierarchy (Epic → Feature → User Story → Task/Test Case)
- Automatic parent-child linking and area path management
- Test plan, test suite, and test case creation with requirement-based organization
- Bulk operations and cleanup utilities in `tools/` directory

### Development Patterns

**Error Handling**: Robust error handling with fail-fast approach. Fallback mechanisms removed in favor of proper error reporting to prevent creation of generic work items.

**Parallel Processing**: Configurable parallel execution for agent stages with rate limiting and worker pool management.

**Real-time Updates**: Server-Sent Events (SSE) for live progress updates during backlog generation.

**Flexible Testing Generation**: Users can choose to generate work items only (~15-30 minutes) or include full testing artifacts (~45-90 minutes) based on project needs.

**Testing**: Extensive test suite in `tools/` directory for individual components, integration testing, and Azure DevOps connectivity validation.

## Recent Fixes and Current Status

### Major System Overhaul (August 1-2, 2025)

#### **Critical System Fixes**
- **Epic Generation**: Fixed template system to generate vision-specific epics instead of generic "Backlog Automation" items
- **Database Integrity**: Added foreign key constraints, validation methods, and repair functionality
- **API Server Cleanup**: Removed 277 lines of duplicate code and fixed import errors
- **Agent Architecture**: Implemented timeout handling, circuit breaker pattern, and comprehensive error recovery
- **Execution Time Display**: Fixed timing calculation and notification system to show accurate job duration

#### **AI Agent Improvements**
- **Prompt Optimization**: Streamlined user story prompt from 71 to 36 lines for Qwen2.5:32B compatibility
- **JSON Compliance**: Achieved 100% proper JSON format generation, eliminating fallback dependencies
- **Template System**: Comprehensive prompt template system with variable validation and context injection
- **QA Agent Template Issues**: Resolved missing template variables causing test plan, suite, and case generation failures
- **Agent Calling Patterns**: Corrected base agent `run()` method usage across all QA agents

#### **Fallback System Overhaul**
- **BREAKING CHANGE**: Removed all fallback methods to prevent generic work item generation
- **Fail-Fast Approach**: Agents now fail clearly instead of generating meaningless content
- **Quality Assurance**: No more generic "Core System Implementation" fallbacks
- **Template Validation**: Failures now raise PromptError exceptions instead of using fallbacks
- **JSON Parsing**: Failures cause skipping instead of generating generic content

#### **Performance & Configuration**
- **Parallel Processing**: Disabled to eliminate race conditions and improve reliability
- **Configuration Management**: Added validation and precedence handling in settings manager
- **Unicode Fixes**: Resolved character encoding issues for Windows environments
- **JSON Extraction**: Added robust utility for handling various LLM response formats

#### **Testing & Validation Improvements**
- **Comprehensive Test Suite**: Added validation test suite and fix utilities in tools directory
- **Agent Quality Compliance**: Implemented compliance validation for acceptance criteria formatting
- **Backlog Sweeper Validation**: Enhanced validation for orphaned work items and completeness
- **JSON Parsing Resilience**: Improved parsing to handle various response formats from different LLM models
- **Acceptance Criteria Validation**: Enhanced generation and formatting of user story acceptance criteria

#### **Work Items vs Testing Toggle Feature (August 3, 2025)**
- **Frontend Enhancement**: Added `includeTestArtifacts` toggle in project creation form with visual processing time feedback
- **Backend Implementation**: Conditional QA stage execution based on user preference in `supervisor/supervisor.py`
- **Performance Optimization**: Users can choose work items only (~15-30 minutes) vs full testing (~45-90 minutes)
- **Workflow Flexibility**: Allows users to generate basic backlog first, then add testing artifacts later if needed
- **API Integration**: `CreateProjectRequest` model updated to support testing preference throughout the pipeline

### Current Limitations
- **Performance**: Individual LLM calls take 30+ seconds, full workflow can take 15-90 minutes depending on options
- **Error Recovery**: Limited retry mechanisms for transient failures
- **Test Coverage**: Core workflow verified but needs comprehensive automated testing
- **Load Testing**: Not tested with large projects (100+ work items)
- **User Experience**: Progress feedback improved with testing toggle option

### Production Readiness Roadmap
1. **Performance Optimization**: Implement caching, parallel processing improvements
2. **Comprehensive Testing**: End-to-end automated test suite
3. **Error Handling**: Enhanced retry logic and graceful degradation
4. **Monitoring**: Add application performance monitoring and alerting
5. **User Testing**: Validate with real business scenarios and user feedback