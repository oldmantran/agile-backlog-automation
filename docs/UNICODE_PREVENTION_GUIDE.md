# Unicode Encoding Prevention Guide

## Problem Summary
Windows console uses cp1252 encoding by default, which cannot display Unicode characters like emojis (❌, ✅, 🔍). This causes `UnicodeEncodeError` exceptions when code tries to print or log these characters.

## Root Causes
1. **Developer/AI Habit**: Adding "pretty" emojis to logging statements
2. **Import Chain Issues**: Unicode characters in imported modules cause errors
3. **Windows Console Limitation**: cp1252 encoding can't handle Unicode
4. **Runtime-Only Detection**: Errors only appear when code executes, not during static analysis

## Prevention Strategy

### 1. Use Safe Logging (MANDATORY)
```python
# ❌ NEVER do this
print("✅ Operation successful")
logger.info("❌ Operation failed")

# ✅ ALWAYS do this
from utils.safe_logger import get_safe_logger, safe_print

logger = get_safe_logger(__name__)
logger.info("Operation successful")  # Automatically converts to [SUCCESS]
safe_print("Operation failed")       # Automatically converts to [ERROR]
```

### 2. Code Review Checklist
Before committing any code, check for:
- [ ] No emojis in print() statements
- [ ] No emojis in logging statements
- [ ] No emojis in error messages
- [ ] No emojis in docstrings or comments
- [ ] Use `get_safe_logger()` instead of direct `logging.getLogger()`

### 3. Pre-commit Hook
Add this to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Check for Unicode emojis in Python files
if git diff --cached --name-only | grep '\.py$' | xargs grep -l '[❌✅⚠️🔍🤖📋📦💰📤📊🔄📥🛡️🚨💨🔧]'; then
    echo "ERROR: Unicode emojis found in Python files. Use ASCII equivalents."
    echo "Replace with: [ERROR], [SUCCESS], [WARNING], etc."
    exit 1
fi
```

### 4. IDE Configuration
**VS Code settings.json:**
```json
{
    "files.encoding": "utf8",
    "python.terminal.executeInFileDir": false,
    "python.defaultInterpreterPath": "python",
    "terminal.integrated.env.windows": {
        "PYTHONIOENCODING": "utf-8"
    }
}
```

### 5. Automated Detection
Run this command to find existing Unicode issues:
```bash
python tools/detect_unicode_issues.py
```

## Emergency Fix Process
When Unicode errors occur:

1. **Immediate Fix**: Replace emojis with ASCII equivalents
2. **Source Location**: Check the full traceback to find the exact file/line
3. **Safe Replacement**: Use the `UNICODE_REPLACEMENTS` mapping in `safe_logger.py`
4. **Test**: Run the failing operation again to verify fix
5. **Prevention**: Update the file to use `safe_logger`

## ASCII Replacement Table
| Emoji | ASCII Replacement |
|-------|------------------|
| ❌     | [ERROR]          |
| ✅     | [SUCCESS]        |
| ⚠️     | [WARNING]        |
| 🔍     | [SEARCH]         |
| 🤖     | [AI]             |
| 📋     | [CONFIG]         |
| 📦     | [PACKAGE]        |
| 💰     | [COST]           |
| 🔄     | [RETRY]          |
| 🛡️     | [SECURITY]       |

## Long-term Solution
Consider migrating to UTF-8 console encoding:
```python
# Add to main application startup
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

However, the safe logging approach is more reliable across all environments.