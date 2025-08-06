#!/usr/bin/env python3
"""
Auto Log Dumper - Automatically captures and saves all backend logs to files.

This eliminates the need to manually copy/paste backend logs for debugging.
All logs are saved with meaningful names including job IDs and timestamps.
"""

import os
import sys
import atexit
import signal
import logging
from datetime import datetime
from pathlib import Path
from io import StringIO
import threading
import time

class AutoLogDumper:
    """Captures all console output and automatically saves to log files."""
    
    def __init__(self, log_dir: str = "logs", job_id: str = None):
        """Initialize the auto log dumper.
        
        Args:
            log_dir: Directory to save log files (default: "logs")
            job_id: Job identifier for meaningful filenames
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.job_id = job_id or f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        
        # Create log filename
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        self.log_filename = self.log_dir / f"backend_{timestamp}_{self.job_id}.log"
        
        # Storage for captured output
        self.captured_output = StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Threading for real-time capture
        self.capture_lock = threading.Lock()
        self.is_active = False
        
        print(f"🔄 Auto log dumper initialized: {self.log_filename}")
    
    def start_capture(self):
        """Start capturing all console output."""
        self.is_active = True
        
        # Create tee-like behavior - show on console AND capture to file
        sys.stdout = TeeOutput(self.original_stdout, self.captured_output, self.capture_lock)
        sys.stderr = TeeOutput(self.original_stderr, self.captured_output, self.capture_lock)
        
        # Register cleanup handlers
        atexit.register(self._save_log_on_exit)
        signal.signal(signal.SIGINT, self._save_log_on_signal)
        signal.signal(signal.SIGTERM, self._save_log_on_signal)
        
        print(f"📝 Auto log capture started - saving to: {self.log_filename}")
    
    def stop_capture(self):
        """Stop capturing and save the log file."""
        if not self.is_active:
            return
            
        self.is_active = False
        
        # Restore original streams
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        # Save the captured output
        self._write_log_file("normal_completion")
        print(f"✅ Auto log saved to: {self.log_filename}")
    
    def _save_log_on_exit(self):
        """Save log when process exits normally."""
        if self.is_active:
            self._write_log_file("normal_exit")
    
    def _save_log_on_signal(self, signum, frame):
        """Save log when process is killed/interrupted."""
        signal_names = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}
        signal_name = signal_names.get(signum, str(signum))
        
        if self.is_active:
            self._write_log_file(f"killed_{signal_name}")
            print(f"\n🛑 Process interrupted - log saved to: {self.log_filename}")
        
        # Re-raise the signal to continue normal termination
        sys.exit(1)
    
    def _write_log_file(self, completion_type: str):
        """Write the captured output to a log file."""
        try:
            with self.capture_lock:
                log_content = self.captured_output.getvalue()
            
            # Add header with metadata
            duration = datetime.now() - self.start_time
            header = f"""
=== BACKEND LOG AUTO-DUMP ===
Job ID: {self.job_id}
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}
Completion Type: {completion_type}
Log File: {self.log_filename.name}
=== LOG CONTENT BEGINS ===

"""
            
            # Write to file
            with open(self.log_filename, 'w', encoding='utf-8', errors='replace') as f:
                f.write(header)
                f.write(log_content)
                f.write(f"\n\n=== LOG CONTENT ENDS ===\n")
                f.write(f"Total captured lines: {log_content.count(chr(10))}")
            
            # Also create a "latest" symlink for easy access
            latest_link = self.log_dir / "latest_backend.log"
            try:
                if latest_link.exists():
                    latest_link.unlink()
                # On Windows, copy instead of symlink
                import shutil
                shutil.copy2(self.log_filename, latest_link)
            except:
                pass  # Ignore symlink errors
                
        except Exception as e:
            # Fallback - try to save to a backup location
            backup_file = self.log_dir / f"backup_{self.job_id}.log"
            try:
                with open(backup_file, 'w') as f:
                    f.write(f"ERROR saving log: {e}\n")
                    f.write(f"Captured content length: {len(log_content)}\n")
                    f.write("Raw captured content:\n")
                    f.write(log_content)
            except:
                pass  # Ultimate fallback - at least we tried


class TeeOutput:
    """Splits output to both console and captured storage."""
    
    def __init__(self, original_stream, capture_stream, lock):
        self.original_stream = original_stream
        self.capture_stream = capture_stream
        self.lock = lock
    
    def write(self, text):
        # Write to original console
        self.original_stream.write(text)
        self.original_stream.flush()
        
        # Write to captured storage (thread-safe)
        with self.lock:
            self.capture_stream.write(text)
        
        return len(text)
    
    def flush(self):
        self.original_stream.flush()
    
    def __getattr__(self, name):
        return getattr(self.original_stream, name)


# Global instance for easy access
_global_dumper = None

def start_auto_logging(job_id: str = None, log_dir: str = "logs"):
    """Start auto-logging for the current process.
    
    Args:
        job_id: Job identifier for meaningful filenames
        log_dir: Directory to save log files
    """
    global _global_dumper
    
    if _global_dumper and _global_dumper.is_active:
        print("⚠️ Auto logging already active")
        return _global_dumper
    
    _global_dumper = AutoLogDumper(log_dir=log_dir, job_id=job_id)
    _global_dumper.start_capture()
    return _global_dumper

def stop_auto_logging():
    """Stop auto-logging and save the current log."""
    global _global_dumper
    
    if _global_dumper and _global_dumper.is_active:
        _global_dumper.stop_capture()
        return _global_dumper.log_filename
    
    return None

def get_latest_log_file():
    """Get the path to the most recent log file."""
    global _global_dumper
    
    if _global_dumper:
        return _global_dumper.log_filename
    
    # Try to find latest log in logs directory
    log_dir = Path("logs")
    if log_dir.exists():
        latest_link = log_dir / "latest_backend.log"
        if latest_link.exists():
            return latest_link
    
    return None