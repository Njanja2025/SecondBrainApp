"""
Integration logger for tracking integration events.
Manages logging of integration attempts, successes, and failures.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class IntegrationEvent:
    """Represents an integration event."""

    event_id: str
    timestamp: datetime
    service: str
    event_type: str
    status: str
    details: Dict[str, Any]
    duration: Optional[float] = None
    error: Optional[str] = None


class IntegrationLogger:
    """Manages integration event logging."""

    def __init__(self, log_dir: str = "logs/integration"):
        """Initialize the integration logger.

        Args:
            log_dir: Directory to store integration logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for the integration logger."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def log_event(
        self,
        service: str,
        event_type: str,
        status: str,
        details: Dict[str, Any],
        duration: Optional[float] = None,
        error: Optional[str] = None,
    ) -> str:
        """Log an integration event.

        Args:
            service: Service name
            event_type: Type of event
            status: Event status
            details: Event details
            duration: Optional event duration
            error: Optional error message

        Returns:
            Event ID
        """
        try:
            # Generate event ID
            event_id = (
                f"{service}_{event_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Create event
            event = IntegrationEvent(
                event_id=event_id,
                timestamp=datetime.now(),
                service=service,
                event_type=event_type,
                status=status,
                details=details,
                duration=duration,
                error=error,
            )

            # Save event
            self._save_event(event)

            # Log event
            log_message = (
                f"Integration event: {event_id} - {service} - {event_type} - {status}"
            )
            if error:
                logger.error(f"{log_message} - Error: {error}")
            else:
                logger.info(log_message)

            return event_id

        except Exception as e:
            logger.error(f"Failed to log integration event: {str(e)}")
            raise

    def _save_event(self, event: IntegrationEvent):
        """Save an integration event to file.

        Args:
            event: Event to save
        """
        try:
            # Create service directory
            service_dir = self.log_dir / event.service
            service_dir.mkdir(parents=True, exist_ok=True)

            # Create event file
            event_file = service_dir / f"{event.event_id}.json"

            with open(event_file, "w") as f:
                json.dump(asdict(event), f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save integration event: {str(e)}")
            raise

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an integration event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event details if found
        """
        try:
            # Parse event ID
            service, event_type, timestamp = event_id.split("_")

            # Find event file
            event_file = self.log_dir / service / f"{event_id}.json"

            if event_file.exists():
                with open(event_file, "r") as f:
                    return json.load(f)

            return None

        except Exception as e:
            logger.error(f"Failed to get integration event {event_id}: {str(e)}")
            return None

    def get_events(
        self,
        service: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get integration events matching criteria.

        Args:
            service: Optional service filter
            event_type: Optional event type filter
            status: Optional status filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of matching events
        """
        try:
            events = []

            # Get service directories
            service_dirs = (
                [self.log_dir / service] if service else self.log_dir.iterdir()
            )

            for service_dir in service_dirs:
                if not service_dir.is_dir():
                    continue

                # Get event files
                for event_file in service_dir.glob("*.json"):
                    try:
                        with open(event_file, "r") as f:
                            event = json.load(f)

                        # Apply filters
                        if event_type and event["event_type"] != event_type:
                            continue
                        if status and event["status"] != status:
                            continue

                        event_time = datetime.fromisoformat(event["timestamp"])
                        if start_time and event_time < start_time:
                            continue
                        if end_time and event_time > end_time:
                            continue

                        events.append(event)

                    except Exception as e:
                        logger.error(
                            f"Failed to process event file {event_file}: {str(e)}"
                        )

            return events

        except Exception as e:
            logger.error(f"Failed to get integration events: {str(e)}")
            return []

    def get_service_stats(
        self,
        service: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get statistics for a service.

        Args:
            service: Service name
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Service statistics
        """
        try:
            events = self.get_events(
                service=service, start_time=start_time, end_time=end_time
            )

            stats = {
                "total_events": len(events),
                "success_count": 0,
                "failure_count": 0,
                "avg_duration": 0.0,
                "event_types": {},
            }

            total_duration = 0.0
            duration_count = 0

            for event in events:
                # Count successes and failures
                if event["status"] == "success":
                    stats["success_count"] += 1
                elif event["status"] == "failure":
                    stats["failure_count"] += 1

                # Calculate average duration
                if event.get("duration"):
                    total_duration += event["duration"]
                    duration_count += 1

                # Count event types
                event_type = event["event_type"]
                stats["event_types"][event_type] = (
                    stats["event_types"].get(event_type, 0) + 1
                )

            if duration_count > 0:
                stats["avg_duration"] = total_duration / duration_count

            return stats

        except Exception as e:
            logger.error(f"Failed to get service stats for {service}: {str(e)}")
            return {}

    def cleanup_old_events(self, days: int = 30):
        """Clean up old integration events.

        Args:
            days: Number of days to keep events
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)

            for service_dir in self.log_dir.iterdir():
                if not service_dir.is_dir():
                    continue

                for event_file in service_dir.glob("*.json"):
                    try:
                        with open(event_file, "r") as f:
                            event = json.load(f)

                        event_time = datetime.fromisoformat(event["timestamp"])
                        if event_time < cutoff_time:
                            event_file.unlink()
                            logger.info(f"Deleted old event file: {event_file}")

                    except Exception as e:
                        logger.error(
                            f"Failed to process event file {event_file}: {str(e)}"
                        )

        except Exception as e:
            logger.error(f"Failed to cleanup old events: {str(e)}")


# Example usage
if __name__ == "__main__":
    logger = IntegrationLogger()

    # Log an event
    event_id = logger.log_event(
        service="example_service",
        event_type="data_sync",
        status="success",
        details={"records_processed": 100},
        duration=1.5,
    )

    # Get event
    event = logger.get_event(event_id)
    print("Event:", event)

    # Get service stats
    stats = logger.get_service_stats("example_service")
    print("Service stats:", stats)

    # Cleanup old events
    logger.cleanup_old_events(days=30)
