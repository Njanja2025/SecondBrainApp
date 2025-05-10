"""
Schedule manager for handling scheduled reports.
Manages report scheduling, execution, and monitoring.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import schedule
import time
import threading
import pytz
from croniter import croniter

logger = logging.getLogger(__name__)

@dataclass
class ScheduleConfig:
    """Configuration for scheduled reports."""
    name: str
    report_config: str
    schedule_type: str  # interval, cron, datetime
    schedule_value: str  # interval in seconds, cron expression, or datetime
    timezone: str = "UTC"
    enabled: bool = True
    retry_count: int = 3
    retry_delay: int = 300  # seconds
    metadata: Dict[str, Any] = None
    description: str = None

class ScheduleManager:
    """Manages scheduled reports and execution."""
    
    def __init__(self, config_dir: str = "config/schedules"):
        """Initialize the schedule manager.
        
        Args:
            config_dir: Directory to store schedule configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self.running = False
        self.jobs = {}
        self._setup_scheduler()
    
    def _setup_logging(self):
        """Set up logging for the schedule manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load schedule configurations."""
        try:
            config_file = self.config_dir / "schedule_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: ScheduleConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Schedule configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load schedule configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save schedule configurations."""
        try:
            config_file = self.config_dir / "schedule_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save schedule configurations: {str(e)}")
    
    def create_config(self, config: ScheduleConfig) -> bool:
        """Create a new schedule configuration.
        
        Args:
            config: Schedule configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            if config.enabled:
                self._schedule_job(config)
            
            logger.info(f"Created schedule configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create schedule configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: ScheduleConfig) -> bool:
        """Update an existing schedule configuration.
        
        Args:
            name: Configuration name
            config: New schedule configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            # Cancel existing job if running
            if name in self.jobs:
                schedule.cancel_job(self.jobs[name])
                del self.jobs[name]
            
            self.configs[name] = config
            self._save_configs()
            
            if config.enabled:
                self._schedule_job(config)
            
            logger.info(f"Updated schedule configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update schedule configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete a schedule configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            bool: True if configuration was deleted successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            # Cancel existing job if running
            if name in self.jobs:
                schedule.cancel_job(self.jobs[name])
                del self.jobs[name]
            
            del self.configs[name]
            self._save_configs()
            
            logger.info(f"Deleted schedule configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete schedule configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[ScheduleConfig]:
        """Get schedule configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Schedule configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all schedule configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def _setup_scheduler(self):
        """Set up the scheduler."""
        try:
            # Schedule all enabled configurations
            for config in self.configs.values():
                if config.enabled:
                    self._schedule_job(config)
            
            logger.info("Scheduler set up")
            
        except Exception as e:
            logger.error(f"Failed to set up scheduler: {str(e)}")
            raise
    
    def _schedule_job(self, config: ScheduleConfig):
        """Schedule a job based on configuration.
        
        Args:
            config: Schedule configuration
        """
        try:
            if config.schedule_type == "interval":
                job = schedule.every(int(config.schedule_value)).seconds.do(
                    self._execute_job, config.name
                )
            elif config.schedule_type == "cron":
                job = schedule.every().day.at(
                    self._get_next_cron_time(config.schedule_value, config.timezone)
                ).do(self._execute_job, config.name)
            elif config.schedule_type == "datetime":
                job = schedule.every().day.at(
                    datetime.strptime(config.schedule_value, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                ).do(self._execute_job, config.name)
            else:
                logger.error(f"Unsupported schedule type: {config.schedule_type}")
                return
            
            self.jobs[config.name] = job
            logger.info(f"Scheduled job {config.name}")
            
        except Exception as e:
            logger.error(f"Failed to schedule job {config.name}: {str(e)}")
    
    def _get_next_cron_time(self, cron_expr: str, timezone: str) -> str:
        """Get next execution time from cron expression.
        
        Args:
            cron_expr: Cron expression
            timezone: Timezone
            
        Returns:
            Next execution time in HH:MM format
        """
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            cron = croniter(cron_expr, now)
            next_time = cron.get_next(datetime)
            return next_time.strftime("%H:%M")
            
        except Exception as e:
            logger.error(f"Failed to get next cron time: {str(e)}")
            return "00:00"
    
    def _execute_job(self, config_name: str):
        """Execute a scheduled job.
        
        Args:
            config_name: Configuration name
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return
            
            # Execute report generation
            # This is a placeholder - implement actual report generation
            logger.info(f"Executing scheduled job {config_name}")
            
            # Reschedule if using cron
            if config.schedule_type == "cron":
                self._schedule_job(config)
            
        except Exception as e:
            logger.error(f"Failed to execute job {config_name}: {str(e)}")
            
            # Handle retries
            if config.retry_count > 0:
                config.retry_count -= 1
                time.sleep(config.retry_delay)
                self._execute_job(config_name)
    
    def start(self):
        """Start the scheduler."""
        try:
            self.running = True
            
            def run_scheduler():
                while self.running:
                    schedule.run_pending()
                    time.sleep(1)
            
            self.scheduler_thread = threading.Thread(target=run_scheduler)
            self.scheduler_thread.start()
            
            logger.info("Scheduler started")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    def stop(self):
        """Stop the scheduler."""
        try:
            self.running = False
            if hasattr(self, 'scheduler_thread'):
                self.scheduler_thread.join()
            
            logger.info("Scheduler stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    manager = ScheduleManager()
    
    # Create schedule configuration
    config = ScheduleConfig(
        name="daily_user_report",
        report_config="user_report",
        schedule_type="cron",
        schedule_value="0 0 * * *",  # Daily at midnight
        timezone="UTC",
        retry_count=3,
        retry_delay=300,
        description="Daily user report schedule"
    )
    manager.create_config(config)
    
    # Start scheduler
    manager.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop scheduler on Ctrl+C
        manager.stop() 