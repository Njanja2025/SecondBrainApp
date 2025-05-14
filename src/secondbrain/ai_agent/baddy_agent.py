"""
Baddy Agent - Main entry point for running the Baddy character agent
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from secondbrain.characters.baddy import Baddy
from secondbrain.config.settings import load_config
from secondbrain.integrations.market import NjaxMarket
from secondbrain.integrations.journal import JournalSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/baddy_agent.log"),
    ],
)
logger = logging.getLogger(__name__)

class TaskProcessor:
    """Process and manage tasks for the Baddy agent."""
    
    def __init__(self, market: NjaxMarket, journal: JournalSystem):
        """Initialize task processor with integrations."""
        self.task_history: List[Dict[str, Any]] = []
        self.active_tasks: Dict[str, Any] = {}
        self.task_file = Path("agent_tasks.txt")
        self.history_file = Path("logs/task_history.json")
        self.market = market
        self.journal = journal
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.task_queue = []
        self.processing_lock = False
        self.error_count = 0
        self.max_errors = 5
        self.error_reset_time = 3600  # 1 hour
        self.last_error_time = None
        
    def load_task_history(self):
        """Load task history from file with enhanced error handling."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    self.task_history = json.load(f)
                logger.info(f"Loaded {len(self.task_history)} tasks from history")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding task history: {e}")
                # Create backup of corrupted file
                if self.history_file.exists():
                    backup_file = self.history_file.with_suffix('.json.bak')
                    self.history_file.rename(backup_file)
                    logger.info(f"Created backup of corrupted history file: {backup_file}")
            except Exception as e:
                logger.error(f"Error loading task history: {e}")
                # Create backup of corrupted file
                if self.history_file.exists():
                    backup_file = self.history_file.with_suffix('.json.bak')
                    self.history_file.rename(backup_file)
                    logger.info(f"Created backup of corrupted history file: {backup_file}")
    
    def save_task_history(self):
        """Save task history to file with atomic write."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            # Create temporary file first
            temp_file = self.history_file.with_suffix('.json.tmp')
            with open(temp_file, "w") as f:
                json.dump(self.task_history, f, indent=2)
            # Atomic rename
            temp_file.replace(self.history_file)
            logger.info(f"Saved {len(self.task_history)} tasks to history")
        except Exception as e:
            logger.error(f"Error saving task history: {e}")
            # Try to save to backup file
            try:
                backup_file = self.history_file.with_suffix('.json.bak')
                with open(backup_file, "w") as f:
                    json.dump(self.task_history, f, indent=2)
                logger.info(f"Saved task history to backup file: {backup_file}")
            except Exception as backup_e:
                logger.error(f"Error saving to backup file: {backup_e}")
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task with enhanced error handling and retry logic."""
        if self.processing_lock:
            logger.warning("Task processing is locked due to too many errors")
            return {"status": "error", "error": "Task processing is locked"}
            
        try:
            category = task["command"]["category"]
            command = task["command"]["command"]
            args = task["command"]["args"]
            
            result = {
                "task_id": len(self.task_history) + 1,
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "command": command,
                "args": args,
                "status": "processing",
                "retries": self.retry_count
            }
            
            # Process based on category
            if category == "market":
                if command == "open":
                    result.update(self.market.open_market())
                elif command == "search" and args:
                    result.update(self.market.search_items(args[0]))
                elif command == "browse":
                    result.update(self.market.browse_categories())
                elif command == "purchase" and args:
                    result.update(self.market.purchase_item(args[0]))
                elif command == "cart":
                    result.update(self.market._get_cart_summary())
                    
            elif category == "journal":
                if command == "start":
                    result.update(self.journal.start_journal())
                elif command == "read":
                    result.update(self.journal.read_journal())
                elif command == "search" and args:
                    result.update(self.journal.search_journal(args[0]))
                elif command == "edit" and args:
                    result.update(self.journal.edit_entry(args[0]))
                elif command == "tag" and len(args) == 2:
                    result.update(self.journal.edit_entry(args[1], tags=[args[0]]))
            
            elif category == "task":
                if command == "create" and args:
                    result.update(self._create_task(args[0]))
                elif command == "list":
                    result.update(self._list_tasks())
                elif command == "complete" and args:
                    result.update(self._complete_task(args[0]))
                elif command == "priority" and len(args) == 2:
                    result.update(self._set_task_priority(args[0], args[1]))
                elif command == "delete" and args:
                    result.update(self._delete_task(args[0]))
            
            # Add task to history
            self.task_history.append(result)
            self.save_task_history()
            
            # Reset retry count and error count on success
            self.retry_count = 0
            self.error_count = 0
            self.last_error_time = None
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            self.error_count += 1
            
            # Check if we should lock processing
            if self.error_count >= self.max_errors:
                self.processing_lock = True
                logger.error("Task processing locked due to too many errors")
                return {"status": "error", "error": "Task processing locked"}
            
            # Implement retry logic
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                logger.info(f"Retrying task (attempt {self.retry_count}/{self.max_retries})")
                time.sleep(self.retry_delay)
                return self.process_task(task)
            
            return {"status": "error", "error": str(e), "retries": self.retry_count}
    
    def _create_task(self, task_name: str) -> Dict[str, Any]:
        """Create a new task with enhanced validation."""
        try:
            # Validate task name
            if not task_name or len(task_name.strip()) == 0:
                return {"status": "error", "error": "Task name cannot be empty"}
            
            task = {
                "id": len(self.active_tasks) + 1,
                "name": task_name,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "priority": "medium",
                "tags": [],
                "notes": "",
                "due_date": None,
                "completed_at": None
            }
            self.active_tasks[task["id"]] = task
            return {
                "status": "success",
                "message": f"Created task: {task_name}",
                "task": task
            }
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {"status": "error", "error": str(e)}
    
    def _list_tasks(self) -> Dict[str, Any]:
        """List all active tasks with enhanced filtering."""
        try:
            tasks = list(self.active_tasks.values())
            
            # Sort tasks by priority and creation date
            tasks.sort(key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3),
                x["created_at"]
            ))
            
            return {
                "status": "success",
                "tasks": tasks,
                "count": len(tasks),
                "pending": len([t for t in tasks if t["status"] == "pending"]),
                "completed": len([t for t in tasks if t["status"] == "completed"])
            }
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {"status": "error", "error": str(e)}
    
    def _complete_task(self, task_id: str) -> Dict[str, Any]:
        """Mark a task as complete with enhanced status tracking."""
        try:
            task_id = int(task_id)
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                
                # Calculate completion time
                created = datetime.fromisoformat(task["created_at"])
                completed = datetime.fromisoformat(task["completed_at"])
                completion_time = (completed - created).total_seconds()
                
                return {
                    "status": "success",
                    "message": f"Completed task: {task['name']}",
                    "task": task,
                    "completion_time": completion_time
                }
            return {"status": "error", "error": "Task not found"}
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return {"status": "error", "error": str(e)}
    
    def _set_task_priority(self, task_id: str, priority: str) -> Dict[str, Any]:
        """Set task priority with enhanced validation."""
        try:
            task_id = int(task_id)
            priority = priority.lower()
            
            # Validate priority
            valid_priorities = ["high", "medium", "low"]
            if priority not in valid_priorities:
                return {"status": "error", "error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"}
            
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                old_priority = task["priority"]
                task["priority"] = priority
                
                return {
                    "status": "success",
                    "message": f"Updated priority for task: {task['name']}",
                    "task": task,
                    "old_priority": old_priority,
                    "new_priority": priority
                }
            return {"status": "error", "error": "Task not found"}
        except Exception as e:
            logger.error(f"Error setting task priority: {e}")
            return {"status": "error", "error": str(e)}
    
    def _delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task with enhanced cleanup."""
        try:
            task_id = int(task_id)
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                del self.active_tasks[task_id]
                
                # Update task IDs to maintain continuity
                new_tasks = {}
                for i, (_, t) in enumerate(sorted(self.active_tasks.items()), 1):
                    t["id"] = i
                    new_tasks[i] = t
                self.active_tasks = new_tasks
                
                return {
                    "status": "success",
                    "message": f"Deleted task: {task['name']}",
                    "deleted_task": task
                }
            return {"status": "error", "error": "Task not found"}
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_new_tasks(self) -> List[Dict[str, Any]]:
        """Check for new tasks in the task file with enhanced error handling."""
        if not self.task_file.exists():
            return []
            
        try:
            with open(self.task_file, "r") as f:
                tasks = []
                for line in f:
                    if line.strip():
                        try:
                            task = json.loads(line)
                            tasks.append(task)
                        except json.JSONDecodeError as e:
                            logger.error(f"Error decoding task: {e}")
                            continue
            
            # Clear the file after reading
            with open(self.task_file, "w") as f:
                f.write("")
                
            logger.info(f"Found {len(tasks)} new tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Error reading tasks file: {e}")
            return []

def main():
    """Main entry point for the Baddy agent."""
    try:
        # Load configuration
        config = load_config()
        
        # Initialize components
        baddy = Baddy(config)
        market = NjaxMarket(config)
        journal = JournalSystem(config)
        task_processor = TaskProcessor(market, journal)
        task_processor.load_task_history()
        
        logger.info("Baddy agent initialized successfully")
        print("\n[Baddy] Online and watching for tasks...\n")
        
        while True:
            # Check for new tasks
            new_tasks = task_processor.check_new_tasks()
            for task in new_tasks:
                # Process the task
                result = task_processor.process_task(task)
                logger.info(f"Processing task: {json.dumps(result, indent=2)}")
                
                # Generate a challenge based on the task
                challenge = baddy.interact("generate_challenge", difficulty="medium")
                logger.info(f"Generated challenge for task '{task['command']['full_match']}': {json.dumps(challenge, indent=2)}")
            
            # Get active challenges
            challenges = baddy.interact("get_challenges")
            if challenges['active']:
                logger.info(f"Active challenges: {json.dumps(challenges['active'], indent=2)}")
            
            # Get stats
            stats = baddy.interact("get_stats")
            logger.info(f"Challenge stats: {json.dumps(stats, indent=2)}")
            
            # Sleep for a bit before checking again
            time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n[Baddy] Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running Baddy agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 