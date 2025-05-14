"""
Integration monitoring system for SecondBrain application.
Tracks API calls, sync status, and integration health.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class APICall:
    """Represents an API call event."""

    timestamp: str
    service: str
    endpoint: str
    method: str
    status: int
    duration: float
    error: Optional[str] = None


@dataclass
class SyncStatus:
    """Represents a sync operation status."""

    timestamp: str
    service: str
    operation: str
    status: str
    items_processed: int
    duration: float
    error: Optional[str] = None


class IntegrationMonitor:
    """Monitors integration operations and API calls."""

    def __init__(self, log_dir: str = "logs/integrations"):
        """Initialize the integration monitor.

        Args:
            log_dir: Directory to store integration logs
        """
        self.log_dir = log_dir
        self.api_calls: List[APICall] = []
        self.sync_statuses: List[SyncStatus] = []
        self._setup_logging()
        self._load_history()

    def _setup_logging(self):
        """Set up logging for the integration monitor."""
        os.makedirs(self.log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_history(self):
        """Load historical data from log files."""
        try:
            # Load API calls
            api_log_path = os.path.join(self.log_dir, "api_calls.json")
            if os.path.exists(api_log_path):
                with open(api_log_path, "r") as f:
                    data = json.load(f)
                    self.api_calls = [APICall(**call) for call in data]

            # Load sync statuses
            sync_log_path = os.path.join(self.log_dir, "sync_status.json")
            if os.path.exists(sync_log_path):
                with open(sync_log_path, "r") as f:
                    data = json.load(f)
                    self.sync_statuses = [SyncStatus(**status) for status in data]

        except Exception as e:
            logger.error(f"Failed to load history: {str(e)}")

    def _save_history(self):
        """Save current data to log files."""
        try:
            # Save API calls
            api_log_path = os.path.join(self.log_dir, "api_calls.json")
            with open(api_log_path, "w") as f:
                json.dump([asdict(call) for call in self.api_calls], f, indent=2)

            # Save sync statuses
            sync_log_path = os.path.join(self.log_dir, "sync_status.json")
            with open(sync_log_path, "w") as f:
                json.dump(
                    [asdict(status) for status in self.sync_statuses], f, indent=2
                )

        except Exception as e:
            logger.error(f"Failed to save history: {str(e)}")

    def log_api_call(
        self,
        service: str,
        endpoint: str,
        method: str,
        status: int,
        duration: float,
        error: Optional[str] = None,
    ):
        """Log an API call.

        Args:
            service: Service name (e.g., 'google_drive')
            endpoint: API endpoint
            method: HTTP method
            status: Response status code
            duration: Call duration in seconds
            error: Error message if any
        """
        call = APICall(
            timestamp=datetime.now().isoformat(),
            service=service,
            endpoint=endpoint,
            method=method,
            status=status,
            duration=duration,
            error=error,
        )

        self.api_calls.append(call)
        self._save_history()

        # Log to console
        if error:
            logger.error(f"API call failed: {service} {endpoint} - {error}")
        else:
            logger.info(f"API call: {service} {endpoint} - {status}")

    def log_sync_status(
        self,
        service: str,
        operation: str,
        status: str,
        items_processed: int,
        duration: float,
        error: Optional[str] = None,
    ):
        """Log a sync operation status.

        Args:
            service: Service name (e.g., 'google_drive')
            operation: Operation type (e.g., 'upload', 'download')
            status: Operation status
            items_processed: Number of items processed
            duration: Operation duration in seconds
            error: Error message if any
        """
        sync = SyncStatus(
            timestamp=datetime.now().isoformat(),
            service=service,
            operation=operation,
            status=status,
            items_processed=items_processed,
            duration=duration,
            error=error,
        )

        self.sync_statuses.append(sync)
        self._save_history()

        # Log to console
        if error:
            logger.error(f"Sync failed: {service} {operation} - {error}")
        else:
            logger.info(
                f"Sync completed: {service} {operation} - {items_processed} items"
            )

    def get_api_stats(
        self, service: Optional[str] = None, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get API call statistics.

        Args:
            service: Filter by service name
            time_window: Filter by time window

        Returns:
            Dict containing API call statistics
        """
        calls = self.api_calls

        # Apply filters
        if service:
            calls = [call for call in calls if call.service == service]

        if time_window:
            cutoff = datetime.now() - time_window
            calls = [
                call
                for call in calls
                if datetime.fromisoformat(call.timestamp) > cutoff
            ]

        if not calls:
            return {
                "total_calls": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "error_count": 0,
            }

        # Calculate statistics
        total_calls = len(calls)
        success_calls = len([call for call in calls if not call.error])
        error_calls = len([call for call in calls if call.error])
        total_duration = sum(call.duration for call in calls)

        return {
            "total_calls": total_calls,
            "success_rate": (success_calls / total_calls) * 100,
            "avg_duration": total_duration / total_calls,
            "error_count": error_calls,
        }

    def get_sync_stats(
        self, service: Optional[str] = None, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get sync operation statistics.

        Args:
            service: Filter by service name
            time_window: Filter by time window

        Returns:
            Dict containing sync operation statistics
        """
        syncs = self.sync_statuses

        # Apply filters
        if service:
            syncs = [sync for sync in syncs if sync.service == service]

        if time_window:
            cutoff = datetime.now() - time_window
            syncs = [
                sync
                for sync in syncs
                if datetime.fromisoformat(sync.timestamp) > cutoff
            ]

        if not syncs:
            return {
                "total_syncs": 0,
                "success_rate": 0,
                "total_items": 0,
                "avg_duration": 0,
            }

        # Calculate statistics
        total_syncs = len(syncs)
        success_syncs = len([sync for sync in syncs if sync.status == "success"])
        total_items = sum(sync.items_processed for sync in syncs)
        total_duration = sum(sync.duration for sync in syncs)

        return {
            "total_syncs": total_syncs,
            "success_rate": (success_syncs / total_syncs) * 100,
            "total_items": total_items,
            "avg_duration": total_duration / total_syncs,
        }

    def cleanup_old_logs(self, max_age_days: int = 30):
        """Remove logs older than specified days.

        Args:
            max_age_days: Maximum age of logs in days
        """
        cutoff = datetime.now() - timedelta(days=max_age_days)

        # Clean up API calls
        self.api_calls = [
            call
            for call in self.api_calls
            if datetime.fromisoformat(call.timestamp) > cutoff
        ]

        # Clean up sync statuses
        self.sync_statuses = [
            sync
            for sync in self.sync_statuses
            if datetime.fromisoformat(sync.timestamp) > cutoff
        ]

        self._save_history()
        logger.info(f"Cleaned up logs older than {max_age_days} days")


# Example usage
if __name__ == "__main__":
    monitor = IntegrationMonitor()

    # Log some API calls
    monitor.log_api_call(
        service="google_drive",
        endpoint="/files",
        method="GET",
        status=200,
        duration=0.5,
    )

    monitor.log_api_call(
        service="google_drive",
        endpoint="/upload",
        method="POST",
        status=500,
        duration=1.2,
        error="Network timeout",
    )

    # Log some sync operations
    monitor.log_sync_status(
        service="google_drive",
        operation="upload",
        status="success",
        items_processed=10,
        duration=2.5,
    )

    # Get statistics
    api_stats = monitor.get_api_stats(service="google_drive")
    sync_stats = monitor.get_sync_stats(service="google_drive")

    print("API Stats:", api_stats)
    print("Sync Stats:", sync_stats)
