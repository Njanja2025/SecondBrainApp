"""
Error handler for managing integration errors and retries.
Handles error recovery, retry logic, and fallback procedures.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    retry_on_exceptions: List[type] = None

class ErrorManager:
    """Manages integration errors and retries."""
    
    def __init__(self, error_dir: str = "logs/errors"):
        """Initialize the error manager.
        
        Args:
            error_dir: Directory to store error logs
        """
        self.error_dir = Path(error_dir)
        self.error_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_error_handlers()
    
    def _setup_logging(self):
        """Set up logging for the error manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_error_handlers(self):
        """Load error handlers from configuration."""
        try:
            config_file = self.error_dir / "error_handlers.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.error_handlers = json.load(f)
            else:
                self.error_handlers = {}
                self._save_error_handlers()
            
            logger.info("Error handlers loaded")
            
        except Exception as e:
            logger.error(f"Failed to load error handlers: {str(e)}")
            raise
    
    def _save_error_handlers(self):
        """Save error handlers to configuration."""
        try:
            config_file = self.error_dir / "error_handlers.json"
            
            with open(config_file, 'w') as f:
                json.dump(self.error_handlers, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save error handlers: {str(e)}")
    
    def register_error_handler(self, error_type: str, handler: Callable):
        """Register an error handler.
        
        Args:
            error_type: Type of error to handle
            handler: Error handler function
        """
        try:
            self.error_handlers[error_type] = handler.__name__
            self._save_error_handlers()
            
            logger.info(f"Registered error handler for {error_type}")
            
        except Exception as e:
            logger.error(f"Failed to register error handler for {error_type}: {str(e)}")
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Handle an integration error.
        
        Args:
            error: Exception to handle
            context: Error context
            
        Returns:
            bool: True if error was handled successfully
        """
        try:
            error_type = type(error).__name__
            
            # Log error
            self._log_error(error, context)
            
            # Get error handler
            handler_name = self.error_handlers.get(error_type)
            if not handler_name:
                logger.error(f"No handler found for error type {error_type}")
                return False
            
            # Call error handler
            handler = getattr(self, handler_name, None)
            if not handler:
                logger.error(f"Handler {handler_name} not found")
                return False
            
            return handler(error, context)
            
        except Exception as e:
            logger.error(f"Failed to handle error: {str(e)}")
            return False
    
    def _log_error(self, error: Exception, context: Dict[str, Any]):
        """Log an error.
        
        Args:
            error: Exception to log
            context: Error context
        """
        try:
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
            
            # Create error file
            error_file = self.error_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(error_file, 'w') as f:
                json.dump(error_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}")
    
    def retry_operation(self, operation: Callable, config: RetryConfig,
                       *args, **kwargs) -> Any:
        """Retry an operation with exponential backoff.
        
        Args:
            operation: Operation to retry
            config: Retry configuration
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Operation result if successful
            
        Raises:
            Exception: If operation fails after all retries
        """
        last_exception = None
        delay = config.initial_delay
        
        for attempt in range(config.max_retries + 1):
            try:
                return operation(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                # Check if we should retry
                if attempt < config.max_retries:
                    if config.retry_on_exceptions and not isinstance(e, tuple(config.retry_on_exceptions)):
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(delay * config.backoff_factor, config.max_delay)
                    
                    # Log retry attempt
                    logger.warning(f"Operation failed, retrying in {delay:.1f} seconds "
                                 f"(attempt {attempt + 1}/{config.max_retries})")
                    
                    # Wait before retrying
                    time.sleep(delay)
                else:
                    logger.error(f"Operation failed after {config.max_retries} retries")
                    raise last_exception
    
    def get_error_stats(self, start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get error statistics.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Error statistics
        """
        try:
            stats = {
                "total_errors": 0,
                "error_types": {},
                "services": {}
            }
            
            for error_file in self.error_dir.glob("error_*.json"):
                try:
                    with open(error_file, 'r') as f:
                        error_data = json.load(f)
                    
                    # Apply time filters
                    error_time = datetime.fromisoformat(error_data["timestamp"])
                    if start_time and error_time < start_time:
                        continue
                    if end_time and error_time > end_time:
                        continue
                    
                    # Update statistics
                    stats["total_errors"] += 1
                    
                    error_type = error_data["error_type"]
                    stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
                    
                    service = error_data["context"].get("service", "unknown")
                    stats["services"][service] = stats["services"].get(service, 0) + 1
                    
                except Exception as e:
                    logger.error(f"Failed to process error file {error_file}: {str(e)}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get error stats: {str(e)}")
            return {}
    
    def cleanup_old_errors(self, days: int = 30):
        """Clean up old error logs.
        
        Args:
            days: Number of days to keep errors
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            for error_file in self.error_dir.glob("error_*.json"):
                try:
                    with open(error_file, 'r') as f:
                        error_data = json.load(f)
                    
                    error_time = datetime.fromisoformat(error_data["timestamp"])
                    if error_time < cutoff_time:
                        error_file.unlink()
                        logger.info(f"Deleted old error file: {error_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to process error file {error_file}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old errors: {str(e)}")

# Example usage
if __name__ == "__main__":
    manager = ErrorManager()
    
    # Register error handler
    def handle_connection_error(error, context):
        logger.error(f"Connection error: {error}")
        return True
    
    manager.register_error_handler("ConnectionError", handle_connection_error)
    
    # Retry operation
    def test_operation():
        raise ConnectionError("Connection failed")
    
    config = RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        max_delay=10.0,
        backoff_factor=2.0,
        retry_on_exceptions=[ConnectionError]
    )
    
    try:
        result = manager.retry_operation(test_operation, config)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
    
    # Get error stats
    stats = manager.get_error_stats()
    print("Error stats:", stats)
    
    # Cleanup old errors
    manager.cleanup_old_errors(days=30) 