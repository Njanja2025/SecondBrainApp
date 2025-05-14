"""
Task Plugin - Task Management System
Provides task management capabilities through voice commands.
"""

import logging
import json
import os
from typing import Any, Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Task data structure."""

    id: str
    title: str
    description: str
    due_date: Optional[datetime]
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]


class TaskPlugin:
    """Task management plugin with voice command support."""

    is_plugin = True

    def __init__(self):
        """Initialize the task plugin."""
        self.name = "Task Plugin"
        self.version = "1.0.0"
        self.description = "Provides task management capabilities"
        self.tasks: Dict[str, Task] = {}
        self.data_file = Path("data/tasks.json")
        self._setup()

    def _setup(self) -> None:
        """Set up the plugin."""
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._load_tasks()
            logger.info(f"Initializing {self.name} v{self.version}")
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {e}")
            raise

    def _load_tasks(self) -> None:
        """Load tasks from storage."""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    for task_data in data:
                        task = Task(
                            id=task_data["id"],
                            title=task_data["title"],
                            description=task_data["description"],
                            due_date=(
                                datetime.fromisoformat(task_data["due_date"])
                                if task_data["due_date"]
                                else None
                            ),
                            priority=task_data["priority"],
                            status=task_data["status"],
                            created_at=datetime.fromisoformat(task_data["created_at"]),
                            updated_at=datetime.fromisoformat(task_data["updated_at"]),
                            tags=task_data["tags"],
                        )
                        self.tasks[task.id] = task
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            raise

    def _save_tasks(self) -> None:
        """Save tasks to storage."""
        try:
            data = []
            for task in self.tasks.values():
                task_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "tags": task.tags,
                }
                data.append(task_data)

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
            raise

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
        }

    def register_commands(self, voice_assistant: Any) -> None:
        """Register voice commands for this plugin."""
        try:
            voice_assistant.register_command("add_task", self._handle_add_task_command)
            voice_assistant.register_command(
                "list_tasks", self._handle_list_tasks_command
            )
            voice_assistant.register_command(
                "complete_task", self._handle_complete_task_command
            )
            voice_assistant.register_command(
                "delete_task", self._handle_delete_task_command
            )
            voice_assistant.register_command(
                "update_task", self._handle_update_task_command
            )
            voice_assistant.register_command(
                "search_tasks", self._handle_search_tasks_command
            )
        except Exception as e:
            logger.error(f"Failed to register commands: {e}")

    def _handle_add_task_command(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
        tags: List[str] = None,
    ) -> str:
        """Handle the 'add_task' voice command."""
        try:
            task = Task(
                id=str(len(self.tasks) + 1),
                title=title,
                description=description,
                due_date=datetime.fromisoformat(due_date) if due_date else None,
                priority=priority,
                status="pending",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=tags or [],
            )
            self.tasks[task.id] = task
            self._save_tasks()
            return f"Added task: {title}"
        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            return "Sorry, I couldn't add the task"

    def _handle_list_tasks_command(
        self, status: str = "pending", priority: Optional[str] = None
    ) -> str:
        """Handle the 'list_tasks' voice command."""
        try:
            tasks = [task for task in self.tasks.values() if task.status == status]
            if priority:
                tasks = [task for task in tasks if task.priority == priority]

            if not tasks:
                return f"No {status} tasks found"

            response = f"Here are your {status} tasks:\n"
            for task in tasks:
                response += f"- {task.title} (Priority: {task.priority})"
                if task.due_date:
                    response += f", Due: {task.due_date.strftime('%Y-%m-%d')}"
                response += "\n"
            return response
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return "Sorry, I couldn't list the tasks"

    def _handle_complete_task_command(self, task_id: str) -> str:
        """Handle the 'complete_task' voice command."""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = "completed"
                task.updated_at = datetime.now()
                self._save_tasks()
                return f"Completed task: {task.title}"
            return f"Task {task_id} not found"
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            return "Sorry, I couldn't complete the task"

    def _handle_delete_task_command(self, task_id: str) -> str:
        """Handle the 'delete_task' voice command."""
        try:
            if task_id in self.tasks:
                task = self.tasks.pop(task_id)
                self._save_tasks()
                return f"Deleted task: {task.title}"
            return f"Task {task_id} not found"
        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            return "Sorry, I couldn't delete the task"

    def _handle_update_task_command(self, task_id: str, **kwargs) -> str:
        """Handle the 'update_task' voice command."""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = datetime.now()
                self._save_tasks()
                return f"Updated task: {task.title}"
            return f"Task {task_id} not found"
        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return "Sorry, I couldn't update the task"

    def _handle_search_tasks_command(self, query: str) -> str:
        """Handle the 'search_tasks' voice command."""
        try:
            query = query.lower()
            matching_tasks = []

            for task in self.tasks.values():
                if (
                    query in task.title.lower()
                    or query in task.description.lower()
                    or query in [tag.lower() for tag in task.tags]
                ):
                    matching_tasks.append(task)

            if not matching_tasks:
                return f"No tasks found matching '{query}'"

            response = f"Found {len(matching_tasks)} matching tasks:\n"
            for task in matching_tasks:
                response += f"- {task.title} (Status: {task.status}, Priority: {task.priority})\n"
            return response
        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            return "Sorry, I couldn't search the tasks"
