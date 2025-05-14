import json
import time
from pathlib import Path
import curses
import sys
from datetime import datetime


class HealthDashboard:
    def __init__(self):
        self.dashboard_file = Path("/tmp/secondbrain_health.json")
        self.update_interval = 1  # Update every second
        self.last_update = 0

    def load_metrics(self):
        try:
            if self.dashboard_file.exists():
                with open(self.dashboard_file, "r") as f:
                    return json.load(f)
            return None
        except Exception as e:
            return None

    def format_size(self, size_bytes):
        """Convert bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def draw_dashboard(self, stdscr):
        # Initialize curses
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)

        while True:
            stdscr.clear()
            metrics = self.load_metrics()

            if metrics:
                # Draw header
                stdscr.addstr(
                    0, 0, "SecondBrain System Health Dashboard", curses.A_BOLD
                )
                stdscr.addstr(1, 0, f"Last Updated: {metrics.get('timestamp', 'N/A')}")

                # Draw CPU section
                cpu = metrics.get("cpu", {})
                stdscr.addstr(3, 0, "CPU Status:", curses.A_BOLD)
                stdscr.addstr(4, 2, f"Usage: {cpu.get('percent', 0)}%")
                stdscr.addstr(5, 2, f"Cores: {cpu.get('count', 0)}")
                if cpu.get("frequency"):
                    stdscr.addstr(6, 2, f"Frequency: {cpu['frequency']/1000:.1f} GHz")

                # Draw Memory section
                memory = metrics.get("memory", {})
                stdscr.addstr(8, 0, "Memory Status:", curses.A_BOLD)
                stdscr.addstr(9, 2, f"Usage: {memory.get('percent', 0)}%")
                stdscr.addstr(
                    10, 2, f"Total: {self.format_size(memory.get('total', 0))}"
                )
                stdscr.addstr(
                    11, 2, f"Available: {self.format_size(memory.get('available', 0))}"
                )

                # Draw Disk section
                disk = metrics.get("disk", {})
                stdscr.addstr(13, 0, "Disk Status:", curses.A_BOLD)
                stdscr.addstr(14, 2, f"Usage: {disk.get('percent', 0)}%")
                stdscr.addstr(15, 2, f"Total: {self.format_size(disk.get('total', 0))}")
                stdscr.addstr(16, 2, f"Free: {self.format_size(disk.get('free', 0))}")

                # Draw Network section
                network = metrics.get("network", {})
                stdscr.addstr(18, 0, "Network Status:", curses.A_BOLD)
                stdscr.addstr(
                    19, 2, f"Sent: {self.format_size(network.get('bytes_sent', 0))}"
                )
                stdscr.addstr(
                    20, 2, f"Received: {self.format_size(network.get('bytes_recv', 0))}"
                )

                # Draw Battery section if available
                if "battery" in metrics:
                    battery = metrics["battery"]
                    stdscr.addstr(22, 0, "Battery Status:", curses.A_BOLD)
                    stdscr.addstr(23, 2, f"Level: {battery.get('percent', 0)}%")
                    stdscr.addstr(
                        24,
                        2,
                        f"Power: {'Plugged in' if battery.get('power_plugged') else 'Battery'}",
                    )

                # Draw System Info
                system = metrics.get("system", {})
                stdscr.addstr(26, 0, "System Info:", curses.A_BOLD)
                stdscr.addstr(
                    27,
                    2,
                    f"OS: {system.get('platform', 'N/A')} {system.get('platform_version', '')}",
                )
                stdscr.addstr(28, 2, f"Machine: {system.get('machine', 'N/A')}")
                stdscr.addstr(29, 2, f"Processor: {system.get('processor', 'N/A')}")
            else:
                stdscr.addstr(0, 0, "No system metrics available", curses.A_BOLD)

            # Add instructions
            stdscr.addstr(curses.LINES - 1, 0, "Press 'q' to quit", curses.A_DIM)

            stdscr.refresh()
            time.sleep(self.update_interval)


def main():
    try:
        dashboard = HealthDashboard()
        curses.wrapper(dashboard.draw_dashboard)
    except KeyboardInterrupt:
        print("\nDashboard closed by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
