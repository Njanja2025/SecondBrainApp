"""
Strategic Planning and Future Prediction Module.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class StrategicPlanner:
    """Advanced strategic planning and prediction system."""
    
    def __init__(self, tasks_path: Optional[str] = None):
        """
        Initialize the strategic planner.
        
        Args:
            tasks_path: Optional path to load existing tasks
        """
        self.future_tasks: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        self.recurring_tasks: List[Dict[str, Any]] = []
        self.task_categories: Dict[str, int] = {}
        self.tasks_path = tasks_path or "strategic_tasks.json"
        self._load_existing_tasks()
        
    def _load_existing_tasks(self) -> None:
        """Load existing tasks if available."""
        try:
            if Path(self.tasks_path).exists():
                with open(self.tasks_path, "r") as f:
                    data = json.load(f)
                    self.future_tasks = data.get("future", [])
                    self.completed_tasks = data.get("completed", [])
                    self.recurring_tasks = data.get("recurring", [])
                    self.task_categories = data.get("categories", {})
                logger.info(f"Loaded {len(self.future_tasks)} future tasks")
        except Exception as e:
            logger.error(f"Failed to load existing tasks: {str(e)}")
            
    def schedule_task(
        self,
        description: str,
        due_date: str,
        category: str = "general",
        priority: int = 2,
        recurring: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Schedule a new task with rich metadata.
        
        Args:
            description: Task description
            due_date: ISO format date string
            category: Task category
            priority: Priority level (1-5)
            recurring: Optional recurring schedule (daily, weekly, monthly)
            context: Additional context information
            
        Returns:
            The created task dictionary
        """
        # Validate priority
        priority = max(1, min(5, priority))
        
        # Create task
        task = {
            "description": description,
            "due": due_date,
            "created": datetime.now().isoformat(),
            "category": category,
            "priority": priority,
            "status": "pending",
            "context": context or {},
            "recurring": recurring
        }
        
        # Update category counts
        self.task_categories[category] = self.task_categories.get(category, 0) + 1
        
        # Handle recurring tasks
        if recurring:
            self.recurring_tasks.append(task)
        
        self.future_tasks.append(task)
        self._auto_save()
        
        return task
        
    def get_upcoming_tasks(
        self,
        days: int = 7,
        category: Optional[str] = None,
        min_priority: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get filtered upcoming tasks.
        
        Args:
            days: Number of days to look ahead
            category: Optional category filter
            min_priority: Optional minimum priority level
            
        Returns:
            List of matching tasks
        """
        today = datetime.now()
        end_date = today + timedelta(days=days)
        
        upcoming = [
            task for task in self.future_tasks
            if datetime.fromisoformat(task["due"]) <= end_date
            and task["status"] == "pending"
            and (category is None or task["category"] == category)
            and (min_priority is None or task["priority"] >= min_priority)
        ]
        
        # Sort by priority and due date
        return sorted(
            upcoming,
            key=lambda x: (
                x["priority"],
                datetime.fromisoformat(x["due"])
            ),
            reverse=True
        )
        
    def complete_task(self, task_id: str, outcome: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark a task as completed.
        
        Args:
            task_id: Task identifier
            outcome: Optional outcome information
        """
        for task in self.future_tasks:
            if task.get("id") == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                task["outcome"] = outcome
                
                # Move to completed tasks
                self.completed_tasks.append(task)
                self.future_tasks.remove(task)
                
                # Handle recurring tasks
                if task.get("recurring"):
                    self._schedule_next_occurrence(task)
                
                self._auto_save()
                break
                
    def _schedule_next_occurrence(self, task: Dict[str, Any]) -> None:
        """Schedule next occurrence of a recurring task."""
        due_date = datetime.fromisoformat(task["due"])
        
        if task["recurring"] == "daily":
            next_due = due_date + timedelta(days=1)
        elif task["recurring"] == "weekly":
            next_due = due_date + timedelta(weeks=1)
        elif task["recurring"] == "monthly":
            # Add one month (approximately)
            next_due = due_date + timedelta(days=30)
        else:
            return
            
        self.schedule_task(
            description=task["description"],
            due_date=next_due.isoformat(),
            category=task["category"],
            priority=task["priority"],
            recurring=task["recurring"],
            context=task["context"]
        )
        
    def analyze_task_patterns(self) -> Dict[str, Any]:
        """
        Analyze task patterns and completion trends.
        
        Returns:
            Dict containing analysis results
        """
        if not self.completed_tasks:
            return {"status": "No completed tasks available"}
            
        # Calculate completion rates
        total_tasks = len(self.completed_tasks) + len(self.future_tasks)
        completion_rate = len(self.completed_tasks) / total_tasks if total_tasks > 0 else 0
        
        # Analyze categories
        category_stats = {
            category: {
                "count": count,
                "percentage": (count / total_tasks) * 100
            }
            for category, count in self.task_categories.items()
        }
        
        # Calculate average completion time
        completion_times = []
        for task in self.completed_tasks:
            created = datetime.fromisoformat(task["created"])
            completed = datetime.fromisoformat(task["completed_at"])
            completion_times.append((completed - created).total_seconds())
            
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": len(self.completed_tasks),
            "completion_rate": completion_rate,
            "category_distribution": category_stats,
            "average_completion_time": avg_completion_time,
            "recurring_tasks": len(self.recurring_tasks)
        }
        
    def predict_future_load(self, days: int = 30) -> Dict[str, Any]:
        """
        Predict future task load and resource requirements.
        
        Args:
            days: Number of days to predict ahead
            
        Returns:
            Dict containing predictions
        """
        upcoming = self.get_upcoming_tasks(days=days)
        
        # Calculate daily load
        daily_load = {}
        for task in upcoming:
            due = datetime.fromisoformat(task["due"]).date()
            daily_load[str(due)] = daily_load.get(str(due), 0) + 1
            
        # Identify peak load periods
        peak_days = sorted(
            daily_load.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5 busiest days
        
        return {
            "total_upcoming": len(upcoming),
            "daily_load": daily_load,
            "peak_periods": peak_days,
            "category_distribution": self.task_categories,
            "estimated_completion_time": self._estimate_completion_time(upcoming)
        }
        
    def _estimate_completion_time(self, tasks: List[Dict[str, Any]]) -> float:
        """Estimate total completion time based on historical data."""
        if not self.completed_tasks:
            return len(tasks) * 3600  # Default 1 hour per task
            
        # Calculate average time per priority level
        priority_times = {}
        for task in self.completed_tasks:
            created = datetime.fromisoformat(task["created"])
            completed = datetime.fromisoformat(task["completed_at"])
            duration = (completed - created).total_seconds()
            priority = task["priority"]
            
            if priority not in priority_times:
                priority_times[priority] = []
            priority_times[priority].append(duration)
            
        # Calculate average times
        avg_times = {
            priority: sum(times) / len(times)
            for priority, times in priority_times.items()
        }
        
        # Estimate total time
        total_time = sum(
            avg_times.get(task["priority"], 3600)
            for task in tasks
        )
        
        return total_time
        
    def _auto_save(self) -> None:
        """Auto-save tasks to file."""
        try:
            data = {
                "future": self.future_tasks,
                "completed": self.completed_tasks,
                "recurring": self.recurring_tasks,
                "categories": self.task_categories
            }
            
            with open(self.tasks_path, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to auto-save tasks: {str(e)}")
            
    def get_task_suggestions(
        self,
        memory_core: Any,
        learning_module: Any
    ) -> List[Dict[str, Any]]:
        """
        Generate task suggestions based on system state.
        
        Args:
            memory_core: Reference to diagnostic memory core
            learning_module: Reference to learning module
            
        Returns:
            List of suggested tasks
        """
        suggestions = []
        
        # Check system health
        diagnostics = memory_core.run_diagnostic()
        if diagnostics["system_health"] == "degraded":
            suggestions.append({
                "type": "maintenance",
                "priority": 4,
                "description": "System health check required",
                "context": {"trigger": "degraded_health"}
            })
            
        # Check learning progress
        behavior = learning_module.summarize_behavior()
        if behavior.get("learning_progress", {}).get("vocabulary_size", 0) > 1000:
            suggestions.append({
                "type": "optimization",
                "priority": 3,
                "description": "Vocabulary optimization recommended",
                "context": {"trigger": "vocabulary_growth"}
            })
            
        # Check emotional stability
        emotions = learning_module.analyze_emotional_trends()
        if emotions.get("stability", 1.0) < 0.5:
            suggestions.append({
                "type": "calibration",
                "priority": 4,
                "description": "Emotional calibration needed",
                "context": {"trigger": "emotional_instability"}
            })
            
        return suggestions 