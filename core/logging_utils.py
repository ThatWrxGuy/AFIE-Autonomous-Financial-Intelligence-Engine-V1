"""
Structured logging utilities for AFC3.

Provides structured logging with:
- timestamp
- component
- task_id
- agent_id
- pipeline_run_id
- duration
- message
- Log levels: INFO, WARNING, ERROR, DEBUG
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import json


class StructuredLogger:
    """Structured logger wrapper."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up logging handlers."""
        # Console handler with simple format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Only add handler if not already present
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.DEBUG)
            self.logger.propagate = False
    
    def _log(self, level: int, message: str, 
             component: Optional[str] = None,
             task_id: Optional[str] = None,
             agent_id: Optional[str] = None,
             pipeline_run_id: Optional[str] = None,
             duration: Optional[float] = None):
        """Internal logging method."""
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": logging.getLevelName(level),
            "component": component or "unknown",
            "task_id": task_id,
            "agent_id": agent_id,
            "pipeline_run_id": pipeline_run_id,
            "duration": duration,
            "message": message
        }
        
        # Filter out None values
        log_entry = {k: v for k, v in log_entry.items() if v is not None}
        
        # Output as JSON
        self.logger.log(level, json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        """Log INFO level message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log WARNING level message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log ERROR level message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log DEBUG level message."""
        self._log(logging.DEBUG, message, **kwargs)


# Global logger registry
_loggers = {}


def get_logger(name: str = "afc3") -> StructuredLogger:
    """Get or create a structured logger."""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def log_info(component: str, message: str, 
             task_id: Optional[str] = None,
             agent_id: Optional[str] = None,
             pipeline_run_id: Optional[str] = None):
    """Convenience function for INFO logging."""
    get_logger().info(message, component=component, task_id=task_id, 
                     agent_id=agent_id, pipeline_run_id=pipeline_run_id)


def log_warning(component: str, message: str,
                task_id: Optional[str] = None,
                agent_id: Optional[str] = None,
                pipeline_run_id: Optional[str] = None):
    """Convenience function for WARNING logging."""
    get_logger().warning(message, component=component, task_id=task_id,
                       agent_id=agent_id, pipeline_run_id=pipeline_run_id)


def log_error(component: str, message: str,
              task_id: Optional[str] = None,
              agent_id: Optional[str] = None,
              pipeline_run_id: Optional[str] = None):
    """Convenience function for ERROR logging."""
    get_logger().error(message, component=component, task_id=task_id,
                      agent_id=agent_id, pipeline_run_id=pipeline_run_id)


def log_debug(component: str, message: str,
              task_id: Optional[str] = None,
              agent_id: Optional[str] = None,
              pipeline_run_id: Optional[str] = None):
    """Convenience function for DEBUG logging."""
    get_logger().debug(message, component=component, task_id=task_id,
                     agent_id=agent_id, pipeline_run_id=pipeline_run_id)
