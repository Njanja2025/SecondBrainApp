"""
Diagnostic Memory Core implementation for SecondBrain
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DiagnosticMemoryCore:
    """Memory core for diagnostic and event tracking."""

    def __init__(self):
        """Initialize the memory core."""
        self.events: List[Dict[str, Any]] = []
        self.max_events = 1000

    def record_event(
        self,
        message: str,
        level: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record an event in the memory core.

        Args:
            message: Event message
            level: Event level (info, warning, error)
            metadata: Optional additional metadata
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "level": level,
            "metadata": metadata or {},
        }

        self.events.append(event)

        # Trim events if exceeding max size
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Log the event
        log_method = getattr(logger, level, logger.info)
        log_method(f"{message} | Metadata: {metadata}")

    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent events.

        Args:
            count: Number of events to return

        Returns:
            List of recent events
        """
        return self.events[-count:]

    def get_events_by_level(self, level: str) -> List[Dict[str, Any]]:
        """
        Get events filtered by level.

        Args:
            level: Event level to filter by

        Returns:
            List of filtered events
        """
        return [event for event in self.events if event["level"] == level]

    def clear_events(self):
        """Clear all events from memory."""
        self.events = []
        logger.info("Memory core events cleared")
