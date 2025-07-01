"""
Logging utilities for the Agile Backlog Automation system.

Provides centralized logging configuration with file rotation,
console output, and structured logging for different components.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str, 
                 log_file: Optional[str] = None, 
                 level: str = 'INFO',
                 console_output: bool = True) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Use a simpler format for console
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger by name."""
    return logging.getLogger(name)


class WorkflowLogger:
    """
    Specialized logger for workflow execution with structured logging.
    """
    
    def __init__(self, workflow_id: str = None):
        """Initialize workflow logger."""
        self.workflow_id = workflow_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = setup_logger(
            f"workflow_{self.workflow_id}",
            f"logs/workflow_{self.workflow_id}.log"
        )
        
        # Stage tracking
        self.current_stage = None
        self.stage_start_time = None
        
    def start_stage(self, stage_name: str):
        """Mark the start of a workflow stage."""
        self.current_stage = stage_name
        self.stage_start_time = datetime.now()
        self.logger.info(f"Starting stage: {stage_name}")
        
    def end_stage(self, stage_name: str, success: bool = True):
        """Mark the end of a workflow stage."""
        if self.stage_start_time:
            duration = (datetime.now() - self.stage_start_time).total_seconds()
            status = "completed" if success else "failed"
            self.logger.info(f"Stage {stage_name} {status} in {duration:.2f} seconds")
        
        self.current_stage = None
        self.stage_start_time = None
        
    def log_agent_interaction(self, agent_name: str, input_data: str, output_data: str):
        """Log agent interaction details."""
        self.logger.debug(f"Agent {agent_name} interaction:")
        self.logger.debug(f"Input: {input_data[:200]}...")
        self.logger.debug(f"Output: {output_data[:200]}...")
        
    def log_error(self, error: Exception, context: str = None):
        """Log an error with context."""
        if context:
            self.logger.error(f"Error in {context}: {error}", exc_info=True)
        else:
            self.logger.error(f"Error: {error}", exc_info=True)
            
    def log_metrics(self, metrics: dict):
        """Log workflow metrics."""
        self.logger.info(f"Metrics: {metrics}")


# Global logger instance
_default_logger = None

def get_default_logger():
    """Get the default application logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger("agile_backlog_automation", "logs/application.log")
    return _default_logger
