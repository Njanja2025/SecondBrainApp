#!/usr/bin/env python3
"""
SecondBrain AI - Main Entry Point
"""
import os
import sys
import asyncio
import logging
import platform
import psutil
import json
from datetime import datetime
from typing import Dict, Any
from secondbrain.ai_agent import AIAgent
from secondbrain.phantom.phantom_core import PhantomCore
from pathlib import Path
import argparse
from secondbrain.cloud.test_runner import run_tests
from secondbrain.cloud.scheduler import BackupScheduler

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/secondbrain.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class SystemCheck:
    @staticmethod
    def check_system_requirements() -> Dict[str, Any]:
        """Check if system meets requirements."""
        checks = {
            "os_version": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_cores": psutil.cpu_count(),
            "memory_available": psutil.virtual_memory().available
            / (1024 * 1024 * 1024),  # GB
            "disk_space": psutil.disk_usage("/").free / (1024 * 1024 * 1024),  # GB
        }

        requirements = {
            "min_python_version": "3.8.0",
            "min_cpu_cores": 2,
            "min_memory_gb": 4,
            "min_disk_space_gb": 1,
        }

        status = {"passed": True, "checks": checks, "issues": []}

        # Check Python version
        if platform.python_version_tuple() < tuple(
            requirements["min_python_version"].split(".")
        ):
            status["passed"] = False
            status["issues"].append(
                f"Python version must be >= {requirements['min_python_version']}"
            )

        # Check CPU cores
        if checks["cpu_cores"] < requirements["min_cpu_cores"]:
            status["passed"] = False
            status["issues"].append(
                f"Need at least {requirements['min_cpu_cores']} CPU cores"
            )

        # Check memory
        if checks["memory_available"] < requirements["min_memory_gb"]:
            status["passed"] = False
            status["issues"].append(
                f"Need at least {requirements['min_memory_gb']}GB available memory"
            )

        # Check disk space
        if checks["disk_space"] < requirements["min_disk_space_gb"]:
            status["passed"] = False
            status["issues"].append(
                f"Need at least {requirements['min_disk_space_gb']}GB free disk space"
            )

        return status


class SecondBrainApp:
    def __init__(self):
        """Initialize SecondBrain application."""
        self.agent = AIAgent()
        self.phantom = PhantomCore()
        self.system_monitor = SystemCheck()

    async def _check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        try:
            import web3
            import whisper
            import gtts
            import cryptography

            return True
        except ImportError as e:
            self.phantom.log_event(
                "Dependency Check", f"Missing dependency: {str(e)}", "ERROR"
            )
            return False

    async def _verify_directories(self) -> bool:
        """Verify and create required directories."""
        required_dirs = ["phantom_logs", "config", "data"]

        try:
            for directory in required_dirs:
                os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            self.phantom.log_event(
                "Directory Check", f"Error creating directories: {str(e)}", "ERROR"
            )
            return False

    async def startup(self):
        """Perform startup sequence."""
        try:
            # System requirements check
            system_status = self.system_monitor.check_system_requirements()
            if not system_status["passed"]:
                issues = "\n".join(system_status["issues"])
                raise Exception(f"System requirements not met:\n{issues}")

            self.phantom.log_event(
                "System Check",
                f"System requirements verified: {json.dumps(system_status['checks'])}",
            )

            # Check dependencies
            if not await self._check_dependencies():
                raise Exception("Missing required dependencies")

            # Verify directories
            if not await self._verify_directories():
                raise Exception("Failed to create required directories")

            # Announce activation
            os.system("say 'Second Brain is now active in Phantom Mode.'")

            # Log startup
            self.phantom.log_event(
                "System Startup",
                f"SecondBrain initialized at {datetime.now().isoformat()}",
            )

            # Start AI Agent
            await self.agent.start()

            # Save initial logs
            self.phantom.save_log()

        except Exception as e:
            error_msg = f"Startup error: {str(e)}"
            self.phantom.log_event("Startup Error", error_msg, "ERROR")
            logger.error(error_msg)
            os.system("say 'Error during startup. Please check logs.'")
            sys.exit(1)

    async def shutdown(self):
        """Perform graceful shutdown."""
        try:
            # Stop AI Agent
            await self.agent.stop()

            # Log shutdown
            self.phantom.log_event(
                "System Shutdown",
                f"SecondBrain shutdown at {datetime.now().isoformat()}",
            )

            # Save final logs
            self.phantom.save_log()

            os.system("say 'Second Brain shutting down.'")

        except Exception as e:
            error_msg = f"Shutdown error: {str(e)}"
            self.phantom.log_event("Shutdown Error", error_msg, "ERROR")
            logger.error(error_msg)
            os.system("say 'Error during shutdown.'")

    async def monitor_system(self):
        """Monitor system resources and health."""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")

                if cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                    self.phantom.log_event(
                        "System Monitor",
                        f"High resource usage - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%",
                        "WARNING",
                    )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.phantom.log_event(
                    "Monitor Error", f"Error monitoring system: {str(e)}", "ERROR"
                )
                await asyncio.sleep(60)


async def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="SecondBrain AI Assistant")
    parser.add_argument("--test", action="store_true", help="Run integration tests")
    args = parser.parse_args()

    try:
        # Create necessary directories
        Path("logs").mkdir(exist_ok=True)
        Path("data/memory").mkdir(parents=True, exist_ok=True)

        # Run tests if requested
        if args.test:
            logger.info("Running integration tests...")
            success = await run_tests()
            if not success:
                logger.error("Integration tests failed")
                return

        # Initialize and start scheduler
        scheduler = BackupScheduler()
        await scheduler.start()

        # Keep the application running
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if "scheduler" in locals():
            await scheduler.stop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        if "scheduler" in locals():
            await scheduler.stop()


if __name__ == "__main__":
    # Ensure phantom_logs directory exists
    os.makedirs("phantom_logs", exist_ok=True)

    # Run the application
    asyncio.run(main())
