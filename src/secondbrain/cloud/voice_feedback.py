"""
Voice feedback module for SecondBrain cloud operations.
"""

import logging
import pyttsx3
import asyncio
from typing import Optional
from functools import partial

logger = logging.getLogger(__name__)


class VoiceFeedback:
    """Manages voice feedback for cloud operations."""

    def __init__(self):
        """Initialize voice feedback system."""
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        """Initialize text-to-speech engine."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 150)  # Slightly slower for clarity
            self._engine.setProperty("volume", 0.9)
        except Exception as e:
            logger.error(f"Failed to initialize voice engine: {e}")
            self._engine = None

    async def speak(self, message: str, priority: bool = False):
        """
        Speak a message asynchronously.

        Args:
            message: The message to speak
            priority: If True, interrupt any ongoing speech
        """
        if not self._engine:
            logger.error("Voice engine not available")
            return

        try:
            # Run speech in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, partial(self._speak_sync, message, priority)
            )
        except Exception as e:
            logger.error(f"Failed to speak message: {e}")

    def _speak_sync(self, message: str, priority: bool):
        """Synchronous speak function."""
        try:
            if priority:
                self._engine.stop()
            self._engine.say(message)
            self._engine.runAndWait()
        except Exception as e:
            logger.error(f"Error during speech: {e}")

    async def notify_backup_start(self, backup_type: str):
        """Notify backup start."""
        await self.speak(f"Starting {backup_type} backup...")

    async def notify_backup_success(self, backup_type: str):
        """Notify backup success."""
        await self.speak(f"{backup_type} backup completed successfully.")

    async def notify_backup_failure(
        self, backup_type: str, error: Optional[str] = None
    ):
        """Notify backup failure."""
        message = f"{backup_type} backup failed"
        if error:
            message += f": {error}"
        await self.speak(message, priority=True)

    async def notify_dns_status(self, success: bool, error: Optional[str] = None):
        """Notify DNS check status."""
        if success:
            await self.speak("DNS health check passed.")
        else:
            message = "DNS health check failed"
            if error:
                message += f": {error}"
            await self.speak(message, priority=True)

    def __del__(self):
        """Cleanup voice engine."""
        if self._engine:
            try:
                self._engine.stop()
            except:
                pass
