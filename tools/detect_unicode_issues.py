#!/usr/bin/env python3
"""
Unicode Issue Detection Tool
Scans the codebase for Unicode characters that will cause encoding issues on Windows.
"""

import os
import sys
import re
from typing import List, Tuple, Dict

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.safe_logger import get_safe_logger, safe_print
    logger = get_safe_logger(__name__)
except ImportError:
    # Fallback if safe_logger not available yet
    import logging
    logger = logging.getLogger(__name__)
    def safe_print(msg):
        print(str(msg).encode('ascii', errors='replace').decode('ascii'))

# Common problematic Unicode characters
PROBLEMATIC_UNICODE = {
    '❌': '[ERROR]',
    '✅': '[SUCCESS]',
    '⚠️': '[WARNING]', 
    '🔍': '[SEARCH]',
    '🤖': '[AI]',
    '📋': '[CONFIG]',
    '📦': '[PACKAGE]',
    '💰': '[COST]',
    '📤': '[REQUEST]',
    '📊': '[STATS]',
    '🔄': '[RETRY]',
    '📥': '[DOWNLOAD]',
    '🛡️': '[SECURITY]',
    '🚨': '[ALERT]',
    '💨': '[FAST]',
    '🔧': '[TOOL]',
}

def scan_file_for_unicode(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Scan a file for problematic Unicode characters.
    
    Returns:
        List of (line_number, line_content, problematic_chars)
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Look for actual Unicode emojis, not ASCII replacements
                problematic_chars = []
                for char in line:
                    # Check if character is a Unicode emoji (outside ASCII range)
                    if ord(char) > 127 and char in PROBLEMATIC_UNICODE:
                        problematic_chars.append(char)
                
                if problematic_chars:
                    issues.append((line_num, line.strip(), ''.join(problematic_chars)))
    
    except Exception as e:
        logger.warning(f"Could not scan {file_path}: {e}")
    
    return issues

def scan_directory(directory: str, extensions: List[str] = ['.py']) -> Dict[str, List[Tuple[int, str, str]]]:
    """Scan directory for Unicode issues in files with given extensions."""
    all_issues = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip common non-source directories and third-party libraries
        dirs[:] = [d for d in dirs if d not in [
            '.git', '__pycache__', 'node_modules', '.vscode', 
            '.venv', 'venv', 'env', 'site-packages', 'Lib'
        ]]
        
        # Skip third-party library paths
        if any(skip_dir in root for skip_dir in ['.venv', 'site-packages', 'Lib\\site-packages']):
            continue
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                issues = scan_file_for_unicode(file_path)
                if issues:
                    all_issues[file_path] = issues
    
    return all_issues

def generate_fix_suggestions(issues: Dict[str, List[Tuple[int, str, str]]]) -> str:
    """Generate fix suggestions for the found issues."""
    suggestions = []
    
    for file_path, file_issues in issues.items():
        suggestions.append(f"\nFile: {file_path}")
        suggestions.append("=" * (len(file_path) + 6))
        
        for line_num, line_content, unicode_chars in file_issues:
            suggestions.append(f"  Line {line_num}: {unicode_chars}")
            suggestions.append(f"    Current: {line_content}")
            
            # Generate fix suggestion
            fixed_line = line_content
            for unicode_char, replacement in PROBLEMATIC_UNICODE.items():
                if unicode_char in unicode_chars:
                    fixed_line = fixed_line.replace(unicode_char, replacement)
            
            suggestions.append(f"    Fixed:   {fixed_line}")
            suggestions.append("")
    
    return '\n'.join(suggestions)

def check_safe_logger_usage(directory: str) -> Dict[str, List[int]]:
    """Check which Python files are not using safe_logger."""
    non_safe_files = {}
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.vscode']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Look for logging usage without safe_logger import
                    has_logging = re.search(r'import logging|from logging', content)
                    has_safe_logger = re.search(r'from utils\.safe_logger|import safe_logger', content)
                    has_print = re.search(r'\bprint\s*\(', content)
                    
                    issues = []
                    if has_logging and not has_safe_logger:
                        issues.append("Uses logging without safe_logger")
                    if has_print and not has_safe_logger:
                        issues.append("Uses print() without safe_print")
                    
                    if issues:
                        non_safe_files[file_path] = issues
                        
                except Exception as e:
                    logger.warning(f"Could not check {file_path}: {e}")
    
    return non_safe_files

def main():
    """Main detection and reporting function."""
    safe_print("Unicode Issue Detection Tool")
    safe_print("=" * 40)
    
    # Scan for Unicode issues
    current_dir = os.getcwd()
    unicode_issues = scan_directory(current_dir)
    
    if unicode_issues:
        safe_print(f"\n[ERROR] Found Unicode issues in {len(unicode_issues)} files:")
        
        total_issues = sum(len(issues) for issues in unicode_issues.values())
        safe_print(f"Total problematic lines: {total_issues}")
        
        # Generate and display fix suggestions
        fix_suggestions = generate_fix_suggestions(unicode_issues)
        safe_print(fix_suggestions)
        
        # Write fix suggestions to file
        with open('unicode_fixes.txt', 'w', encoding='utf-8') as f:
            f.write("Unicode Fix Suggestions\n")
            f.write("=" * 30 + "\n")
            f.write(fix_suggestions)
        
        safe_print(f"[SUCCESS] Fix suggestions written to: unicode_fixes.txt")
    else:
        safe_print("[SUCCESS] No Unicode issues found!")
    
    # Check safe_logger usage
    safe_print("\n" + "=" * 40)
    safe_print("Safe Logger Usage Check")
    safe_print("=" * 40)
    
    non_safe_files = check_safe_logger_usage(current_dir)
    
    if non_safe_files:
        safe_print(f"\n[WARNING] Found {len(non_safe_files)} files not using safe_logger:")
        
        for file_path, issues in non_safe_files.items():
            safe_print(f"\n  {file_path}")
            for issue in issues:
                safe_print(f"    - {issue}")
        
        safe_print(f"\n[RECOMMENDATION] Update these files to use:")
        safe_print("  from utils.safe_logger import get_safe_logger, safe_print")
        safe_print("  logger = get_safe_logger(__name__)")
    else:
        safe_print("[SUCCESS] All files are using safe logging!")

if __name__ == "__main__":
    main()