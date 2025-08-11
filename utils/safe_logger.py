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
    # Common Unicode characters that cause encoding issues
    '\u2011': '-',   # Non-breaking hyphen
    '\u2012': '-',   # Figure dash
    '\u2013': '-',   # En dash
    '\u2014': '--',  # Em dash
    '\u2015': '--',  # Horizontal bar
    '\u2018': "'",   # Left single quotation mark
    '\u2019': "'",   # Right single quotation mark
    '\u201a': ',',   # Single low-9 quotation mark
    '\u201c': '"',   # Left double quotation mark
    '\u201d': '"',   # Right double quotation mark
    '\u201e': '"',   # Double low-9 quotation mark
    '\u2026': '...', # Horizontal ellipsis
    '\u2022': '*',   # Bullet
    '\u2023': '>',   # Triangular bullet
    '\u2024': '.',   # One dot leader
    '\u2025': '..',  # Two dot leader
    '\u2027': '-',   # Hyphenation point
    '\u2032': "'",   # Prime
    '\u2033': '"',   # Double prime
    '\u203a': '>',   # Single right-pointing angle quotation mark
    '\u203c': '!!',  # Double exclamation mark
    '\u2047': '??',  # Double question mark
    '\u2048': '?!',  # Question exclamation mark
    '\u2049': '!?',  # Exclamation question mark
    '\xa0': ' ',     # Non-breaking space
    '\u200b': '',    # Zero-width space
    '\u200c': '',    # Zero-width non-joiner
    '\u200d': '',    # Zero-width joiner
    '\u2060': '',    # Word joiner
    '\ufeff': '',    # Zero-width no-break space (BOM)
}

def sanitize_message(message: str) -> str:
    """Replace Unicode characters with ASCII equivalents."""
    for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
        message = message.replace(unicode_char, replacement)
    
    # Try cp1252 encoding first (Windows default), then ASCII
    try:
        # Test if it can be encoded in cp1252
        message.encode('cp1252')
        return message
    except UnicodeEncodeError:
        # If cp1252 fails, try ASCII with replacement
        try:
            message.encode('ascii')
            return message
        except UnicodeEncodeError:
            # Replace any remaining non-ASCII with '?'
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