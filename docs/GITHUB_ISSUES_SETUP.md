# GitHub Issues Bulk Creator

This script automatically creates 18 GitHub issues for all the problems and improvements identified in the comprehensive application analysis.

## Prerequisites

1. **Python 3.8+** installed on your system
2. **GitHub Personal Access Token** with repository permissions
3. **Repository access** to the target GitHub repository

## Setup Instructions

### 1. Create GitHub Personal Access Token

You can use either a **Classic** or **Fine-grained** personal access token:

#### Option A: Classic Personal Access Token (Recommended)
1. Go to GitHub.com and sign in
2. Click your profile picture → Settings
3. Scroll down to "Developer settings" (bottom left)
4. Click "Personal access tokens" → "Tokens (classic)"
5. Click "Generate new token" → "Generate new token (classic)"
6. Give it a name like "Agile Backlog Issues Creator"
7. Select scopes:
   - ✅ `repo` (Full control of private repositories)
8. Click "Generate token"
9. **Copy the token** (starts with `ghp_`)

#### Option B: Fine-grained Personal Access Token
1. Go to GitHub.com and sign in
2. Click your profile picture → Settings
3. Scroll down to "Developer settings" (bottom left)
4. Click "Personal access tokens" → "Fine-grained tokens"
5. Click "Generate new token"
6. Give it a name like "Agile Backlog Issues Creator"
7. Set expiration as needed
8. Select repository access:
   - ✅ "Only select repositories" → Choose your target repository
9. Set permissions:
   - ✅ **Repository permissions** → **Issues** → **Read and write**
   - ✅ **Repository permissions** → **Metadata** → **Read-only**
10. Click "Generate token"
11. **Copy the token** (starts with `github_pat_`)

### 2. Set Environment Variable

#### Windows (Command Prompt)
```cmd
set GITHUB_TOKEN=your_actual_token_here
```

#### Windows (PowerShell)
```powershell
$env:GITHUB_TOKEN="your_actual_token_here"
```

#### Windows (Permanent - System Properties)
1. Right-click "This PC" → Properties
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `GITHUB_TOKEN`
6. Variable value: `your_actual_token_here`
7. Click OK

#### macOS/Linux
```bash
export GITHUB_TOKEN=your_actual_token_here
```

**Important:** Replace `your_actual_token_here` with your actual token (starts with `ghp_` or `github_pat_`)

### 3. Run the Script

#### Option 1: Use the Batch File (Windows)
```cmd
create_github_issues.bat
```

#### Option 2: Run Python Script Directly
```bash
python create_github_issues.py
```

## What the Script Does

The script will create 18 GitHub issues with the following categories:

### 🚨 Critical Issues (5)
1. **Fix Navigation Route Inconsistency** - Mixed route naming
2. **Implement API Authentication** - Exposed API endpoints
3. **Add Automated Testing Suite** - No tests
4. **Add Error Handling for WebSocket Connections** - Poor error handling
5. **Implement User Authentication System** - Hardcoded user email

### ⚠️ Important Issues (13)
6. **Add Frontend Build Process** - Missing production build
7. **Implement Health Check Endpoint** - No backend validation
8. **Improve Unicode Handling** - Database character replacement
9. **Add Loading States** - Missing async operation feedback
10. **Implement Offline Mode** - No offline functionality
11. **Add Input Validation** - Limited form validation
12. **Implement Progress Persistence** - Lost progress on refresh
13. **Optimize Bundle Size** - Large frontend dependencies
14. **Implement Caching Strategy** - No API response caching
15. **Secure Environment Variables** - Exposed configuration
16. **Implement Error Monitoring** - No centralized logging
17. **Add API Documentation** - Missing OpenAPI docs
18. **Create User Guide** - No user documentation

## Issue Format

Each issue includes:
- **Clear title** describing the problem
- **Detailed description** with problem, impact, and location
- **Acceptance criteria** as checkboxes
- **Appropriate labels** for categorization
- **Recommendations** for fixing the issue

## Labels Used

- `bug` - Actual bugs that need fixing
- `critical` - High priority issues
- `enhancement` - Improvements and new features
- `security` - Security-related issues
- `frontend` - Frontend-specific issues
- `backend` - Backend-specific issues
- `documentation` - Documentation issues
- `testing` - Testing-related issues
- `performance` - Performance improvements
- `ux` - User experience improvements

## Troubleshooting

### "GITHUB_TOKEN environment variable not set"
- Make sure you've set the environment variable correctly
- Try setting it in the same terminal session where you run the script
- Verify you're using the actual token, not placeholder text

### "Token is invalid or expired"
- Check that your token is correct and hasn't expired
- For fine-grained tokens, ensure "Issues" permission is set to "Read and write"
- For classic tokens, ensure "repo" scope is selected

### "No access to repository"
- Verify you have access to the repository
- For fine-grained tokens, make sure the repository is selected in token settings
- Check that the repository name is spelled correctly

### "Failed to create issue"
- Check that your token has the correct permissions
- Verify you have access to the repository
- Ensure the repository exists and is spelled correctly

### "Rate limit exceeded"
- GitHub has rate limits for API calls
- The script includes delays to avoid this
- If you hit the limit, wait an hour and try again

### "Repository not found"
- Check the repository name spelling
- Ensure you have access to the repository
- Verify the repository is not private (or your token has private repo access)

## Token Types Comparison

| Feature | Classic Token | Fine-grained Token |
|---------|---------------|-------------------|
| Format | `ghp_...` | `github_pat_...` |
| Permissions | Broad scopes | Granular permissions |
| Repository Access | All repos or specific repos | Specific repositories only |
| Required Permissions | `repo` scope | `Issues: Read and write` |
| Security | Less secure | More secure |

## Manual Alternative

If you prefer to create issues manually, you can copy the issue content from the `create_github_issues.py` file. Each issue is defined in the `get_issues_data()` method with:
- `title`: Issue title
- `body`: Full issue description
- `labels`: Array of labels

## Security Note

- Keep your GitHub token secure
- Don't commit the token to version control
- Fine-grained tokens are more secure than classic tokens
- Delete the token after creating the issues if you don't need it anymore
- Set appropriate expiration dates for your tokens

## Support

If you encounter any issues with the script, please:
1. Check the troubleshooting section above
2. Verify your GitHub token has the correct permissions
3. Ensure you have access to the target repository
4. Check that Python and the requests module are properly installed
5. For fine-grained tokens, ensure "Issues" permission is enabled 