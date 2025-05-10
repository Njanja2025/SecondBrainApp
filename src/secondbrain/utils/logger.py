"""
Logging management for SecondBrainApp
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logger(name: str, log_file: Optional[str] = None, 
                level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    try:
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Create file handler if log file specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        logger.info(f"Set up logger {name} with level {level}")
        return logger
        
    except Exception as e:
        print(f"Failed to set up logger {name}: {e}")
        return logging.getLogger(name)
        
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
    
def set_log_level(logger: logging.Logger, level: str) -> bool:
    """
    Set logging level for a logger.
    
    Args:
        logger: Logger instance
        level: Logging level
        
    Returns:
        bool: True if successful
    """
    try:
        logger.setLevel(getattr(logging, level.upper()))
        logger.info(f"Set log level to {level}")
        return True
    except Exception as e:
        logger.error(f"Failed to set log level: {e}")
        return False
        
def add_file_handler(logger: logging.Logger, log_file: str, 
                    level: Optional[str] = None) -> bool:
    """
    Add a file handler to a logger.
    
    Args:
        logger: Logger instance
        log_file: Path to log file
        level: Optional logging level for file handler
        
    Returns:
        bool: True if successful
    """
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        if level:
            file_handler.setLevel(getattr(logging, level.upper()))
            
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        ))
        
        logger.addHandler(file_handler)
        logger.info(f"Added file handler: {log_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add file handler: {e}")
        return False
        
def remove_file_handler(logger: logging.Logger, log_file: str) -> bool:
    """
    Remove a file handler from a logger.
    
    Args:
        logger: Logger instance
        log_file: Path to log file
        
    Returns:
        bool: True if successful
    """
    try:
        for handler in logger.handlers[:]:
            if isinstance(handler, RotatingFileHandler):
                if handler.baseFilename == str(Path(log_file).absolute()):
                    logger.removeHandler(handler)
                    logger.info(f"Removed file handler: {log_file}")
                    return True
        return False
        
    except Exception as e:
        logger.error(f"Failed to remove file handler: {e}")
        return False
        
def get_log_handlers(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Get information about logger handlers.
    
    Args:
        logger: Logger instance
        
    Returns:
        List[Dict[str, Any]]: Handler information
    """
    handlers = []
    for handler in logger.handlers:
        handler_info = {
            "type": handler.__class__.__name__,
            "level": logging.getLevelName(handler.level),
            "formatter": handler.formatter.__class__.__name__ if handler.formatter else None
        }
        
        if isinstance(handler, RotatingFileHandler):
            handler_info.update({
                "file": handler.baseFilename,
                "max_bytes": handler.maxBytes,
                "backup_count": handler.backupCount
            })
            
        handlers.append(handler_info)
        
    return handlers
    
def get_log_stats(logger: logging.Logger) -> Dict[str, Any]:
    """
    Get logging statistics.
    
    Args:
        logger: Logger instance
        
    Returns:
        Dict[str, Any]: Logging statistics
    """
    stats = {
        "name": logger.name,
        "level": logging.getLevelName(logger.level),
        "handlers": get_log_handlers(logger),
        "propagate": logger.propagate,
        "disabled": logger.disabled
    }
    
    # Get parent loggers
    parent = logger.parent
    parents = []
    while parent:
        parents.append(parent.name)
        parent = parent.parent
    stats["parents"] = parents
    
    return stats
    
def configure_root_logger(level: str = "INFO", 
                         log_file: Optional[str] = None) -> bool:
    """
    Configure the root logger.
    
    Args:
        level: Logging level
        log_file: Optional path to log file
        
    Returns:
        bool: True if successful
    """
    try:
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            ))
            root_logger.addHandler(file_handler)
            
        root_logger.info(f"Configured root logger with level {level}")
        return True
        
    except Exception as e:
        print(f"Failed to configure root logger: {e}")
        return False 