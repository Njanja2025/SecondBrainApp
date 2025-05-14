"""
Monitoring dashboard for SecondBrain application.
Syncs deployment data to various services and provides analytics.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DashboardSync:
    """Syncs deployment data to various dashboard services."""

    def __init__(self, config_path: str = "config/dashboard_config.json"):
        """Initialize the dashboard sync.

        Args:
            config_path: Path to dashboard configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._setup_services()

    def _load_config(self) -> Dict[str, Any]:
        """Load dashboard configuration.

        Returns:
            Dashboard configuration dictionary
        """
        if not self.config_path.exists():
            return {
                "google_sheets": {
                    "enabled": False,
                    "credentials_file": "",
                    "spreadsheet_id": "",
                },
                "notion": {"enabled": False, "api_key": "", "database_id": ""},
                "webhook": {"enabled": False, "url": ""},
            }

        with open(self.config_path) as f:
            return json.load(f)

    def _setup_services(self) -> None:
        """Set up dashboard services."""
        if self.config["google_sheets"]["enabled"]:
            try:
                import gspread
                from oauth2client.service_account import ServiceAccountCredentials

                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive",
                ]

                credentials = ServiceAccountCredentials.from_json_keyfile_name(
                    self.config["google_sheets"]["credentials_file"], scope
                )

                self.gc = gspread.authorize(credentials)
                self.spreadsheet = self.gc.open_by_key(
                    self.config["google_sheets"]["spreadsheet_id"]
                )

            except Exception as e:
                logger.error(f"Failed to set up Google Sheets: {str(e)}")
                self.config["google_sheets"]["enabled"] = False

        if self.config["notion"]["enabled"]:
            try:
                from notion_client import Client

                self.notion = Client(auth=self.config["notion"]["api_key"])
            except Exception as e:
                logger.error(f"Failed to set up Notion: {str(e)}")
                self.config["notion"]["enabled"] = False

    def sync_event(self, event: Dict[str, Any]) -> None:
        """Sync a deployment event to configured services.

        Args:
            event: Deployment event to sync
        """
        if self.config["google_sheets"]["enabled"]:
            self._sync_to_sheets(event)

        if self.config["notion"]["enabled"]:
            self._sync_to_notion(event)

        if self.config["webhook"]["enabled"]:
            self._sync_to_webhook(event)

    def _sync_to_sheets(self, event: Dict[str, Any]) -> None:
        """Sync event to Google Sheets.

        Args:
            event: Deployment event to sync
        """
        try:
            worksheet = self.spreadsheet.sheet1
            row = [
                event["timestamp"],
                event["host"],
                event["platform"],
                event["status"],
                event["notes"],
                str(event["memory_usage"]),
                str(event["cpu_usage"]),
            ]
            worksheet.append_row(row)
        except Exception as e:
            logger.error(f"Failed to sync to Google Sheets: {str(e)}")

    def _sync_to_notion(self, event: Dict[str, Any]) -> None:
        """Sync event to Notion.

        Args:
            event: Deployment event to sync
        """
        try:
            self.notion.pages.create(
                parent={"database_id": self.config["notion"]["database_id"]},
                properties={
                    "Timestamp": {"date": {"start": event["timestamp"]}},
                    "Host": {"title": [{"text": {"content": event["host"]}}]},
                    "Platform": {
                        "rich_text": [{"text": {"content": event["platform"]}}]
                    },
                    "Status": {"select": {"name": event["status"]}},
                    "Notes": {"rich_text": [{"text": {"content": event["notes"]}}]},
                    "Memory Usage": {"number": event["memory_usage"]},
                    "CPU Usage": {"number": event["cpu_usage"]},
                },
            )
        except Exception as e:
            logger.error(f"Failed to sync to Notion: {str(e)}")

    def _sync_to_webhook(self, event: Dict[str, Any]) -> None:
        """Sync event to webhook.

        Args:
            event: Deployment event to sync
        """
        try:
            response = requests.post(
                self.config["webhook"]["url"],
                json=event,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to sync to webhook: {str(e)}")

    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get deployment analytics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary containing analytics data
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        analytics = {
            "total_launches": 0,
            "total_crashes": 0,
            "avg_memory_usage": 0,
            "avg_cpu_usage": 0,
            "platforms": {},
            "status_timeline": [],
        }

        try:
            with open("logs/deployment_status.log", "r") as f:
                for line in f:
                    event = json.loads(line.strip())
                    event_date = datetime.fromisoformat(event["timestamp"])

                    if event_date >= start_date:
                        # Count launches and crashes
                        if event["status"] == "launched":
                            analytics["total_launches"] += 1
                        elif event["status"] == "crashed":
                            analytics["total_crashes"] += 1

                        # Track platform distribution
                        platform = event["platform"]
                        analytics["platforms"][platform] = (
                            analytics["platforms"].get(platform, 0) + 1
                        )

                        # Track resource usage
                        analytics["avg_memory_usage"] += event["memory_usage"]
                        analytics["avg_cpu_usage"] += event["cpu_usage"]

                        # Add to timeline
                        analytics["status_timeline"].append(
                            {"timestamp": event["timestamp"], "status": event["status"]}
                        )

            # Calculate averages
            total_events = analytics["total_launches"] + analytics["total_crashes"]
            if total_events > 0:
                analytics["avg_memory_usage"] /= total_events
                analytics["avg_cpu_usage"] /= total_events

            # Sort timeline
            analytics["status_timeline"].sort(key=lambda x: x["timestamp"])

        except Exception as e:
            logger.error(f"Failed to generate analytics: {str(e)}")

        return analytics


# Create global instance
dashboard = DashboardSync()

# Example usage
if __name__ == "__main__":
    # Sync a test event
    test_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "host": "test-host",
        "platform": "test-platform",
        "status": "test",
        "notes": "Test event",
        "memory_usage": 50.0,
        "cpu_usage": 25.0,
    }
    dashboard.sync_event(test_event)

    # Get analytics
    analytics = dashboard.get_analytics()
    print(f"Analytics: {json.dumps(analytics, indent=2)}")
