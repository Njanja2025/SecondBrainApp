"""
Main entry point for SecondBrain
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from .brain_controller import BrainController
from .memory.diagnostic_memory_core import DiagnosticMemoryCore
from .persona.adaptive_learning import PersonaLearningModule
from .core.strategic_planner import StrategicPlanner
from .utils.logger import setup_logger
from .utils.config import Config


def setup_environment():
    """Set up the application environment."""
    # Load environment variables
    load_dotenv()

    # Set up logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.path.join(
        os.getenv("SECONDBRAIN_BASE_DIR", "~"), "logs", "secondbrain.log"
    )
    logger = setup_logger(level=log_level, log_file=log_file)

    # Create necessary directories
    base_dir = Path(
        os.path.expanduser(os.getenv("SECONDBRAIN_BASE_DIR", "~/.secondbrain"))
    )
    for dir_name in ["logs", "data", "config", "memory"]:
        (base_dir / dir_name).mkdir(parents=True, exist_ok=True)

    return logger


async def main():
    """Main entry point."""
    try:
        # Set up environment
        logger = setup_environment()
        logger.info("Starting SecondBrain...")

        # Initialize components
        memory_core = DiagnosticMemoryCore()
        learning_module = PersonaLearningModule()
        strategic_planner = StrategicPlanner()

        # Initialize brain controller
        brain = BrainController(
            memory_core=memory_core,
            learning_module=learning_module,
            strategic_planner=strategic_planner,
        )

        # Start the brain
        await brain.initialize()

        # Keep the application running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if "brain" in locals():
            await brain.stop()
        logger.info("SecondBrain stopped")


if __name__ == "__main__":
    asyncio.run(main())
