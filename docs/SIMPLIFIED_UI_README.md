# Simplified UI Implementation

## Overview
The UI has been simplified to require only **4 essential fields** from the user, with all other information automatically extracted by AI or set to sensible defaults.

## Required User Inputs

### 1. **Vision Statement** (Comprehensive)
- A single, comprehensive text field where users describe their entire product vision
- Should include: goals, objectives, target audience, success metrics, and key features
- Example: "Create a comprehensive ride-sharing platform that connects drivers and passengers with real-time matching, secure payments, and intelligent routing. Target urban commuters and part-time drivers seeking flexible income. Success measured by: 50K+ active users in 6 months, 90%+ ride completion rate, $2M+ annual revenue."

### 2. **Azure DevOps Project**
- Format: `organization/project` or just `project-name`
- Examples: `myorg/myproject`, `myproject`
- The organization URL is automatically constructed

### 3. **Area Path**
- The Azure DevOps area path where work items will be created
- Examples: `Grit`, `Data Visualization`, `Product Development`

### 4. **Iteration Path**
- The Azure DevOps iteration/sprint where work items will be assigned
- Examples: `Sprint 1`, `Backlog`, `Release 1.0`

## Auto-Generated/Default Fields

### Automatically Extracted by AI from Vision Statement:
- **Business Objectives**: Extracted from the vision statement
- **Success Metrics**: Extracted from the vision statement  
- **Target Audience**: Extracted from the vision statement
- **Project Description**: Derived from vision statement

### Default Values:
- **Project Name**: "AI Generated Project"
- **Domain**: "software_development"
- **Personal Access Token**: Loaded from `.env` file (`AZURE_DEVOPS_PAT`)
- **Organization URL**: Constructed from project input

## Files Changed

### Frontend:
- `frontend/src/components/forms/SimplifiedProjectForm.tsx` - Main simplified form
- `frontend/src/screens/project/SimpleProjectWizard.tsx` - Simplified wizard screen
- `frontend/src/App.tsx` - Updated routing to use simplified wizard

### Backend:
- `api_server.py` - Updated models to make fields optional/default
- Added support for loading PAT from environment if not provided

### Testing:
- `tools/test_minimum_fields.py` - Validation of minimum required fields

## Usage

1. **Start the application**:
   ```
   npm start (frontend)
   python api_server.py (backend)
   ```

2. **Navigate to**: `http://localhost:3000/project/new`

3. **Fill in only 4 fields**:
   - Vision Statement (comprehensive)
   - Azure DevOps Project
   - Area Path
   - Iteration Path

4. **Click "Generate Agile Backlog"** - Everything else is handled automatically

## Legacy Support

The original multi-step wizard is still available at `/project/wizard` for reference, but the simplified version at `/project/new` is now the default.

## Benefits

- **Reduced complexity**: 4 fields instead of 15+ fields
- **Faster setup**: Single form instead of multi-step wizard
- **Better UX**: Users only need to focus on their vision and ADO basics
- **AI-powered**: Leverages AI to extract objectives, metrics, and audience from vision
- **Sensible defaults**: All other fields use appropriate defaults

## Next Steps

1. Test the simplified UI with a real end-to-end scenario
2. Verify all test artifacts are created in Azure DevOps
3. Optional: Remove constraints or set to `null` in `config/settings.yaml` for production
