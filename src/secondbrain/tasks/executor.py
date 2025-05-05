"""
Task execution module for the AI Agent system.
"""
from typing import Dict, Any
import logging
from ..voice_processor import VoiceProcessor

logger = logging.getLogger(__name__)

class TaskExecutor:
    def __init__(self):
        self.voice_processor = VoiceProcessor()
        self._register_actions()

    def _register_actions(self):
        """Register all available task actions."""
        self.actions = {
            "status_check": self._status_check,
            "say_hello": self._say_hello,
        }

    async def execute(self, task: Dict[str, Any]) -> bool:
        """
        Execute a given task.
        Returns True if execution was successful, False otherwise.
        """
        try:
            action = task.get("action")
            if action not in self.actions:
                logger.warning(f"Unknown task action: {action}")
                return False

            await self.actions[action](task)
            return True

        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return False

    async def _status_check(self, task: Dict[str, Any]):
        """Perform a system status check."""
        await self.voice_processor.speak("All systems operational.")

    async def _say_hello(self, task: Dict[str, Any]):
        """Simple greeting task."""
        await self.voice_processor.speak("Hello, I am your AI Agent.") 