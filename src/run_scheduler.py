"""
Script to run the cloud backup and DNS update scheduler.
"""

import asyncio
import logging
import sys
from pathlib import Path
from secondbrain.cloud.scheduler import BackupScheduler
from secondbrain.cloud.env_loader import EnvironmentLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    try:
        # Initialize and validate environment variables
        env_loader = EnvironmentLoader()
        env_vars = env_loader.get_all_vars()

        # Initialize scheduler with validated environment
        scheduler = BackupScheduler()

        # Start scheduler
        await scheduler.start()

        logger.info("Scheduler started successfully")

        # Keep running
        while True:
            await asyncio.sleep(60)

    except EnvironmentError as e:
        logger.error(f"Environment configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        if "scheduler" in locals():
            await scheduler.stop()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if "scheduler" in locals():
            await scheduler.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
