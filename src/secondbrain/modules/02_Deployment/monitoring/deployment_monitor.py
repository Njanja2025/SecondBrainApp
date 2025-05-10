"""
Deployment monitoring system for SecondBrain application.
Tracks deployment status, performance metrics, and system health.
"""

import os
import json
import logging
import threading
import time
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DeploymentMetrics:
    """Represents deployment performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    timestamp: datetime

@dataclass
class DeploymentStatus:
    """Represents deployment status information."""
    version: str
    environment: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    metrics: List[DeploymentMetrics]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]

class DeploymentMonitor:
    """Monitors deployment status and system metrics."""
    
    def __init__(self, config_dir: str = "config/deployment"):
        """Initialize the deployment monitor.
        
        Args:
            config_dir: Directory to store deployment configuration
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_config()
        self._initialize_metrics()
        self._start_monitoring()
    
    def _setup_logging(self):
        """Set up logging for the deployment monitor."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_config(self):
        """Load monitoring configuration."""
        try:
            config_file = self.config_dir / "monitoring.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Default configuration
                self.config = {
                    "metrics_interval": 60,  # seconds
                    "retention_days": 30,
                    "alert_thresholds": {
                        "cpu_usage": 80.0,
                        "memory_usage": 80.0,
                        "disk_usage": 80.0
                    }
                }
                
                # Save default configuration
                with open(config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
            
            logger.info("Monitoring configuration loaded")
            
        except Exception as e:
            logger.error(f"Failed to load monitoring configuration: {str(e)}")
            raise
    
    def _initialize_metrics(self):
        """Initialize monitoring metrics."""
        self.current_deployment: Optional[DeploymentStatus] = None
        self.deployment_history: List[DeploymentStatus] = []
        self.monitoring = False
    
    def _start_monitoring(self):
        """Start the monitoring thread."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                if self.current_deployment:
                    metrics = self._collect_metrics()
                    self.current_deployment.metrics.append(metrics)
                    
                    # Check for alerts
                    self._check_alerts(metrics)
                
                time.sleep(self.config["metrics_interval"])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
    
    def _collect_metrics(self) -> DeploymentMetrics:
        """Collect system metrics.
        
        Returns:
            Current system metrics
        """
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            net_io = psutil.net_io_counters()
            network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            return DeploymentMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            raise
    
    def _check_alerts(self, metrics: DeploymentMetrics):
        """Check metrics against alert thresholds.
        
        Args:
            metrics: Current system metrics
        """
        try:
            thresholds = self.config["alert_thresholds"]
            
            if metrics.cpu_usage > thresholds["cpu_usage"]:
                self._add_warning("High CPU usage", {
                    "current": metrics.cpu_usage,
                    "threshold": thresholds["cpu_usage"]
                })
            
            if metrics.memory_usage > thresholds["memory_usage"]:
                self._add_warning("High memory usage", {
                    "current": metrics.memory_usage,
                    "threshold": thresholds["memory_usage"]
                })
            
            if metrics.disk_usage > thresholds["disk_usage"]:
                self._add_warning("High disk usage", {
                    "current": metrics.disk_usage,
                    "threshold": thresholds["disk_usage"]
                })
            
        except Exception as e:
            logger.error(f"Failed to check alerts: {str(e)}")
    
    def _add_warning(self, message: str, details: Dict[str, Any]):
        """Add a warning to the current deployment.
        
        Args:
            message: Warning message
            details: Warning details
        """
        if self.current_deployment:
            self.current_deployment.warnings.append({
                "message": message,
                "details": details,
                "timestamp": datetime.now()
            })
    
    def _add_error(self, message: str, details: Dict[str, Any]):
        """Add an error to the current deployment.
        
        Args:
            message: Error message
            details: Error details
        """
        if self.current_deployment:
            self.current_deployment.errors.append({
                "message": message,
                "details": details,
                "timestamp": datetime.now()
            })
    
    def start_deployment(self, version: str, environment: str) -> bool:
        """Start tracking a new deployment.
        
        Args:
            version: Deployment version
            environment: Deployment environment
            
        Returns:
            bool: True if deployment tracking started successfully
        """
        try:
            if self.current_deployment:
                logger.error("Deployment already in progress")
                return False
            
            self.current_deployment = DeploymentStatus(
                version=version,
                environment=environment,
                status="in_progress",
                start_time=datetime.now(),
                end_time=None,
                metrics=[],
                errors=[],
                warnings=[]
            )
            
            logger.info(f"Started tracking deployment {version} in {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start deployment tracking: {str(e)}")
            return False
    
    def end_deployment(self, status: str = "completed") -> bool:
        """End tracking the current deployment.
        
        Args:
            status: Final deployment status
            
        Returns:
            bool: True if deployment tracking ended successfully
        """
        try:
            if not self.current_deployment:
                logger.error("No deployment in progress")
                return False
            
            self.current_deployment.status = status
            self.current_deployment.end_time = datetime.now()
            
            # Add to history
            self.deployment_history.append(self.current_deployment)
            
            # Save deployment status
            self._save_deployment_status(self.current_deployment)
            
            # Clean up old deployments
            self._cleanup_old_deployments()
            
            self.current_deployment = None
            logger.info(f"Ended deployment tracking with status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end deployment tracking: {str(e)}")
            return False
    
    def _save_deployment_status(self, deployment: DeploymentStatus):
        """Save deployment status to file.
        
        Args:
            deployment: Deployment status to save
        """
        try:
            status_dir = self.config_dir / "status"
            status_dir.mkdir(parents=True, exist_ok=True)
            
            status_file = status_dir / f"deployment_{deployment.version}_{deployment.environment}.json"
            
            with open(status_file, 'w') as f:
                json.dump(asdict(deployment), f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to save deployment status: {str(e)}")
    
    def _cleanup_old_deployments(self):
        """Clean up old deployment status files."""
        try:
            status_dir = self.config_dir / "status"
            if not status_dir.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.config["retention_days"])
            
            for status_file in status_dir.glob("deployment_*.json"):
                try:
                    with open(status_file, 'r') as f:
                        status = json.load(f)
                    
                    end_time = datetime.fromisoformat(status["end_time"])
                    if end_time < cutoff_date:
                        status_file.unlink()
                        logger.info(f"Deleted old deployment status: {status_file}")
                        
                except Exception as e:
                    logger.error(f"Failed to process status file {status_file}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old deployments: {str(e)}")
    
    def get_current_deployment(self) -> Optional[Dict[str, Any]]:
        """Get current deployment status.
        
        Returns:
            Current deployment status if available
        """
        if self.current_deployment:
            return asdict(self.current_deployment)
        return None
    
    def get_deployment_history(self, environment: Optional[str] = None,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get deployment history.
        
        Args:
            environment: Optional environment filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of deployment statuses
        """
        try:
            filtered_history = []
            
            for deployment in self.deployment_history:
                if environment and deployment.environment != environment:
                    continue
                if start_time and deployment.start_time < start_time:
                    continue
                if end_time and deployment.end_time and deployment.end_time > end_time:
                    continue
                
                filtered_history.append(asdict(deployment))
            
            return filtered_history
            
        except Exception as e:
            logger.error(f"Failed to get deployment history: {str(e)}")
            return []
    
    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Get latest system metrics.
        
        Returns:
            Latest metrics if available
        """
        try:
            if self.current_deployment and self.current_deployment.metrics:
                return asdict(self.current_deployment.metrics[-1])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest metrics: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    monitor = DeploymentMonitor()
    
    # Start deployment tracking
    monitor.start_deployment("v1.2.3", "prod")
    
    # Wait for some metrics
    time.sleep(5)
    
    # Get current status
    status = monitor.get_current_deployment()
    print("Current deployment:", status)
    
    # End deployment
    monitor.end_deployment("completed")
    
    # Get history
    history = monitor.get_deployment_history(environment="prod")
    print("Deployment history:", history) 