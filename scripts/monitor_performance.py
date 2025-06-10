#!/usr/bin/env python3

import os
import time
import psutil
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from brain.memory_engine import (
    initialize_memory_db,
    save_memory_entry,
    query_memory_entries,
    DB_PATH
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance.log'),
        logging.StreamHandler()
    ]
)

class PerformanceMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.db_size = 0
        self.last_check = time.time()
        self.interval = 60  # Check every 60 seconds

    def get_memory_usage(self):
        """Get current memory usage."""
        return self.process.memory_info().rss / 1024 / 1024  # Convert to MB

    def get_cpu_usage(self):
        """Get current CPU usage."""
        return self.process.cpu_percent()

    def get_db_size(self):
        """Get current database size."""
        if os.path.exists(DB_PATH):
            return os.path.getsize(DB_PATH) / 1024 / 1024  # Convert to MB
        return 0

    def get_db_stats(self):
        """Get database statistics."""
        if not os.path.exists(DB_PATH):
            return {}
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get table statistics
        cursor.execute("SELECT COUNT(*) FROM MemoryEntries")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT memory_type, COUNT(*) 
            FROM MemoryEntries 
            GROUP BY memory_type
        """)
        entries_by_type = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT source_agent, COUNT(*) 
            FROM MemoryEntries 
            GROUP BY source_agent
        """)
        entries_by_agent = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'entries_by_type': entries_by_type,
            'entries_by_agent': entries_by_agent
        }

    def log_performance_metrics(self):
        """Log current performance metrics."""
        current_time = time.time()
        if current_time - self.last_check < self.interval:
            return
        
        memory_usage = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        db_size = self.get_db_size()
        db_stats = self.get_db_stats()
        
        logging.info(f"Memory Usage: {memory_usage:.2f} MB")
        logging.info(f"CPU Usage: {cpu_usage:.2f}%")
        logging.info(f"Database Size: {db_size:.2f} MB")
        logging.info(f"Total Entries: {db_stats['total_entries']}")
        logging.info(f"Entries by Type: {db_stats['entries_by_type']}")
        logging.info(f"Entries by Agent: {db_stats['entries_by_agent']}")
        
        self.last_check = current_time

    def monitor_performance(self, duration=3600):  # Monitor for 1 hour by default
        """Monitor performance for specified duration."""
        end_time = time.time() + duration
        
        logging.info("Starting performance monitoring...")
        
        while time.time() < end_time:
            self.log_performance_metrics()
            time.sleep(self.interval)
        
        logging.info("Performance monitoring completed.")

def main():
    monitor = PerformanceMonitor()
    try:
        monitor.monitor_performance()
    except KeyboardInterrupt:
        logging.info("Performance monitoring stopped by user.")
    except Exception as e:
        logging.error(f"Error during performance monitoring: {e}")

if __name__ == "__main__":
    main() 