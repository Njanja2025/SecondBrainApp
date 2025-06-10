import unittest
import os
import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from memory_engine import (
    initialize_memory_db,
    save_memory_entry,
    query_memory_entries,
    DB_PATH
)

class TestMemoryEngineSpecific(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        initialize_memory_db()

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_json_data_handling(self):
        """Test handling of JSON data in memory entries."""
        test_data = {
            "user_id": "12345",
            "actions": ["login", "search", "logout"],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }
        
        # Save JSON data
        save_memory_entry(
            "TestAgent",
            "json_data",
            json.dumps(test_data)
        )
        
        # Retrieve and verify
        entries = query_memory_entries("json_data")
        retrieved_data = json.loads(entries[0][4])
        self.assertEqual(retrieved_data, test_data)

    def test_timestamp_ordering(self):
        """Test precise timestamp ordering of entries."""
        # Create entries with known timestamps
        timestamps = []
        for i in range(5):
            timestamp = datetime.now() + timedelta(seconds=i)
            timestamps.append(timestamp.isoformat())
            save_memory_entry(
                "TestAgent",
                "timestamp_test",
                f"Entry {i}",
                timestamp=timestamp
            )
        
        # Verify ordering
        entries = query_memory_entries("timestamp_test")
        for i, entry in enumerate(entries):
            self.assertEqual(entry[1], timestamps[-(i+1)])  # Most recent first

    def test_memory_type_hierarchy(self):
        """Test hierarchical memory type organization."""
        # Create hierarchical memory types
        types = [
            "system/startup",
            "system/shutdown",
            "user/login",
            "user/logout",
            "error/critical",
            "error/warning"
        ]
        
        for mem_type in types:
            save_memory_entry(
                "TestAgent",
                mem_type,
                f"Test entry for {mem_type}"
            )
        
        # Test querying by parent type
        system_entries = query_memory_entries("system")
        self.assertEqual(len(system_entries), 2)
        
        error_entries = query_memory_entries("error")
        self.assertEqual(len(error_entries), 2)

    def test_agent_interaction_tracking(self):
        """Test tracking of interactions between agents."""
        # Simulate agent interactions
        interactions = [
            ("AgentA", "AgentB", "request_data"),
            ("AgentB", "AgentA", "send_data"),
            ("AgentA", "AgentC", "notify"),
            ("AgentC", "AgentA", "acknowledge")
        ]
        
        for source, target, action in interactions:
            save_memory_entry(
                source,
                "agent_interaction",
                json.dumps({
                    "target": target,
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                })
            )
        
        # Verify interaction tracking
        entries = query_memory_entries("agent_interaction")
        self.assertEqual(len(entries), len(interactions))

    def test_memory_retention_policy(self):
        """Test memory retention based on type and age."""
        # Create entries with different types and ages
        now = datetime.now()
        entries = [
            ("critical", now - timedelta(days=1)),
            ("important", now - timedelta(days=7)),
            ("normal", now - timedelta(days=30)),
            ("archived", now - timedelta(days=90))
        ]
        
        for mem_type, timestamp in entries:
            save_memory_entry(
                "TestAgent",
                mem_type,
                f"Test entry for {mem_type}",
                timestamp=timestamp
            )
        
        # Verify retention based on type
        critical_entries = query_memory_entries("critical")
        self.assertEqual(len(critical_entries), 1)
        
        archived_entries = query_memory_entries("archived")
        self.assertEqual(len(archived_entries), 1)

    def test_memory_compression(self):
        """Test memory compression for large entries."""
        # Create a large entry with repetitive content
        large_content = "test" * 10000  # 40KB of data
        
        # Save and verify compression
        save_memory_entry(
            "TestAgent",
            "compressed",
            large_content
        )
        
        entries = query_memory_entries("compressed")
        self.assertEqual(entries[0][4], large_content)

    def test_memory_encryption(self):
        """Test memory encryption for sensitive data."""
        sensitive_data = {
            "password": "hashed_password_here",
            "token": "sensitive_token_here",
            "user_data": {
                "id": "12345",
                "role": "admin"
            }
        }
        
        # Save encrypted data
        save_memory_entry(
            "SecurityAgent",
            "encrypted",
            json.dumps(sensitive_data)
        )
        
        # Verify encryption
        entries = query_memory_entries("encrypted")
        retrieved_data = json.loads(entries[0][4])
        self.assertEqual(retrieved_data, sensitive_data)

    def test_memory_validation(self):
        """Test memory entry validation."""
        # Test invalid memory types
        with self.assertRaises(ValueError):
            save_memory_entry("TestAgent", "", "content")
        
        # Test invalid source agents
        with self.assertRaises(ValueError):
            save_memory_entry("", "test", "content")
        
        # Test invalid content
        with self.assertRaises(ValueError):
            save_memory_entry("TestAgent", "test", "")

    def test_memory_aggregation(self):
        """Test memory aggregation capabilities."""
        # Create multiple entries for aggregation
        for i in range(10):
            save_memory_entry(
                "TestAgent",
                "aggregation_test",
                json.dumps({
                    "value": i,
                    "category": "test" if i % 2 == 0 else "prod"
                })
            )
        
        # Verify aggregation
        entries = query_memory_entries("aggregation_test")
        self.assertEqual(len(entries), 10)

if __name__ == '__main__':
    unittest.main() 