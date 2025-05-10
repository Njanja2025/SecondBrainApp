"""
Test runner for cloud backup and DNS systems.
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List
import fpdf

from .scheduler import BackupScheduler
from .env_loader import EnvironmentLoader
from .cloud_sync import CloudSync
from .dns_manager import DNSManager
from .voice_feedback import VoiceFeedback
from .log_reporter import BackupLogReport

logger = logging.getLogger(__name__)

class BackupTestRunner:
    """Runs integration tests for backup and DNS systems."""
    
    def __init__(self):
        """Initialize test runner with all required components."""
        # Initialize environment
        self.env_loader = EnvironmentLoader()
        self.env_vars = self.env_loader.get_all_vars()
        
        # Configure email settings
        email_config = {
            'to_email': "lloydkavh77@gmail.com",
            'from_email': "admin@njanja.net",
            'smtp_server': "smtp.namecheap.com",
            'smtp_port': 465,
            'smtp_user': "admin@njanja.net",
            'smtp_pass': os.getenv("EMAIL_PASSWORD")
        }
        
        # Initialize components
        self.scheduler = BackupScheduler()
        self.cloud_sync = CloudSync()
        self.dns_manager = DNSManager()
        self.voice = VoiceFeedback()
        self.log_reporter = BackupLogReport(email_config=email_config)
        
        # Test results storage
        self.test_results: List[Dict] = []
        
    async def run_memory_backup_test(self):
        """Test weekly memory backup functionality."""
        logger.info("Testing weekly memory backup...")
        await self.voice.notify_backup_start("memory")
        self.log_reporter.log_event("backup", "Starting memory backup")
        
        try:
            memory_path = Path("data/memory/samantha_memory.json")
            
            # Create test memory file if it doesn't exist
            if not memory_path.exists():
                memory_path.parent.mkdir(parents=True, exist_ok=True)
                with open(memory_path, 'w') as f:
                    json.dump({"test": "data"}, f)
            
            # Test Dropbox backup
            dropbox_result = await self.cloud_sync.upload_to_dropbox(
                str(memory_path),
                self.env_vars['cloud']['DROPBOX_ACCESS_TOKEN']
            )
            
            # Test Google Drive backup
            drive_result = await self.cloud_sync.upload_to_drive(
                str(memory_path),
                self.env_vars['cloud']['GOOGLE_DRIVE_CREDENTIALS'],
                self.env_vars['cloud']['GOOGLE_DRIVE_FOLDER_ID']
            )
            
            # Test S3 backup
            s3_result = await self.cloud_sync.upload_to_s3(
                str(memory_path),
                self.env_vars['cloud']['AWS_BUCKET_NAME'],
                self.env_vars['cloud']['AWS_ACCESS_KEY'],
                self.env_vars['cloud']['AWS_SECRET_KEY'],
                self.env_vars['cloud']['AWS_REGION']
            )
            
            success = all([dropbox_result, drive_result, s3_result])
            
            if success:
                await self.voice.notify_backup_success("memory")
                self.log_reporter.log_event(
                    "backup",
                    "Memory backup completed successfully",
                    "SUCCESS",
                    {
                        "dropbox": dropbox_result,
                        "drive": drive_result,
                        "s3": s3_result
                    }
                )
            else:
                raise Exception("One or more backup services failed")
            
            return success
            
        except Exception as e:
            error_msg = f"Memory backup test failed: {e}"
            logger.error(error_msg)
            await self.voice.notify_backup_failure("memory", str(e))
            self.log_reporter.log_event("backup", error_msg, "ERROR")
            return False
            
    async def run_voice_log_backup_test(self):
        """Test nightly voice log backup functionality."""
        logger.info("Testing voice log backup...")
        await self.voice.notify_backup_start("voice log")
        self.log_reporter.log_event("backup", "Starting voice log backup")
        
        try:
            voice_log_dir = Path("logs/voice")
            voice_log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create test voice log
            test_log = voice_log_dir / "test_voice.log"
            test_log.write_text("Test voice log entry")
            
            # Test backups
            results = []
            services = {
                'dropbox': self.cloud_sync.upload_to_dropbox,
                'drive': self.cloud_sync.upload_to_drive,
                's3': self.cloud_sync.upload_to_s3
            }
            
            for service_name, upload_func in services.items():
                try:
                    if service_name == 'dropbox':
                        result = await upload_func(
                            str(test_log),
                            self.env_vars['cloud']['DROPBOX_ACCESS_TOKEN']
                        )
                    elif service_name == 'drive':
                        result = await upload_func(
                            str(test_log),
                            self.env_vars['cloud']['GOOGLE_DRIVE_CREDENTIALS'],
                            self.env_vars['cloud']['GOOGLE_DRIVE_FOLDER_ID']
                        )
                    else:  # s3
                        result = await upload_func(
                            str(test_log),
                            self.env_vars['cloud']['AWS_BUCKET_NAME'],
                            self.env_vars['cloud']['AWS_ACCESS_KEY'],
                            self.env_vars['cloud']['AWS_SECRET_KEY'],
                            self.env_vars['cloud']['AWS_REGION']
                        )
                    results.append(result)
                    
                    if result:
                        self.log_reporter.log_event(
                            "backup",
                            f"{service_name.title()} voice log backup successful",
                            "SUCCESS"
                        )
                    else:
                        self.log_reporter.log_event(
                            "backup",
                            f"{service_name.title()} voice log backup failed",
                            "ERROR"
                        )
                        
                except Exception as e:
                    logger.error(f"{service_name.title()} backup failed: {e}")
                    results.append(False)
                    self.log_reporter.log_event(
                        "backup",
                        f"{service_name.title()} voice log backup error: {e}",
                        "ERROR"
                    )
            
            success = all(results)
            if success:
                await self.voice.notify_backup_success("voice log")
            else:
                await self.voice.notify_backup_failure("voice log")
            
            return success
            
        except Exception as e:
            error_msg = f"Voice log backup test failed: {e}"
            logger.error(error_msg)
            await self.voice.notify_backup_failure("voice log", str(e))
            self.log_reporter.log_event("backup", error_msg, "ERROR")
            return False
            
    async def run_dns_health_test(self):
        """Test DNS health check functionality."""
        logger.info("Testing DNS health check...")
        self.log_reporter.log_event("dns", "Starting DNS health check")
        
        try:
            # Get DNS credentials
            dns_vars = self.env_vars['dns']
            
            # Test DNS verification
            verify_result = await self.dns_manager.verify_dns(
                "njanja.net",  # Replace with your domain
                "samantha",    # Replace with your subdomain
                dns_vars['SERVER_IP']
            )
            
            self.log_reporter.log_event(
                "dns",
                "DNS verification completed",
                "SUCCESS" if verify_result else "WARNING",
                {"verified": verify_result}
            )
            
            # Test DNS update if verification fails
            update_result = True
            if not verify_result:
                self.log_reporter.log_event("dns", "DNS verification failed, attempting update")
                update_result = await self.dns_manager.update_namecheap_dns(
                    dns_vars['NAMECHEAP_API_USER'],
                    dns_vars['NAMECHEAP_API_KEY'],
                    "njanja.net",
                    "samantha",
                    dns_vars['SERVER_IP']
                )
                
                self.log_reporter.log_event(
                    "dns",
                    "DNS update completed",
                    "SUCCESS" if update_result else "ERROR",
                    {"updated": update_result}
                )
            
            success = verify_result or update_result
            await self.voice.notify_dns_status(success)
            
            return success
            
        except Exception as e:
            error_msg = f"DNS health test failed: {e}"
            logger.error(error_msg)
            await self.voice.notify_dns_status(False, str(e))
            self.log_reporter.log_event("dns", error_msg, "ERROR")
            return False
            
    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting integration tests...")
        await self.voice.speak("Starting integration tests...")
        
        results = await asyncio.gather(
            self.run_memory_backup_test(),
            self.run_voice_log_backup_test(),
            self.run_dns_health_test()
        )
        
        # Generate final report
        report_path = self.log_reporter.generate_report()
        if report_path:
            await self.voice.speak("Test report generated successfully.")
            logger.info(f"Test report available at: {report_path}")
        
        success = all(results)
        await self.voice.speak(
            "All tests completed successfully!" if success else "Some tests failed. Please check the report."
        )
        
        return success

async def run_tests():
    """Run all integration tests and return results."""
    runner = BackupTestRunner()
    success = await runner.run_all_tests()
    return success

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n[TEST] Running full integration test...")
    success = asyncio.run(run_tests())
    print(f"\n[TEST COMPLETED] {'All tests passed!' if success else 'Some tests failed.'}") 