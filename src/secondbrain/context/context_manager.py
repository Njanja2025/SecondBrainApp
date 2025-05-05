"""
Advanced context management system for SecondBrain.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path
import asyncio
from ..memory import MemoryStore

logger = logging.getLogger(__name__)

class Context:
    def __init__(self, context_type: str, data: Dict[str, Any]):
        self.type = context_type
        self.data = data
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.metadata = {}
        
    def update(self, data: Dict[str, Any]):
        """Update context data."""
        self.data.update(data)
        self.updated_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "type": self.type,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Context':
        """Create context from dictionary."""
        context = cls(data["type"], data["data"])
        context.created_at = datetime.fromisoformat(data["created_at"])
        context.updated_at = datetime.fromisoformat(data["updated_at"])
        context.metadata = data.get("metadata", {})
        return context

class ContextManager:
    def __init__(self):
        self.memory = MemoryStore()
        self.context_stack: List[Context] = []
        self.context_history: List[Context] = []
        self.max_history = 100
        self.context_file = Path("config/context.json")
        
    async def initialize(self):
        """Initialize context manager."""
        try:
            await self._load_context()
            logger.info("Context manager initialized")
        except Exception as e:
            logger.error(f"Error initializing context manager: {e}")
            
    async def _load_context(self):
        """Load saved context."""
        try:
            if self.context_file.exists():
                with open(self.context_file, "r") as f:
                    data = json.load(f)
                    
                self.context_stack = [
                    Context.from_dict(ctx) for ctx in data.get("stack", [])
                ]
                self.context_history = [
                    Context.from_dict(ctx) for ctx in data.get("history", [])
                ]
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            
    async def _save_context(self):
        """Save current context."""
        try:
            self.context_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.context_file, "w") as f:
                json.dump({
                    "stack": [ctx.to_dict() for ctx in self.context_stack],
                    "history": [ctx.to_dict() for ctx in self.context_history]
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            
    def push_context(self, context_type: str, data: Dict[str, Any]):
        """Push new context onto stack."""
        try:
            context = Context(context_type, data)
            self.context_stack.append(context)
            
            # Add to history
            self.context_history.append(context)
            if len(self.context_history) > self.max_history:
                self.context_history.pop(0)
                
            # Save context
            asyncio.create_task(self._save_context())
            
            logger.info(f"Pushed new context: {context_type}")
            
        except Exception as e:
            logger.error(f"Error pushing context: {e}")
            
    def pop_context(self) -> Optional[Context]:
        """Pop context from stack."""
        try:
            if self.context_stack:
                context = self.context_stack.pop()
                asyncio.create_task(self._save_context())
                return context
            return None
        except Exception as e:
            logger.error(f"Error popping context: {e}")
            return None
            
    def get_current_context(self) -> Optional[Context]:
        """Get current context."""
        return self.context_stack[-1] if self.context_stack else None
        
    def update_current_context(self, data: Dict[str, Any]):
        """Update current context."""
        try:
            if current := self.get_current_context():
                current.update(data)
                asyncio.create_task(self._save_context())
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            
    def clear_context(self):
        """Clear all context."""
        try:
            self.context_stack.clear()
            asyncio.create_task(self._save_context())
            logger.info("Cleared context stack")
        except Exception as e:
            logger.error(f"Error clearing context: {e}")
            
    def get_context_history(self, context_type: Optional[str] = None) -> List[Context]:
        """Get context history, optionally filtered by type."""
        try:
            if context_type:
                return [ctx for ctx in self.context_history if ctx.type == context_type]
            return self.context_history.copy()
        except Exception as e:
            logger.error(f"Error getting context history: {e}")
            return []
            
    async def analyze_context(self) -> Dict[str, Any]:
        """Analyze current context state."""
        try:
            current = self.get_current_context()
            
            analysis = {
                "current_type": current.type if current else None,
                "stack_depth": len(self.context_stack),
                "history_length": len(self.context_history),
                "context_types": self._get_context_type_distribution(),
                "recent_changes": self._get_recent_changes()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return {}
            
    def _get_context_type_distribution(self) -> Dict[str, int]:
        """Get distribution of context types."""
        try:
            distribution = {}
            for context in self.context_history:
                distribution[context.type] = distribution.get(context.type, 0) + 1
            return distribution
        except Exception as e:
            logger.error(f"Error getting context distribution: {e}")
            return {}
            
    def _get_recent_changes(self) -> List[Dict[str, Any]]:
        """Get recent context changes."""
        try:
            changes = []
            for context in reversed(self.context_history[-10:]):
                changes.append({
                    "type": context.type,
                    "timestamp": context.created_at.isoformat(),
                    "data_keys": list(context.data.keys())
                })
            return changes
        except Exception as e:
            logger.error(f"Error getting recent changes: {e}")
            return []
            
    async def merge_contexts(self, context_types: List[str]) -> Optional[Context]:
        """Merge multiple contexts of specified types."""
        try:
            contexts = [
                ctx for ctx in self.context_stack
                if ctx.type in context_types
            ]
            
            if not contexts:
                return None
                
            merged_data = {}
            for ctx in contexts:
                merged_data.update(ctx.data)
                
            merged = Context("merged", merged_data)
            merged.metadata["source_types"] = context_types
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging contexts: {e}")
            return None
            
    async def save_context_snapshot(self, description: str):
        """Save a snapshot of current context state."""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "stack": [ctx.to_dict() for ctx in self.context_stack],
                "current": self.get_current_context().to_dict() if self.get_current_context() else None
            }
            
            # Save to memory store
            await self.memory.store_context_snapshot(snapshot)
            logger.info(f"Saved context snapshot: {description}")
            
        except Exception as e:
            logger.error(f"Error saving context snapshot: {e}")
            
    async def load_context_snapshot(self, timestamp: str) -> bool:
        """Load context from a saved snapshot."""
        try:
            snapshot = await self.memory.get_context_snapshot(timestamp)
            if not snapshot:
                return False
                
            # Restore context stack
            self.context_stack = [
                Context.from_dict(ctx) for ctx in snapshot["stack"]
            ]
            
            await self._save_context()
            logger.info(f"Loaded context snapshot from {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading context snapshot: {e}")
            return False 