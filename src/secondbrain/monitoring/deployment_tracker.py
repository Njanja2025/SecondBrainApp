"""
Deployment tracking and monitoring system for SecondBrain application.
Tracks application launches, crashes, and usage statistics.
"""

import os
import json
import platform
import socket
import datetime
import logging
import uuid
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DeploymentEvent:
    """Represents a deployment event with system and application information."""
    event_id: str
    timestamp: str
    host: str
    platform: str
    python_version: str
    app_version: str
    status: str
    memory_usage: float
    cpu_usage: float
    notes: str
    session_id: str
    user_id: Optional[str] = None

class DeploymentTracker:
    """Tracks deployment events and system metrics."""
    
    def __init__(self, app_name: str, app_version: str, log_dir: str = "logs"):
        """Initialize the deployment tracker.
        
        Args:
            app_name: Name of the application
            app_version: Version of the application
            log_dir: Directory for log files
        """
        self.app_name = app_name
        self.app_version = app_version
        self.log_dir = Path(log_dir)
        self.session_id = str(uuid.uuid4())
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up log files
        self.deployment_log = self.log_dir / "deployment_status.log"
        self.metrics_log = self.log_dir / "system_metrics.log"
        
        # Initialize logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        
        # Deployment status handler
        deployment_handler = logging.FileHandler(self.deployment_log)
        deployment_handler.setFormatter(formatter)
        logger.addHandler(deployment_handler)
        
        # System metrics handler
        metrics_handler = logging.FileHandler(self.metrics_log)
        metrics_handler.setFormatter(formatter)
        logger.addHandler(metrics_handler)
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics.
        
        Returns:
            Dictionary containing system metrics
        """
        return {
            'memory_usage': psutil.Process().memory_percent(),
            'cpu_usage': psutil.Process().cpu_percent(),
            'disk_usage': psutil.disk_usage('/').percent
        }
    
    def _create_event(self, status: str, notes: str = "") -> DeploymentEvent:
        """Create a deployment event.
        
        Args:
            status: Event status (e.g., 'launched', 'crashed')
            notes: Additional notes about the event
            
        Returns:
            DeploymentEvent object
        """
        metrics = self._get_system_metrics()
        return DeploymentEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.datetime.utcnow().isoformat(),
            host=socket.gethostname(),
            platform=platform.platform(),
            python_version=platform.python_version(),
            app_version=self.app_version,
            status=status,
            memory_usage=metrics['memory_usage'],
            cpu_usage=metrics['cpu_usage'],
            notes=notes,
            session_id=self.session_id
        )
    
    def log_event(self, status: str, notes: str = "") -> None:
        """Log a deployment event.
        
        Args:
            status: Event status (e.g., 'launched', 'crashed')
            notes: Additional notes about the event
        """
        try:
            event = self._create_event(status, notes)
            
            # Log to file
            with open(self.deployment_log, "a") as f:
                f.write(f"{json.dumps(asdict(event))}\n")
            
            # Log to logger
            logger.info(f"Deployment event: {status} - {notes}")
            
        except Exception as e:
            logger.error(f"Failed to log deployment event: {str(e)}")
    
    def log_metrics(self) -> None:
        """Log current system metrics."""
        try:
            metrics = self._get_system_metrics()
            metrics['timestamp'] = datetime.datetime.utcnow().isoformat()
            metrics['session_id'] = self.session_id
            
            # Log to file
            with open(self.metrics_log, "a") as f:
                f.write(f"{json.dumps(metrics)}\n")
            
            # Log to logger
            logger.debug(f"System metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Failed to log system metrics: {str(e)}")
    
    def get_recent_events(self, limit: int = 100) -> list:
        """Get recent deployment events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent deployment events
        """
        events = []
        try:
            with open(self.deployment_log, "r") as f:
                for line in f.readlines()[-limit:]:
                    events.append(json.loads(line.strip()))
        except Exception as e:
            logger.error(f"Failed to read deployment events: {str(e)}")
        return events
    
    def get_session_metrics(self) -> list:
        """Get metrics for the current session.
        
        Returns:
            List of metrics for the current session
        """
        metrics = []
        try:
            with open(self.metrics_log, "r") as f:
                for line in f:
                    metric = json.loads(line.strip())
                    if metric.get('session_id') == self.session_id:
                        metrics.append(metric)
        except Exception as e:
            logger.error(f"Failed to read session metrics: {str(e)}")
        return metrics

# Create global instance
tracker = DeploymentTracker(
    app_name="SecondBrainApp",
    app_version="1.0.0"
)

# Example usage
if __name__ == "__main__":
    # Log application launch
    tracker.log_event("launched", "Application started")
    
    # Log periodic metrics
    tracker.log_metrics()
    
    # Get recent events
    events = tracker.get_recent_events()
    print(f"Recent events: {events}")
    
    # Get session metrics
    metrics = tracker.get_session_metrics()
    print(f"Session metrics: {metrics}") 