"""
Scheduler for automatic cloud backups and DNS updates.
"""
import logging
import asyncio
from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from .cloud_sync import CloudSync
from .dns_manager import DNSManager

logger = logging.getLogger(__name__)

class BackupScheduler:
    """Manages scheduled backups and DNS updates."""
    
    def __init__(
        self,
        config_path: str = "config/scheduler.json",
        backup_paths: Optional[Dict[str, str]] = None
    ):
        self.config_path = Path(config_path)
        
        # Default backup paths
        self.backup_paths = backup_paths or {
            "memory": "data/memory/samantha_memory.json",
            "voice_logs": "logs/voice",
            "emotional_logs": "logs/emotional",
            "gui_logs": "logs/gui"
        }
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.cloud_sync = CloudSync()
        self.dns_manager = DNSManager()
        
        # Active tasks
        self.tasks = []
        
        # Load environment variables
        load_dotenv()
        
    def _load_config(self) -> Dict:
        """Load scheduler configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    return json.load(f)
            return {
                "backup_schedule": {
                    "memory": {
                        "frequency": "weekly",
                        "day": "sunday",
                        "time": "00:00"
                    },
                    "voice_logs": {
                        "frequency": "daily",
                        "time": "23:00"
                    },
                    "emotional_logs": {
                        "frequency": "daily",
                        "time": "23:30"
                    },
                    "gui_logs": {
                        "frequency": "daily",
                        "time": "23:45"
                    }
                },
                "dns_check_interval": 21600,  # 6 hours
                "enabled": True
            }
        except Exception as e:
            logger.error(f"Failed to load scheduler config: {e}")
            return {}
            
    async def start(self):
        """Start all scheduled tasks."""
        if not self.config.get("enabled", True):
            logger.info("Scheduler is disabled")
            return
            
        try:
            # Start backup tasks
            self.tasks.extend([
                asyncio.create_task(self._run_memory_backup()),
                asyncio.create_task(self._run_voice_logs_backup()),
                asyncio.create_task(self._run_emotional_logs_backup()),
                asyncio.create_task(self._run_gui_logs_backup())
            ])
            
            # Start DNS check task
            self.tasks.append(
                asyncio.create_task(self._run_dns_checks())
            )
            
            logger.info("Started all scheduled tasks")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            
    async def stop(self):
        """Stop all scheduled tasks."""
        for task in self.tasks:
            task.cancel()
            
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        
    async def _run_memory_backup(self):
        """Run memory backup task."""
        while True:
            try:
                schedule = self.config["backup_schedule"]["memory"]
                
                # Calculate next run time
                next_run = self._calculate_next_run(schedule)
                await asyncio.sleep(next_run)
                
                # Perform backup
                await self._backup_memory()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory backup task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
                
    async def _run_voice_logs_backup(self):
        """Run voice logs backup task."""
        while True:
            try:
                schedule = self.config["backup_schedule"]["voice_logs"]
                
                # Calculate next run time
                next_run = self._calculate_next_run(schedule)
                await asyncio.sleep(next_run)
                
                # Perform backup
                await self._backup_voice_logs()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in voice logs backup task: {e}")
                await asyncio.sleep(300)
                
    async def _run_emotional_logs_backup(self):
        """Run emotional logs backup task."""
        while True:
            try:
                schedule = self.config["backup_schedule"]["emotional_logs"]
                
                # Calculate next run time
                next_run = self._calculate_next_run(schedule)
                await asyncio.sleep(next_run)
                
                # Perform backup
                await self._backup_emotional_logs()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in emotional logs backup task: {e}")
                await asyncio.sleep(300)
                
    async def _run_gui_logs_backup(self):
        """Run GUI logs backup task."""
        while True:
            try:
                schedule = self.config["backup_schedule"]["gui_logs"]
                
                # Calculate next run time
                next_run = self._calculate_next_run(schedule)
                await asyncio.sleep(next_run)
                
                # Perform backup
                await self._backup_gui_logs()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in GUI logs backup task: {e}")
                await asyncio.sleep(300)
                
    async def _run_dns_checks(self):
        """Run periodic DNS checks."""
        while True:
            try:
                # Get check interval
                interval = self.config.get("dns_check_interval", 21600)
                
                # Perform DNS checks
                await self._check_and_update_dns()
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in DNS check task: {e}")
                await asyncio.sleep(300)
                
    async def _backup_memory(self):
        """Perform memory backup to all configured services."""
        try:
            memory_path = Path(self.backup_paths["memory"])
            if not memory_path.exists():
                logger.warning(f"Memory file not found: {memory_path}")
                return
                
            # Backup to Dropbox
            if os.getenv("DROPBOX_ACCESS_TOKEN"):
                await self.cloud_sync.upload_to_dropbox(
                    str(memory_path),
                    os.getenv("DROPBOX_ACCESS_TOKEN")
                )
                
            # Backup to Google Drive
            if os.getenv("GOOGLE_DRIVE_CREDENTIALS"):
                await self.cloud_sync.upload_to_drive(
                    str(memory_path),
                    os.getenv("GOOGLE_DRIVE_CREDENTIALS"),
                    os.getenv("GOOGLE_DRIVE_FOLDER_ID")
                )
                
            # Backup to AWS S3
            if all([
                os.getenv("AWS_ACCESS_KEY"),
                os.getenv("AWS_SECRET_KEY"),
                os.getenv("AWS_BUCKET_NAME")
            ]):
                await self.cloud_sync.upload_to_s3(
                    str(memory_path),
                    os.getenv("AWS_BUCKET_NAME"),
                    os.getenv("AWS_ACCESS_KEY"),
                    os.getenv("AWS_SECRET_KEY"),
                    os.getenv("AWS_REGION", "us-east-1")
                )
                
        except Exception as e:
            logger.error(f"Failed to backup memory: {e}")
            
    async def _backup_voice_logs(self):
        """Backup voice logs to configured services."""
        try:
            voice_logs_dir = Path(self.backup_paths["voice_logs"])
            if not voice_logs_dir.exists():
                logger.warning(f"Voice logs directory not found: {voice_logs_dir}")
                return
                
            # Create archive of voice logs
            archive_name = f"voice_logs_{datetime.now().strftime('%Y%m%d')}.zip"
            archive_path = voice_logs_dir / archive_name
            
            # TODO: Implement archive creation
            
            # Backup archive to configured services
            # Similar to memory backup
            
        except Exception as e:
            logger.error(f"Failed to backup voice logs: {e}")
            
    async def _backup_emotional_logs(self):
        """Backup emotional logs to configured services."""
        try:
            emotional_logs_dir = Path(self.backup_paths["emotional_logs"])
            if not emotional_logs_dir.exists():
                logger.warning(f"Emotional logs directory not found: {emotional_logs_dir}")
                return
                
            # Similar to voice logs backup
            
        except Exception as e:
            logger.error(f"Failed to backup emotional logs: {e}")
            
    async def _backup_gui_logs(self):
        """Backup GUI logs to configured services."""
        try:
            gui_logs_dir = Path(self.backup_paths["gui_logs"])
            if not gui_logs_dir.exists():
                logger.warning(f"GUI logs directory not found: {gui_logs_dir}")
                return
                
            # Similar to voice logs backup
            
        except Exception as e:
            logger.error(f"Failed to backup GUI logs: {e}")
            
    async def _check_and_update_dns(self):
        """Check and update DNS records if needed."""
        try:
            # Get Namecheap credentials
            api_user = os.getenv("NAMECHEAP_API_USER")
            api_key = os.getenv("NAMECHEAP_API_KEY")
            
            if not all([api_user, api_key]):
                return
                
            # Check each configured domain
            for domain_config in self.dns_manager.config.get("domains", []):
                domain = domain_config["domain"]
                
                for subdomain in domain_config["subdomains"]:
                    # Get current IP
                    current_ip = os.getenv("SERVER_IP")
                    if not current_ip:
                        continue
                        
                    # Verify DNS
                    if not await self.dns_manager.verify_dns(
                        domain,
                        subdomain,
                        current_ip
                    ):
                        # Update if verification fails
                        await self.dns_manager.update_namecheap_dns(
                            api_user,
                            api_key,
                            domain,
                            subdomain,
                            current_ip
                        )
                        
        except Exception as e:
            logger.error(f"Failed to check/update DNS: {e}")
            
    def _calculate_next_run(self, schedule: Dict) -> float:
        """Calculate seconds until next scheduled run."""
        try:
            now = datetime.now()
            frequency = schedule["frequency"]
            
            if frequency == "daily":
                # Parse scheduled time
                hour, minute = map(int, schedule["time"].split(":"))
                next_run = now.replace(
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                )
                
                # If time already passed, schedule for tomorrow
                if next_run <= now:
                    next_run += timedelta(days=1)
                    
            elif frequency == "weekly":
                # Get scheduled day and time
                day = schedule["day"].lower()
                hour, minute = map(int, schedule["time"].split(":"))
                
                # Calculate days until next scheduled day
                days_ahead = {
                    "monday": 0, "tuesday": 1, "wednesday": 2,
                    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
                }
                current_day = now.weekday()
                days_until = days_ahead[day] - current_day
                
                if days_until <= 0:
                    days_until += 7
                    
                next_run = now.replace(
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                ) + timedelta(days=days_until)
                
            else:
                raise ValueError(f"Unsupported frequency: {frequency}")
                
            # Return seconds until next run
            return (next_run - now).total_seconds()
            
        except Exception as e:
            logger.error(f"Failed to calculate next run time: {e}")
            return 300  # Default to 5 minutes
            
    def save_config(self):
        """Save current configuration."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save scheduler config: {e}")
            
    def update_schedule(self, backup_type: str, schedule: Dict):
        """Update backup schedule configuration."""
        if backup_type in self.config["backup_schedule"]:
            self.config["backup_schedule"][backup_type].update(schedule)
            self.save_config() 