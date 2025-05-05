"""
Memory storage and retrieval system for the AI Agent.
"""
import time
from typing import Dict, List, Optional, Any
import sqlite3
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the memory store with optional custom database path."""
        if db_path is None:
            db_path = str(Path.home() / '.secondbrain' / 'memory.db')
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Create necessary database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    importance REAL DEFAULT 1.0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_type 
                ON memories(type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp 
                ON memories(timestamp)
            """)

    def store(self, 
              memory_type: str, 
              content: Any, 
              metadata: Optional[Dict] = None, 
              importance: float = 1.0) -> int:
        """
        Store a new memory.
        Returns the ID of the stored memory.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO memories (type, content, timestamp, metadata, importance)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        memory_type,
                        json.dumps(content),
                        time.time(),
                        json.dumps(metadata) if metadata else None,
                        importance
                    )
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            return -1

    def retrieve(self, 
                memory_type: Optional[str] = None, 
                limit: int = 10, 
                since: Optional[float] = None,
                min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieve memories matching the given criteria.
        Returns a list of memory dictionaries.
        """
        try:
            query = "SELECT * FROM memories WHERE importance >= ?"
            params = [min_importance]
            
            if memory_type:
                query += " AND type = ?"
                params.append(memory_type)
            
            if since:
                query += " AND timestamp >= ?"
                params.append(since)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                memories = []
                for row in cursor:
                    memory = dict(row)
                    memory['content'] = json.loads(memory['content'])
                    if memory['metadata']:
                        memory['metadata'] = json.loads(memory['metadata'])
                    memories.append(memory)
                
                return memories
                
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {str(e)}")
            return []

    def update_importance(self, memory_id: int, importance: float) -> bool:
        """Update the importance score of a memory."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE memories SET importance = ? WHERE id = ?",
                    (importance, memory_id)
                )
                return True
        except Exception as e:
            logger.error(f"Failed to update memory importance: {str(e)}")
            return False

    def clear(self, memory_type: Optional[str] = None) -> bool:
        """Clear memories of given type or all memories if type is None."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if memory_type:
                    conn.execute("DELETE FROM memories WHERE type = ?", (memory_type,))
                else:
                    conn.execute("DELETE FROM memories")
                return True
        except Exception as e:
            logger.error(f"Failed to clear memories: {str(e)}")
            return False 