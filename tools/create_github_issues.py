#!/usr/bin/env python3
"""
GitHub Issues Bulk Creator for Agile Backlog Automation

This script creates GitHub issues for all the problems and improvements identified
in the comprehensive application analysis.
"""

import os
import requests
import json
import re
from typing import List, Dict, Any
from datetime import datetime

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📁 Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value
        print("✅ Environment variables loaded")
    else:
        print(f"⚠️  {env_file} file not found, using system environment variables")

class GitHubIssueCreator:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
    
    def validate_token(self) -> bool:
        """Validate the GitHub token by making a test API call."""
        try:
            response = requests.get(
                'https://api.github.com/user',
                headers=self.headers
            )
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Token validated successfully for user: {user_data.get('login', 'Unknown')}")
                return True
            elif response.status_code == 401:
                print("❌ Token is invalid or expired")
                return False
            else:
                print(f"❌ Token validation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error validating token: {e}")
            return False
    
    def test_repository_access(self) -> bool:
        """Test if the token has access to the specified repository."""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.owner}/{self.repo}",
                headers=self.headers
            )
            if response.status_code == 200:
                repo_data = response.json()
                print(f"✅ Repository access confirmed: {repo_data.get('full_name', 'Unknown')}")
                return True
            elif response.status_code == 404:
                print(f"❌ Repository not found: {self.owner}/{self.repo}")
                return False
            elif response.status_code == 403:
                print(f"❌ No access to repository: {self.owner}/{self.repo}")
                return False
            else:
                print(f"❌ Repository access test failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error testing repository access: {e}")
            return False
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a single GitHub issue."""
        data = {
            'title': title,
            'body': body
        }
        if labels:
            data['labels'] = labels
        
        response = requests.post(
            f"{self.base_url}/issues",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 201:
            issue = response.json()
            print(f"✅ Created issue #{issue['number']}: {title}")
            return issue
        else:
            print(f"❌ Failed to create issue '{title}': {response.status_code} - {response.text}")
            return None
    
    def create_all_issues(self):
        """Create all issues from the analysis."""
        # Validate token and repository access first
        print("🔍 Validating GitHub token and repository access...")
        if not self.validate_token():
            print("❌ Token validation failed. Please check your token.")
            return []
        
        if not self.test_repository_access():
            print("❌ Repository access failed. Please check repository name and permissions.")
            return []
        
        issues = self.get_issues_data()
        
        print(f"🚀 Creating {len(issues)} issues in {self.owner}/{self.repo}")
        print("=" * 60)
        
        created_issues = []
        for i, issue_data in enumerate(issues, 1):
            print(f"Creating issue {i}/{len(issues)}...")
            issue = self.create_issue(
                title=issue_data['title'],
                body=issue_data['body'],
                labels=issue_data['labels']
            )
            if issue:
                created_issues.append(issue)
            
            # Rate limiting - GitHub allows 5000 requests per hour for authenticated users
            # Adding small delay to be safe
            import time
            time.sleep(1)
        
        print("=" * 60)
        print(f"✅ Successfully created {len(created_issues)} issues")
        return created_issues
    
    def get_issues_data(self) -> List[Dict[str, Any]]:
        """Get all issues data from the analysis."""
        return [
            {
                "title": "FEATURE: Implement Agent Learning System for Continuous Improvement",
                "body": '''## 🧠 FEATURE: Agent Learning System for Continuous Improvement

### Problem Statement
The current agentic backlog generator has sophisticated multi-agent architecture with quality assessment and improvement loops, but agents don't learn from past experiences. This leads to:
- Agents making the same mistakes repeatedly
- No improvement in performance over time
- Wasted resources on repeated improvement cycles
- Lack of domain-specific learning and optimization

### Current State
- ✅ Multi-agent system with specialized agents (Epic Strategist, Feature Decomposer, User Story Decomposer, Developer Agent, QA Lead)
- ✅ Quality assessment and improvement mechanisms
- ✅ Circuit breaker pattern and timeout handling
- ✅ Quality metrics tracking
- ❌ No learning from past experiences
- ❌ No pattern recognition for success/failure
- ❌ No continuous improvement based on historical data

### Proposed Solution: Agent Learning Architecture

#### 1. Agent Memory & Learning Database
Create a new database schema to store agent learning experiences:

**Tables:**
- `agent_learning_experiences` - Records of all agent executions with outcomes
- `agent_learning_patterns` - Identified success/failure patterns and strategies

**Key Fields:**
- Agent name, task type, domain
- Input context, output quality metrics
- Improvement attempts and strategies used
- Final outcome and lessons learned
- Performance metrics and context analysis

#### 2. Enhanced Base Agent with Learning
Modify `agents/base_agent.py` to include:
- Learning memory integration
- Experience recording capabilities
- Learning insights retrieval
- Prompt enhancement with historical learnings

**New Methods:**
- `_record_learning_experience()` - Store execution results
- `_get_learning_insights()` - Retrieve relevant learnings
- `_enhance_prompt_with_learning()` - Improve prompts with insights

#### 3. Learning-Enhanced Quality Assessment
Enhance `utils/quality_metrics_tracker.py` to:
- Record complete improvement cycles
- Extract lessons learned from failures
- Track improvement strategy effectiveness
- Generate learning recommendations

#### 4. Integration with Existing Agents
Update all specialized agents to:
- Record learning experiences during quality improvement cycles
- Use learning insights to enhance prompts
- Apply proven strategies from past successes
- Avoid repeating common failure patterns

#### 5. Learning Dashboard & Analytics
Create `tools/agent_learning_dashboard.py` for:
- Learning progress monitoring
- Performance trend analysis
- Strategy effectiveness tracking
- Actionable improvement recommendations

### Implementation Details

#### Database Schema
```sql
-- Learning experiences table
CREATE TABLE agent_learning_experiences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    domain TEXT NOT NULL,
    input_context TEXT NOT NULL,  -- JSON
    output_quality TEXT NOT NULL,  -- JSON
    improvement_attempts TEXT NOT NULL,  -- JSON
    final_outcome TEXT NOT NULL,
    lessons_learned TEXT NOT NULL,  -- JSON array
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- Performance metrics
    initial_score INTEGER,
    final_score INTEGER,
    improvement_count INTEGER,
    total_duration_seconds REAL,
    
    -- Context analysis
    context_length INTEGER,
    domain_specificity REAL,
    vision_clarity_score REAL
);

-- Learning patterns table
CREATE TABLE agent_learning_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    domain TEXT NOT NULL,
    pattern_type TEXT NOT NULL,  -- 'success_pattern', 'failure_pattern', 'improvement_strategy'
    pattern_data TEXT NOT NULL,  -- JSON
    confidence_score REAL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### Learning Experience Structure
```python
@dataclass
class LearningExperience:
    agent_name: str
    task_type: str  # 'epic', 'feature', 'user_story', 'task'
    domain: str
    input_context: Dict[str, Any]
    output_quality: Dict[str, Any]
    improvement_attempts: List[Dict[str, Any]]
    final_outcome: str  # 'success', 'partial_success', 'failure'
    lessons_learned: List[str]
    timestamp: datetime
```

#### Prompt Enhancement Example
```python
def _enhance_prompt_with_learning(self, base_prompt: str, task_type: str, 
                                domain: str = None, context: Dict[str, Any] = None) -> str:
    insights = self._get_learning_insights(task_type, domain)
    
    enhanced_prompt = f"""
{base_prompt}

## LEARNING-BASED IMPROVEMENTS
Based on analysis of {insights['insights']['total_experiences']} previous experiences:

{self._build_learning_instructions(insights, context)}

## PREVIOUS SUCCESS PATTERNS
{self._format_success_patterns(insights)}

## COMMON PITFALLS TO AVOID
{self._format_failure_patterns(insights)}

Please apply these learnings to improve your output quality.
"""
    return enhanced_prompt
```

### Key Benefits

1. **Pattern Recognition**: Agents learn from successful and failed attempts
2. **Continuous Improvement**: Each experience makes the agent smarter
3. **Domain-Specific Learning**: Agents learn industry-specific best practices
4. **Failure Prevention**: Avoid repeating common mistakes
5. **Strategy Optimization**: Learn which improvement approaches work best
6. **Performance Tracking**: Monitor learning progress over time

### Implementation Steps

1. **Phase 1: Core Infrastructure**
   - [ ] Create `utils/agent_learning_memory.py`
   - [ ] Implement database schema and tables
   - [ ] Create `LearningExperience` data class
   - [ ] Implement basic CRUD operations

2. **Phase 2: Base Agent Enhancement**
   - [ ] Modify `agents/base_agent.py`
   - [ ] Add learning memory integration
   - [ ] Implement experience recording methods
   - [ ] Add prompt enhancement capabilities

3. **Phase 3: Quality Assessment Integration**
   - [ ] Enhance `utils/quality_metrics_tracker.py`
   - [ ] Integrate learning experience recording
   - [ ] Implement lessons learned extraction
   - [ ] Add improvement strategy tracking

4. **Phase 4: Agent Updates**
   - [ ] Update `agents/developer_agent.py`
   - [ ] Update `agents/user_story_decomposer_agent.py`
   - [ ] Update `agents/feature_decomposer_agent.py`
   - [ ] Update `agents/epic_strategist.py`

5. **Phase 5: Learning Dashboard**
   - [ ] Create `tools/agent_learning_dashboard.py`
   - [ ] Implement trend analysis
   - [ ] Add performance monitoring
   - [ ] Create actionable recommendations

6. **Phase 6: Testing & Validation**
   - [ ] Test with sample vision statements
   - [ ] Validate learning database population
   - [ ] Verify prompt enhancement effectiveness
   - [ ] Measure performance improvements

### Technical Requirements

- **Database**: SQLite with new learning tables
- **Dependencies**: No additional external dependencies
- **Performance**: Minimal impact on existing agent execution
- **Compatibility**: Works with all existing LLM providers
- **Scalability**: Efficient querying for large learning datasets

### Success Metrics

- [ ] Reduction in improvement cycles required
- [ ] Increase in first-attempt quality scores
- [ ] Decrease in common failure patterns
- [ ] Improvement in domain-specific performance
- [ ] Positive learning trend over time

### Files to Create/Modify

**New Files:**
- `utils/agent_learning_memory.py` - Core learning system
- `tools/agent_learning_dashboard.py` - Learning analytics

**Modified Files:**
- `agents/base_agent.py` - Add learning capabilities
- `utils/quality_metrics_tracker.py` - Integrate learning recording
- `agents/developer_agent.py` - Use learning insights
- `agents/user_story_decomposer_agent.py` - Use learning insights
- `agents/feature_decomposer_agent.py` - Use learning insights
- `agents/epic_strategist.py` - Use learning insights

### Labels
- `enhancement`
- `feature`
- `ai-learning`
- `agent-improvement`
- `performance`
- `database`
- `architecture`''',
                "labels": ["enhancement", "feature", "ai-learning", "agent-improvement", "performance", "database", "architecture"]
            },
            {
                "title": "CRITICAL: Navigation to My Projects Screen Not Working After Backlog Generation",
                "body": """## 🚨 CRITICAL: Navigation Failure After Backlog Generation

### Problem
After submitting a product vision and starting backlog generation, the application does not automatically navigate to the My Projects screen as expected. Users remain stuck on the project creation screen.

### Impact
- Users cannot monitor backlog generation progress
- Poor user experience - users think the system is broken
- Users manually navigate to My Projects screen
- Critical workflow interruption

### Current Behavior
- Project creation succeeds
- Backlog generation API call is made
- Success message shows for 2 seconds
- Navigation to `/my-projects` fails or doesn't happen
- User remains on project creation screen

### Expected Behavior
- After successful backlog generation start
- Immediate navigation to My Projects screen
- Show progress bar and server logs
- Allow user to monitor generation progress

### Location
- `frontend/src/screens/project/SimpleProjectWizard.tsx` (lines 70-90)
- Navigation logic in `handleSubmit` function

### Root Cause
- Navigation timeout may be failing
- React Router navigation may not be working properly
- Success state may not be triggering correctly

### Acceptance Criteria
- [ ] Navigation to My Projects screen happens immediately after backlog generation starts
- [ ] No 2-second delay - navigate immediately
- [ ] Fallback navigation works if React Router fails
- [ ] User sees progress bar and server logs on My Projects screen
- [ ] No manual navigation required

### Labels
- `bug`
- `critical`
- `frontend`
- `navigation`
- `user-experience`""",
                "labels": ["bug", "critical", "frontend", "navigation", "user-experience"]
            },
            {
                "title": "CRITICAL: My Projects Screen Not Showing Progress Bar and Server Logs",
                "body": """## 🚨 CRITICAL: My Projects Screen Missing Progress and Logs

### Problem
When navigating to the My Projects screen (either automatically or manually), the progress bar for active backlog generation and server logs are not displayed, even when jobs are running.

### Impact
- Users cannot monitor backlog generation progress
- No visibility into server logs and processing status
- Users think the system is not working
- Critical monitoring functionality broken

### Current Behavior
- My Projects screen loads
- No progress bar visible for active jobs
- Server Logs component not showing
- No indication that backlog generation is running
- API calls may be failing silently

### Expected Behavior
- My Projects screen shows progress bar for active jobs
- Server Logs component displays real-time backend logs
- Active jobs are visible and updating
- Clear indication of running processes

### Location
- `frontend/src/screens/project/MyProjectsScreen.tsx`
- `frontend/src/components/logs/ServerLogs.tsx`
- API calls to `/api/jobs` and `/api/backlog/status/{job_id}`

### Root Cause
- API calls may be failing due to network issues
- Server Logs component may not be rendering
- Active jobs not being loaded from localStorage or API
- WebSocket connection may not be established

### Acceptance Criteria
- [ ] Progress bar shows for active backlog generation jobs
- [ ] Server Logs component displays and connects to WebSocket
- [ ] Active jobs are loaded and displayed correctly
- [ ] Real-time updates work for job progress
- [ ] Error handling shows clear messages if components fail

### Labels
- `bug`
- `critical`
- `frontend`
- `monitoring`
- `user-experience`""",
                "labels": ["bug", "critical", "frontend", "monitoring", "user-experience"]
            },
            {
                "title": "Fix Navigation Route Inconsistency",
                "body": """## 🚨 Critical Issue: Navigation Route Inconsistency

### Problem
The application has inconsistent route naming between `/my-projects` and `/projects`, which can cause navigation failures.

### Impact
- Users may experience navigation failures
- Inconsistent user experience
- Potential broken links

### Current State
- `App.tsx` defines `/my-projects` route
- `SimpleProjectWizard.tsx` navigates to `/my-projects`
- `MyProjectsScreen.tsx` has individual project links to `/projects/{id}`

### Location
- `frontend/src/App.tsx`
- `frontend/src/screens/project/SimpleProjectWizard.tsx`
- `frontend/src/screens/project/MyProjectsScreen.tsx`

### Recommendation
Standardize on `/my-projects` for the main projects list and keep `/projects/{id}` for individual project details.

### Acceptance Criteria
- [ ] All navigation uses consistent route naming
- [ ] No broken links in the application
- [ ] Individual project details use `/projects/{id}` format
- [ ] Main projects list uses `/my-projects` format

### Labels
- `bug`
- `critical`
- `frontend`
- `navigation`""",
                "labels": ["bug", "critical", "frontend", "navigation"]
            },
            {
                "title": "Add Error Handling for WebSocket Connections",
                "body": """## ⚠️ Issue: Missing Error Handling in WebSocket Connection

### Problem
`ServerLogs` component doesn't handle WebSocket connection failures gracefully, which can lead to poor user experience when the backend is not running.

### Impact
- Users may not see server logs if backend is not running
- No feedback when connection fails
- Poor user experience

### Location
`frontend/src/components/logs/ServerLogs.tsx`

### Current Behavior
- WebSocket attempts to connect but fails silently
- No user feedback about connection status
- Users may think the application is broken

### Recommendation
Add better error handling and user feedback for WebSocket connection issues.

### Acceptance Criteria
- [ ] Clear error messages when WebSocket connection fails
- [ ] Automatic retry mechanism with exponential backoff
- [ ] Visual indicators for connection status
- [ ] Graceful degradation when backend is unavailable
- [ ] User-friendly error messages

### Labels
- `enhancement`
- `frontend`
- `websocket`
- `error-handling`""",
                "labels": ["enhancement", "frontend", "websocket", "error-handling"]
            },
            {
                "title": "Implement User Authentication System",
                "body": """## ⚠️ Issue: Hardcoded User Email

### Problem
`MyProjectsScreen.tsx` has hardcoded user email `kevin.tran@c4workx.com`, which means the application only works for one user.

### Impact
- Only works for one user
- No multi-user support
- Security concerns with hardcoded credentials

### Location
`frontend/src/screens/project/MyProjectsScreen.tsx:48`

### Current State
```typescript
const USER_EMAIL = 'kevin.tran@c4workx.com'; // TODO: Replace with dynamic user email
```

### Recommendation
Implement proper user authentication and dynamic user email handling.

### Acceptance Criteria
- [ ] User login/logout functionality
- [ ] Session management
- [ ] Dynamic user email handling
- [ ] Secure authentication flow
- [ ] User profile management
- [ ] Multi-user support

### Labels
- `enhancement`
- `security`
- `authentication`
- `frontend`""",
                "labels": ["enhancement", "security", "authentication", "frontend"]
            },
            {
                "title": "Add Frontend Build Process to Quick Start",
                "body": """## ⚠️ Issue: Missing Frontend Build Process

### Problem
`quick_start.bat` doesn't build the frontend for production, which may cause issues with missing development dependencies in production.

### Impact
- Development dependencies may be missing in production
- Potential runtime errors
- Inconsistent deployment behavior

### Location
`quick_start.bat`

### Current State
The script only runs `npm start` which is for development mode.

### Recommendation
Add `npm run build` step before starting the frontend server.

### Acceptance Criteria
- [ ] Add build step to quick_start.bat
- [ ] Ensure production build is created
- [ ] Verify all dependencies are properly bundled
- [ ] Test production build functionality

### Labels
- `enhancement`
- `deployment`
- `frontend`
- `build`""",
                "labels": ["enhancement", "deployment", "frontend", "build"]
            },
            {
                "title": "Implement Health Check Endpoint",
                "body": """## ⚠️ Issue: No Health Check Endpoint

### Problem
Frontend doesn't check if backend is running before making API calls, which can lead to confusing error states.

### Impact
- Users may see errors without knowing the backend is down
- Poor user experience
- Difficult troubleshooting

### Location
Frontend API calls

### Recommendation
Add health check endpoint and frontend validation.

### Acceptance Criteria
- [ ] Add `/api/health` endpoint to backend
- [ ] Frontend checks backend health before making API calls
- [ ] Clear error messages when backend is unavailable
- [ ] Automatic retry mechanism
- [ ] Health status indicators in UI

### Labels
- `enhancement`
- `backend`
- `frontend`
- `monitoring`""",
                "labels": ["enhancement", "backend", "frontend", "monitoring"]
            },
            {
                "title": "Improve Unicode Handling in Database",
                "body": """## ⚠️ Issue: Unicode Handling in Database

### Problem
Database sanitization replaces Unicode characters with text equivalents, which results in loss of visual indicators in stored data.

### Impact
- Loss of visual indicators in stored data
- Poor data quality
- Inconsistent display of special characters

### Location
`db.py:_sanitize_json_for_storage`

### Current Behavior
Unicode characters like ✅, ❌, ⚠️ are replaced with text equivalents like [SUCCESS], [FAILED], [WARNING].

### Recommendation
Use proper UTF-8 encoding instead of character replacement.

### Acceptance Criteria
- [ ] Implement proper UTF-8 encoding
- [ ] Preserve Unicode characters in database
- [ ] Ensure proper display in frontend
- [ ] Test with various Unicode characters
- [ ] Maintain data integrity

### Labels
- `enhancement`
- `backend`
- `database`
- `unicode`""",
                "labels": ["enhancement", "backend", "database", "unicode"]
            },
            {
                "title": "Add Loading States for All Async Operations",
                "body": """## ⚠️ Issue: Missing Loading States

### Problem
Some API calls don't show loading states, which leads to poor user experience during long operations.

### Impact
- Poor user experience during long operations
- Users may think the application is frozen
- No feedback on operation progress

### Location
Various frontend components

### Recommendation
Add loading spinners for all async operations.

### Acceptance Criteria
- [ ] Add loading spinners to all API calls
- [ ] Show progress indicators for long operations
- [ ] Disable buttons during operations
- [ ] Provide clear feedback on operation status
- [ ] Consistent loading UI across components

### Labels
- `enhancement`
- `frontend`
- `ux`
- `loading`""",
                "labels": ["enhancement", "frontend", "ux", "loading"]
            },
            {
                "title": "Implement Offline Mode",
                "body": """## ⚠️ Issue: No Offline Mode

### Problem
Application requires constant backend connection, which means users can't view historical data when backend is down.

### Impact
- Users can't view historical data when backend is down
- Poor user experience during network issues
- No offline functionality

### Location
Frontend components

### Recommendation
Implement offline mode with cached data.

### Acceptance Criteria
- [ ] Cache historical data locally
- [ ] Allow viewing cached data when offline
- [ ] Sync data when connection is restored
- [ ] Clear offline indicators
- [ ] Graceful degradation of functionality

### Labels
- `enhancement`
- `frontend`
- `offline`
- `caching`""",
                "labels": ["enhancement", "frontend", "offline", "caching"]
            },
            {
                "title": "Add Comprehensive Input Validation",
                "body": """## ⚠️ Issue: Missing Input Validation

### Problem
Limited validation on Azure DevOps project input, which can lead to users entering invalid project names.

### Impact
- Users may enter invalid project names
- Potential API errors
- Poor user experience

### Location
`SimplifiedProjectForm.tsx`

### Recommendation
Add comprehensive input validation with helpful error messages.

### Acceptance Criteria
- [ ] Validate Azure DevOps project name format
- [ ] Validate area path and iteration path
- [ ] Provide helpful error messages
- [ ] Real-time validation feedback
- [ ] Prevent form submission with invalid data

### Labels
- `enhancement`
- `frontend`
- `validation`
- `forms`""",
                "labels": ["enhancement", "frontend", "validation", "forms"]
            },
            {
                "title": "Implement Progress Persistence",
                "body": """## ⚠️ Issue: No Progress Persistence

### Problem
Progress is lost if user refreshes page during backlog generation, which means users can't resume interrupted operations.

### Impact
- Users can't resume interrupted operations
- Lost progress on page refresh
- Poor user experience

### Location
Frontend state management

### Recommendation
Persist progress in localStorage or database.

### Acceptance Criteria
- [ ] Save progress to localStorage
- [ ] Restore progress on page reload
- [ ] Resume interrupted operations
- [ ] Clear progress when operation completes
- [ ] Handle progress conflicts

### Labels
- `enhancement`
- `frontend`
- `state-management`
- `persistence`""",
                "labels": ["enhancement", "frontend", "state-management", "persistence"]
            },
            {
                "title": "Optimize Frontend Bundle Size",
                "body": """## ⚠️ Issue: Large Bundle Size

### Problem
Frontend has many dependencies that may not all be needed, which leads to slow initial load times.

### Impact
- Slow initial load times
- Poor performance on slow connections
- Unnecessary bandwidth usage

### Location
`frontend/package.json`

### Recommendation
Audit and remove unused dependencies.

### Acceptance Criteria
- [ ] Audit all dependencies
- [ ] Remove unused packages
- [ ] Implement code splitting
- [ ] Optimize bundle size
- [ ] Measure performance improvements

### Labels
- `enhancement`
- `frontend`
- `performance`
- `optimization`""",
                "labels": ["enhancement", "frontend", "performance", "optimization"]
            },
            {
                "title": "Implement Caching Strategy",
                "body": """## ⚠️ Issue: No Caching Strategy

### Problem
API responses are not cached, which leads to repeated API calls for the same data.

### Impact
- Repeated API calls for same data
- Poor performance
- Unnecessary server load

### Location
Frontend API calls

### Recommendation
Implement caching for static data like project lists.

### Acceptance Criteria
- [ ] Cache static data (project lists, templates)
- [ ] Implement cache invalidation
- [ ] Cache user preferences
- [ ] Optimize cache size
- [ ] Handle cache conflicts

### Labels
- `enhancement`
- `frontend`
- `caching`
- `performance`""",
                "labels": ["enhancement", "frontend", "caching", "performance"]
            },
            {
                "title": "Implement API Authentication",
                "body": """## 🚨 Critical Issue: Exposed API Endpoints

### Problem
No authentication on API endpoints, which means anyone can access the API.

### Impact
- Anyone can access the API
- Security vulnerability
- Potential data exposure

### Location
`unified_api_server.py`

### Recommendation
Implement proper authentication and authorization.

### Acceptance Criteria
- [ ] Implement API key authentication
- [ ] Add user authentication
- [ ] Implement role-based access control
- [ ] Secure sensitive endpoints
- [ ] Add rate limiting

### Labels
- `security`
- `critical`
- `backend`
- `authentication`""",
                "labels": ["security", "critical", "backend", "authentication"]
            },
            {
                "title": "Secure Environment Variables",
                "body": """## ⚠️ Issue: Environment Variables in Frontend

### Problem
API URL is exposed in frontend code, which is a potential security risk.

### Impact
- Potential security risk
- Exposed configuration
- Hard to manage different environments

### Location
`frontend/src/services/api/apiClient.ts`

### Recommendation
Use environment variables properly and validate on backend.

### Acceptance Criteria
- [ ] Use environment variables for configuration
- [ ] Validate configuration on backend
- [ ] Secure sensitive data
- [ ] Support different environments
- [ ] Document configuration requirements

### Labels
- `security`
- `frontend`
- `configuration`
- `environment`""",
                "labels": ["security", "frontend", "configuration", "environment"]
            },
            {
                "title": "Add Automated Testing Suite",
                "body": """## 🚨 Critical Issue: No Automated Tests

### Problem
No unit or integration tests, which means there's no confidence in code changes.

### Impact
- No confidence in code changes
- Potential regressions
- Difficult to maintain code quality

### Location
Entire codebase

### Recommendation
Implement comprehensive test suite.

### Acceptance Criteria
- [ ] Add unit tests for core functions
- [ ] Add integration tests for API endpoints
- [ ] Add frontend component tests
- [ ] Add end-to-end tests
- [ ] Set up CI/CD pipeline with tests

### Labels
- `testing`
- `critical`
- `quality`
- `ci-cd`""",
                "labels": ["testing", "critical", "quality", "ci-cd"]
            },
            {
                "title": "Implement Error Monitoring",
                "body": """## ⚠️ Issue: No Error Monitoring

### Problem
No centralized error logging or monitoring, which means issues may go unnoticed.

### Impact
- Issues may go unnoticed
- Difficult to debug problems
- Poor user experience

### Location
Frontend and backend

### Recommendation
Implement error monitoring and alerting.

### Acceptance Criteria
- [ ] Centralized error logging
- [ ] Error monitoring dashboard
- [ ] Alert notifications
- [ ] Error categorization
- [ ] Performance monitoring

### Labels
- `monitoring`
- `logging`
- `alerting`
- `observability`""",
                "labels": ["monitoring", "logging", "alerting", "observability"]
            },
            {
                "title": "Add API Documentation",
                "body": """## ⚠️ Issue: Missing API Documentation

### Problem
No comprehensive API documentation, which makes it difficult for developers to understand and use the API.

### Impact
- Difficult for developers to understand and use
- Poor developer experience
- Hard to maintain API

### Location
Backend API

### Recommendation
Add OpenAPI/Swagger documentation.

### Acceptance Criteria
- [ ] Generate OpenAPI specification
- [ ] Add Swagger UI
- [ ] Document all endpoints
- [ ] Add request/response examples
- [ ] Keep documentation up to date

### Labels
- `documentation`
- `api`
- `developer-experience`
- `swagger`""",
                "labels": ["documentation", "api", "developer-experience", "swagger"]
            },
            {
                "title": "Create User Guide",
                "body": """## ⚠️ Issue: No User Guide

### Problem
No user documentation, which means users may not know how to use the application effectively.

### Impact
- Users may not know how to use effectively
- Poor user experience
- Increased support requests

### Location
Documentation

### Recommendation
Create comprehensive user guide.

### Acceptance Criteria
- [ ] Create step-by-step user guide
- [ ] Add screenshots and examples
- [ ] Document all features
- [ ] Add troubleshooting section
- [ ] Keep guide up to date

### Labels
- `documentation`
- `user-guide`
- `onboarding`
- `support`""",
                "labels": ["documentation", "user-guide", "onboarding", "support"]
            }
        ]

def main():
    """Main function to create GitHub issues."""
    print("GitHub Issues Bulk Creator for Agile Backlog Automation")
    print("=" * 60)
    
    # Load environment variables from .env file
    load_env_file()
    
    # Get configuration
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nPlease set your GitHub personal access token:")
        print("\nFor Windows (Command Prompt):")
        print("  set GITHUB_TOKEN=your_actual_token_here")
        print("\nFor Windows (PowerShell):")
        print("  $env:GITHUB_TOKEN=\"your_actual_token_here\"")
        print("\nFor macOS/Linux:")
        print("  export GITHUB_TOKEN=your_actual_token_here")
        print("\nToken should look like:")
        print("  - Classic token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print("  - Fine-grained token: github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        return
    
    # Validate token format
    if not (token.startswith('ghp_') or token.startswith('github_pat_')):
        print("❌ Error: Invalid token format")
        print("Token should start with 'ghp_' (classic) or 'github_pat_' (fine-grained)")
        print(f"Your token starts with: {token[:10]}...")
        return
    
    # Show token type
    if token.startswith('ghp_'):
        print("🔑 Using Classic Personal Access Token")
    else:
        print("🔑 Using Fine-grained Personal Access Token")
    
    owner = input("Enter GitHub username/organization: ").strip()
    if not owner:
        print("❌ Error: GitHub username/organization is required")
        return
    
    repo = input("Enter repository name: ").strip()
    if not repo:
        print("❌ Error: Repository name is required")
        return
    
    # Confirm before creating issues
    print(f"\n📋 About to create 18 issues in {owner}/{repo}")
    print("This will create issues for all problems and improvements identified in the analysis.")
    
    confirm = input("\nDo you want to continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    # Create issues
    creator = GitHubIssueCreator(token, owner, repo)
    created_issues = creator.create_all_issues()
    
    # Summary
    if created_issues:
        print(f"\n🎉 Successfully created {len(created_issues)} issues!")
        print("\nCreated issues:")
        for issue in created_issues:
            print(f"  #{issue['number']}: {issue['title']}")
        
        print(f"\nView all issues at: https://github.com/{owner}/{repo}/issues")
    else:
        print("❌ No issues were created. Please check your token and repository access.")
        print("\nTroubleshooting:")
        print("1. Verify your token has 'repo' permissions")
        print("2. Check that you have access to the repository")
        print("3. Ensure the repository name is spelled correctly")
        print("4. For fine-grained tokens, make sure 'Issues' permission is enabled")

if __name__ == "__main__":
    main() 