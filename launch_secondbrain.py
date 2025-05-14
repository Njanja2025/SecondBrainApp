#!/usr/bin/env python3
"""
SecondBrain App Launcher
A code-level launch script for the SecondBrain application.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("launch.log")],
)
logger = logging.getLogger(__name__)


def setup_environment() -> None:
    """Set up the Python environment and paths."""
    # Add app_core to Python path
    app_core_path = Path(__file__).parent / "app_core"
    if app_core_path.exists():
        sys.path.append(str(app_core_path))
    else:
        logger.error("app_core directory not found!")
        sys.exit(1)


def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    try:
        import PyQt5
        import numpy
        import pandas
        import requests

        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False


def initialize_app() -> Optional[object]:
    """Initialize the main application."""
    try:
        from app_core.njax import NjaxEngine
        from app_core.vault import VaultManager
        from app_core.voice import VoiceAssistant
        from app_core.forge import ForgeManager

        # Initialize core components
        engine = NjaxEngine()
        vault = VaultManager()
        voice = VoiceAssistant()
        forge = ForgeManager()

        return {"engine": engine, "vault": vault, "voice": voice, "forge": forge}
    except Exception as e:
        logger.error(f"Failed to initialize app: {e}")
        return None


def main():
    """Main entry point for the application."""
    logger.info("Starting SecondBrain App...")

    # Setup environment
    setup_environment()

    # Check dependencies
    if not check_dependencies():
        logger.error(
            "Please install required dependencies: pip install -r requirements.txt"
        )
        sys.exit(1)

    # Initialize app
    app = initialize_app()
    if not app:
        logger.error("Failed to initialize application")
        sys.exit(1)

    logger.info("SecondBrain App initialized successfully!")

    # TODO: Launch main UI or CLI based on configuration
    # For now, just keep the app running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Shutting down SecondBrain App...")
        sys.exit(0)


if __name__ == "__main__":
    main()
