#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Suppress warnings and noise
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress specific module logging
logging.getLogger("moviepy").setLevel(logging.ERROR)
logging.getLogger("matplotlib").setLevel(logging.ERROR)
logging.getLogger("PIL").setLevel(logging.ERROR)


def main():
    try:
        logger.info("Starting SecondBrain application...")
        # Add your main application code here
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
