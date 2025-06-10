import unittest
import os
import sqlite3
import time
import threading
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import memory_engine
sys.path.append(str(Path(__file__).parent.parent))
from memory_engine import (
    initialize_memory_db,
    save_memory_entry,
    query_memory_entries,
    DB_PATH
)

class TestMemoryEngineAdvanced(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        initialize_memory_db()

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_concurrent_access(self):
        """Test concurrent access to the database."""
        def worker(worker_id):
            for i in range(10):
                save_memory_entry(
                    f"Worker{worker_id}",
                    "concurrent_test",
                    f"Entry {i} from worker {worker_id}"
                )
                time.sleep(0.01)  # Small delay to increase chance of concurrent access

        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify all entries were saved
        entries = query_memory_entries("concurrent_test")
        self.assertEqual(len(entries), 50)  # 5 workers * 10 entries each

    def test_large_data_handling(self):
        """Test handling of large data entries."""
        # Create a large content string
        large_content = "x" * (1024 * 1024)  # 1MB of data
        
        # Save large entry
        save_memory_entry("TestAgent", "large_data", large_content)
        
        # Verify entry was saved correctly
        entries = query_memory_entries("large_data")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][4], large_content)

    def test_special_characters(self):
        """Test handling of special characters in content."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        save_memory_entry("TestAgent", "special_chars", special_chars)
        
        entries = query_memory_entries("special_chars")
        self.assertEqual(entries[0][4], special_chars)

    def test_unicode_support(self):
        """Test handling of Unicode characters."""
        unicode_text = "Hello, 世界! 🌍"
        save_memory_entry("TestAgent", "unicode", unicode_text)
        
        entries = query_memory_entries("unicode")
        self.assertEqual(entries[0][4], unicode_text)

    def test_performance(self):
        """Test performance with multiple entries."""
        start_time = time.time()
        
        # Save 1000 entries
        for i in range(1000):
            save_memory_entry(
                "PerformanceTest",
                "performance",
                f"Entry {i}"
            )
        
        save_time = time.time() - start_time
        
        # Query all entries
        start_time = time.time()
        entries = query_memory_entries("performance")
        query_time = time.time() - start_time
        
        # Verify performance
        self.assertEqual(len(entries), 1000)
        self.assertLess(save_time, 5.0)  # Should save 1000 entries in less than 5 seconds
        self.assertLess(query_time, 1.0)  # Should query 1000 entries in less than 1 second

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        with self.assertRaises(Exception):
            save_memory_entry(None, "test", "content")
        
        with self.assertRaises(Exception):
            save_memory_entry("agent", None, "content")
        
        with self.assertRaises(Exception):
            save_memory_entry("agent", "test", None)

    def test_database_corruption_recovery(self):
        """Test recovery from database corruption."""
        # Save some entries
        save_memory_entry("TestAgent", "test", "content1")
        save_memory_entry("TestAgent", "test", "content2")
        
        # Corrupt the database
        with open(DB_PATH, 'wb') as f:
            f.write(b'corrupted')
        
        # Reinitialize should create a new database
        initialize_memory_db()
        
        # Verify new database is empty
        entries = query_memory_entries()
        self.assertEqual(len(entries), 0)

    @pytest.mark.slow
    def test_long_running_operations(self):
        """Test long-running operations."""
        # Save entries over a longer period
        for i in range(100):
            save_memory_entry(
                "LongRunningTest",
                "long_running",
                f"Entry {i}"
            )
            time.sleep(0.1)
        
        # Verify all entries were saved
        entries = query_memory_entries("long_running")
        self.assertEqual(len(entries), 100)

if __name__ == '__main__':
    unittest.main() 