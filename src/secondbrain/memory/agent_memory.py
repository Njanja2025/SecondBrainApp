from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

class MemoryEntry:
    def __init__(self, description: str, entry_type: str, metadata: Optional[Dict] = None):
        self.timestamp = datetime.now()
        self.description = description
        self.type = entry_type
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "description": self.description,
            "type": self.type,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        entry = cls(data["description"], data["type"], data.get("metadata", {}))
        entry.timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
        return entry

class AgentMemory:
    def __init__(self):
        self.log: List[MemoryEntry] = []
        self.task_history: Dict[str, List[MemoryEntry]] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        self.importance_threshold = 0.5
        self.max_memory_size = 10000
        self.compression_threshold = 5000

    def remember(self, task_description: str, task_type: str = "general", metadata: Optional[Dict] = None, importance: float = 1.0) -> str:
        """Record a task with timestamp and metadata."""
        try:
            # Check memory size and compress if needed
            if len(self.log) >= self.compression_threshold:
                self._compress_old_memories()

            # Create and store memory entry
            entry = MemoryEntry(task_description, task_type, metadata)
            self.log.append(entry)
            
            # Track task type frequencies
            if task_type not in self.task_history:
                self.task_history[task_type] = []
            self.task_history[task_type].append(entry)

            # Record importance as a metric
            self.record_metric(f"importance_{task_type}", importance)

            logger.debug(f"Recorded memory: {task_description} [{task_type}]")
            return entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        except Exception as e:
            logger.error(f"Failed to record memory: {str(e)}")
            raise

    def show_memory(self, task_type: Optional[str] = None, limit: Optional[int] = None, 
                   start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> str:
        """Show memory entries with advanced filtering."""
        try:
            # Get base entries
            if task_type:
                entries = self.task_history.get(task_type, [])
            else:
                entries = self.log

            # Apply date filtering
            if start_date or end_date:
                entries = [
                    entry for entry in entries
                    if (not start_date or entry.timestamp >= start_date) and
                    (not end_date or entry.timestamp <= end_date)
                ]

            # Sort by timestamp
            entries = sorted(entries, key=lambda x: x.timestamp, reverse=True)

            # Apply limit
            if limit:
                entries = entries[:limit]

            # Format output
            return "\n".join([
                f"{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - "
                f"[{entry.type}] {entry.description}"
                f"{' ' + json.dumps(entry.metadata) if entry.metadata else ''}"
                for entry in entries
            ])

        except Exception as e:
            logger.error(f"Failed to show memory: {str(e)}")
            return f"Error showing memory: {str(e)}"

    def analyze_performance(self, task_type: Optional[str] = None, 
                          time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze task performance metrics with advanced analytics."""
        try:
            # Get relevant tasks
            if task_type:
                relevant_tasks = self.task_history.get(task_type, [])
            else:
                relevant_tasks = self.log

            # Apply time window
            if time_window:
                cutoff_time = datetime.now() - time_window
                relevant_tasks = [
                    task for task in relevant_tasks
                    if task.timestamp >= cutoff_time
                ]

            # Calculate basic metrics
            total_tasks = len(relevant_tasks)
            task_distribution = {
                type_: len(tasks) 
                for type_, tasks in self.task_history.items()
            }

            # Calculate advanced metrics
            hourly_distribution = self._calculate_hourly_distribution(relevant_tasks)
            type_success_rates = self._calculate_type_success_rates()
            performance_trends = self._analyze_performance_trends()

            return {
                "total_tasks": total_tasks,
                "task_distribution": task_distribution,
                "hourly_distribution": hourly_distribution,
                "type_success_rates": type_success_rates,
                "performance_trends": performance_trends,
                "metrics": self.performance_metrics
            }

        except Exception as e:
            logger.error(f"Failed to analyze performance: {str(e)}")
            return {"error": str(e)}

    def record_metric(self, metric_name: str, value: float):
        """Record a performance metric with validation."""
        try:
            if not isinstance(value, (int, float)):
                raise ValueError(f"Metric value must be numeric, got {type(value)}")

            if metric_name not in self.performance_metrics:
                self.performance_metrics[metric_name] = []
            self.performance_metrics[metric_name].append(value)

            # Keep only recent metrics
            max_metrics = 1000
            if len(self.performance_metrics[metric_name]) > max_metrics:
                self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-max_metrics:]

        except Exception as e:
            logger.error(f"Failed to record metric: {str(e)}")
            raise

    def _compress_old_memories(self):
        """Compress old memories to maintain memory size."""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            old_entries = [
                entry for entry in self.log 
                if entry.timestamp < cutoff_date
            ]

            if not old_entries:
                return

            # Create summary
            summary = {
                "period_start": old_entries[0].timestamp,
                "period_end": old_entries[-1].timestamp,
                "total_entries": len(old_entries),
                "entry_types": {}
            }

            for entry in old_entries:
                if entry.type not in summary["entry_types"]:
                    summary["entry_types"][entry.type] = 0
                summary["entry_types"][entry.type] += 1

            # Remove old entries and add summary
            self.log = [
                entry for entry in self.log 
                if entry.timestamp >= cutoff_date
            ]
            
            # Add summary as a new memory entry
            self.remember(
                "Memory compression summary",
                "system",
                metadata=summary,
                importance=0.5
            )

        except Exception as e:
            logger.error(f"Failed to compress memories: {str(e)}")

    def _calculate_hourly_distribution(self, tasks: List[MemoryEntry]) -> Dict[int, int]:
        """Calculate task distribution by hour."""
        distribution = {i: 0 for i in range(24)}
        for task in tasks:
            hour = task.timestamp.hour
            distribution[hour] += 1
        return distribution

    def _calculate_type_success_rates(self) -> Dict[str, float]:
        """Calculate success rates for different task types."""
        success_rates = {}
        for task_type, tasks in self.task_history.items():
            if not tasks:
                continue
            successful = sum(
                1 for task in tasks 
                if task.metadata.get("status") == "success"
            )
            success_rates[task_type] = successful / len(tasks)
        return success_rates

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        trends = {}
        for metric_name, values in self.performance_metrics.items():
            if len(values) < 2:
                continue
            
            # Calculate basic trend indicators
            trend = {
                "current": values[-1],
                "previous": values[-2],
                "change": values[-1] - values[-2],
                "change_percent": ((values[-1] - values[-2]) / values[-2] * 100) 
                                if values[-2] != 0 else 0
            }
            trends[metric_name] = trend
            
        return trends

    def search_memories(self, query: str, task_type: Optional[str] = None) -> List[Dict]:
        """Search through memories with text matching."""
        try:
            matching_entries = []
            search_entries = self.task_history.get(task_type, []) if task_type else self.log
            
            for entry in search_entries:
                if (query.lower() in entry.description.lower() or
                    query.lower() in json.dumps(entry.metadata).lower()):
                    matching_entries.append(entry.to_dict())
            
            return matching_entries

        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        return {
            "total_memories": len(self.log),
            "type_counts": {
                type_: len(entries) 
                for type_, entries in self.task_history.items()
            },
            "oldest_memory": min(entry.timestamp for entry in self.log) if self.log else None,
            "newest_memory": max(entry.timestamp for entry in self.log) if self.log else None,
            "metrics_tracked": list(self.performance_metrics.keys())
        } 