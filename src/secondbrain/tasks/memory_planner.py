"""
Memory-aware task planner that uses context and history for better decisions.
"""
from typing import Optional, Dict, Any
import time
from ..memory import MemoryStore, ContextManager
from .planner import TaskPlanner

class MemoryTaskPlanner(TaskPlanner):
    def __init__(self, memory_store: MemoryStore, context_manager: ContextManager):
        super().__init__()
        self.memory_store = memory_store
        self.context_manager = context_manager
        
    def plan(self) -> Optional[Dict[str, Any]]:
        """
        Generate the next task using memory and context awareness.
        """
        current_time = time.time()
        
        # Rate limiting from parent class
        if current_time - self.last_plan_time < self.plan_interval:
            return None
            
        self.last_plan_time = current_time
        
        # Get current context
        context = self.context_manager.get_current_context()
        
        # Get recent memories
        recent_tasks = self.memory_store.retrieve(
            memory_type="task_execution",
            limit=5
        )
        
        # Basic task selection logic
        if not context:
            # No active context, do system check
            return {
                "description": "System Status Check",
                "action": "status_check",
                "priority": 1,
                "timestamp": current_time
            }
            
        # If we're in a conversation context
        if context.get("type") == "conversation":
            return {
                "description": "Process Conversation",
                "action": "process_conversation",
                "priority": 2,
                "timestamp": current_time,
                "data": context["data"]
            }
            
        # If we're in a task context
        if context.get("type") == "task":
            return {
                "description": f"Continue Task: {context['data'].get('task_name', 'Unknown')}",
                "action": "continue_task",
                "priority": 3,
                "timestamp": current_time,
                "data": context["data"]
            }
        
        # Default to parent class behavior
        return super().plan() 