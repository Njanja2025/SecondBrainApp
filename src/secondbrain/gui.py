"""
GUI module for SecondBrainApp
"""

import pygame
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .utils.hotkey import Hotkey
from .utils.config import Config
from .utils.logger import setup_logger

logger = logging.getLogger(__name__)


class GUI:
    """Main GUI class for SecondBrainApp."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the GUI."""
        self.config = config or Config()
        self.hotkey_manager = Hotkey()
        self.setup_logging()
        self.initialize_pygame()

    def setup_logging(self):
        """Configure logging for the GUI."""
        setup_logger("gui", self.config.log_level)

    def initialize_pygame(self):
        """Initialize pygame and set up the display."""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("SecondBrainApp 2025")

    def run(self):
        """Main GUI loop."""
        try:
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                # Update display
                self.screen.fill((255, 255, 255))
                pygame.display.flip()

        except Exception as e:
            logger.error(f"GUI error: {e}")
        finally:
            pygame.quit()

    def register_hotkeys(self):
        """Register default hotkeys."""
        self.hotkey_manager.register("ctrl+q", lambda: self.quit())
        self.hotkey_manager.register("ctrl+h", lambda: self.show_help())

    def quit(self):
        """Clean up and quit the application."""
        logger.info("Shutting down SecondBrainApp")
        pygame.quit()

    def show_help(self):
        """Display help information."""
        logger.info("Showing help information")
        # TODO: Implement help display
