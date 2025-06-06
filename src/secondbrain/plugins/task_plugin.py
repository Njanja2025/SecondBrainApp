# Expose the real TaskPlugin for test compatibility
from plugins.task_plugin import TaskPlugin, Task

__all__ = ["TaskPlugin", "Task"]
