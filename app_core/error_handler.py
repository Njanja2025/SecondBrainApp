"""
Error Handler - Custom Error Handling System
Provides centralized error handling and logging for the voice assistant.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

@dataclass
class ErrorContext:
    """Context information for error handling."""
    timestamp: datetime
    severity: ErrorSeverity
    error_type: str
    message: str
    traceback: Optional[str]
    command: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ErrorHandler:
    """Centralized error handling system."""
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_handlers: Dict[ErrorSeverity, Callable] = {
            ErrorSeverity.DEBUG: self._handle_debug,
            ErrorSeverity.INFO: self._handle_info,
            ErrorSeverity.WARNING: self._handle_warning,
            ErrorSeverity.ERROR: self._handle_error,
            ErrorSeverity.CRITICAL: self._handle_critical
        }
        self.error_history: List[ErrorContext] = []
        self.max_history_size = 1000
    
    def handle_error(self, error: Exception, severity: ErrorSeverity = ErrorSeverity.ERROR,
                    command: Optional[str] = None, args: Optional[Dict[str, Any]] = None,
                    user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """Handle an error with the specified severity."""
        try:
            error_context = ErrorContext(
                timestamp=datetime.now(),
                severity=severity,
                error_type=type(error).__name__,
                message=str(error),
                traceback=traceback.format_exc(),
                command=command,
                args=args,
                user_id=user_id,
                session_id=session_id
            )
            
            # Add to history
            self.error_history.append(error_context)
            if len(self.error_history) > self.max_history_size:
                self.error_history.pop(0)
            
            # Handle based on severity
            handler = self.error_handlers.get(severity, self._handle_error)
            return handler(error_context)
        except Exception as e:
            logger.critical(f"Failed to handle error: {e}")
            return "An unexpected error occurred while handling another error"
    
    def _handle_debug(self, context: ErrorContext) -> str:
        """Handle debug level errors."""
        logger.debug(f"Debug: {context.message}")
        return f"Debug: {context.message}"
    
    def _handle_info(self, context: ErrorContext) -> str:
        """Handle info level errors."""
        logger.info(f"Info: {context.message}")
        return f"Info: {context.message}"
    
    def _handle_warning(self, context: ErrorContext) -> str:
        """Handle warning level errors."""
        logger.warning(f"Warning: {context.message}")
        return f"Warning: {context.message}"
    
    def _handle_error(self, context: ErrorContext) -> str:
        """Handle error level errors."""
        logger.error(f"Error: {context.message}\n{context.traceback}")
        return "I encountered an error processing your request. Please try again."
    
    def _handle_critical(self, context: ErrorContext) -> str:
        """Handle critical level errors."""
        logger.critical(f"Critical Error: {context.message}\n{context.traceback}")
        return "I encountered a critical error. Please restart the application."
    
    def get_error_history(self, severity: Optional[ErrorSeverity] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[ErrorContext]:
        """Get error history with optional filtering."""
        filtered_history = self.error_history
        
        if severity:
            filtered_history = [e for e in filtered_history if e.severity == severity]
        
        if start_time:
            filtered_history = [e for e in filtered_history if e.timestamp >= start_time]
        
        if end_time:
            filtered_history = [e for e in filtered_history if e.timestamp <= end_time]
        
        return filtered_history
    
    def clear_error_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by severity."""
        summary = {severity: 0 for severity in ErrorSeverity}
        for error in self.error_history:
            summary[error.severity] += 1
        return summary
    
    def get_most_common_errors(self, limit: int = 10) -> List[tuple]:
        """Get most common errors by type."""
        error_counts = {}
        for error in self.error_history:
            error_type = error.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:limit] 