"""
Safe logging utility that prevents Unicode encoding issues on Windows.
Automatically replaces problematic characters with ASCII equivalents.
"""

import logging
import sys
from typing import Any

# Unicode to ASCII mappings for common emojis/symbols
UNICODE_REPLACEMENTS = {
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

def sanitize_message(message: str) -> str:
    """Replace Unicode characters with ASCII equivalents."""
    for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
        message = message.replace(unicode_char, replacement)
    
    # Remove any remaining non-ASCII characters
    try:
        message.encode('ascii')
        return message
    except UnicodeEncodeError:
        # Replace any remaining non-ASCII with ASCII representation
        return message.encode('ascii', errors='replace').decode('ascii')

class SafeLogger:
    """Logger wrapper that prevents Unicode encoding issues."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, *args, **kwargs):
        safe_message = sanitize_message(str(message))
        self.logger.info(safe_message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        safe_message = sanitize_message(str(message))
        self.logger.warning(safe_message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        safe_message = sanitize_message(str(message))
        self.logger.error(safe_message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        safe_message = sanitize_message(str(message))
        self.logger.debug(safe_message, *args, **kwargs)

def safe_print(message: Any):
    """Safe print function that handles Unicode encoding issues."""
    try:
        safe_message = sanitize_message(str(message))
        print(safe_message)
    except Exception as e:
        # Fallback - print without Unicode characters
        try:
            ascii_message = str(message).encode('ascii', errors='replace').decode('ascii')
            print(f"[ENCODING_ISSUE] {ascii_message}")
        except:
            print(f"[ENCODING_ERROR] Could not display message: {type(message)}")

# Global logger instances
def get_safe_logger(name: str) -> SafeLogger:
    """Get a safe logger instance for the given module."""
    return SafeLogger(name)