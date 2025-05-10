"""
Memory Engine for managing personal context and mood history with feedback-based learning.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union
from collections import defaultdict

from .cloud_backup import CloudBackupManager

logger = logging.getLogger(__name__)

class MemoryEngine:
    """Manages personal context and mood history with feedback-based learning."""
    
    def __init__(
        self,
        memory_file: str = "samantha_memory.json",
        enable_cloud_backup: bool = True
    ):
        self.memory_file = Path("data/memory") / memory_file
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory structure
        self.memory = self.load_memory()
        
        # Training metrics
        self.accuracy_threshold = 0.5  # Trigger retraining if accuracy falls below this
        self.min_feedback_samples = 5  # Minimum samples before considering retraining
        self.feedback_window = timedelta(days=7)  # Consider feedback from last 7 days
        
        # Mood transition probabilities for better prediction
        self.mood_transitions = defaultdict(lambda: defaultdict(float))
        self._initialize_mood_transitions()
        
        # Initialize cloud backup if enabled
        self.cloud_backup = CloudBackupManager() if enable_cloud_backup else None
        
    def load_memory(self) -> Dict:
        """Load memory from file or create new if not exists."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file) as f:
                    return json.load(f)
            return {
                "mood_history": [],
                "user_feedback": [],
                "context_markers": {},
                "learning_metrics": {
                    "total_predictions": 0,
                    "correct_predictions": 0,
                    "last_retrain": None
                }
            }
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return self._create_default_memory()
            
    def save_memory(self):
        """Save current memory state to file and trigger cloud backup."""
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.memory, f, indent=4)
                
            # Trigger async cloud backup if enabled
            if self.cloud_backup:
                import asyncio
                asyncio.create_task(self.backup_to_cloud())
                
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            
    def remember_mood(self, tone: str, context: Optional[Dict] = None):
        """
        Record a new mood with optional context.
        
        Args:
            tone: The emotional tone/mood to remember
            context: Optional contextual information about the mood
        """
        timestamp = str(datetime.now())
        
        # Update mood history
        mood_entry = {
            "timestamp": timestamp,
            "mood": tone,
            "context": context or {}
        }
        self.memory["mood_history"].append(mood_entry)
        
        # Update transition probabilities
        if self.memory["mood_history"]:
            last_mood = self.get_last_mood(skip=1)  # Get previous mood
            if last_mood:
                self._update_mood_transition(last_mood, tone)
        
        self.save_memory()
        
    def remember_feedback(self, mood: str, feedback: bool, context: Optional[Dict] = None):
        """
        Record user feedback about mood prediction.
        
        Args:
            mood: The mood being evaluated
            feedback: True if prediction was correct, False otherwise
            context: Optional context about the feedback
        """
        timestamp = str(datetime.now())
        
        # Update feedback history
        feedback_entry = {
            "timestamp": timestamp,
            "mood": mood,
            "feedback": feedback,
            "context": context or {}
        }
        self.memory["user_feedback"].append(feedback_entry)
        
        # Update learning metrics
        self.memory["learning_metrics"]["total_predictions"] += 1
        if feedback:
            self.memory["learning_metrics"]["correct_predictions"] += 1
            
        self.save_memory()
        
    def get_last_mood(self, skip: int = 0) -> Optional[str]:
        """
        Get the last recorded mood, optionally skipping recent entries.
        
        Args:
            skip: Number of recent entries to skip
            
        Returns:
            The mood string or None if no history
        """
        history = self.memory["mood_history"]
        if len(history) > skip:
            return history[-(skip + 1)]["mood"]
        return None
        
    def predict_next_mood(self, current_mood: str) -> str:
        """
        Predict the next likely mood based on transition probabilities.
        
        Args:
            current_mood: The current mood state
            
        Returns:
            Most likely next mood
        """
        transitions = self.mood_transitions[current_mood]
        if not transitions:
            return current_mood
            
        # Get mood with highest transition probability
        return max(transitions.items(), key=lambda x: x[1])[0]
        
    def needs_retraining(self) -> bool:
        """Check if the system needs retraining based on recent feedback."""
        metrics = self.memory["learning_metrics"]
        recent_feedback = self._get_recent_feedback()
        
        if len(recent_feedback) < self.min_feedback_samples:
            return False
            
        # Calculate accuracy over recent feedback
        correct = sum(1 for f in recent_feedback if f["feedback"])
        accuracy = correct / len(recent_feedback)
        
        return accuracy < self.accuracy_threshold
        
    def get_mood_analytics(self) -> Dict:
        """Get analytics about mood patterns and prediction accuracy."""
        try:
            metrics = self.memory["learning_metrics"]
            recent_feedback = self._get_recent_feedback()
            
            # Calculate overall accuracy
            total_preds = metrics["total_predictions"]
            correct_preds = metrics["correct_predictions"]
            overall_accuracy = correct_preds / total_preds if total_preds > 0 else 0
            
            # Calculate recent accuracy
            recent_correct = sum(1 for f in recent_feedback if f["feedback"])
            recent_accuracy = (
                recent_correct / len(recent_feedback)
                if recent_feedback else 0
            )
            
            # Get mood distribution
            mood_counts = defaultdict(int)
            for entry in self.memory["mood_history"]:
                mood_counts[entry["mood"]] += 1
                
            return {
                "overall_accuracy": overall_accuracy,
                "recent_accuracy": recent_accuracy,
                "mood_distribution": dict(mood_counts),
                "transition_probabilities": dict(self.mood_transitions),
                "total_samples": total_preds,
                "needs_retraining": self.needs_retraining(),
                "timestamp": str(datetime.now())
            }
            
        except Exception as e:
            logger.error(f"Failed to get mood analytics: {e}")
            return {}
            
    def _create_default_memory(self) -> Dict:
        """Create default memory structure."""
        return {
            "mood_history": [],
            "user_feedback": [],
            "context_markers": {},
            "learning_metrics": {
                "total_predictions": 0,
                "correct_predictions": 0,
                "last_retrain": None
            }
        }
        
    def _initialize_mood_transitions(self):
        """Initialize mood transition probabilities from history."""
        if not self.memory["mood_history"]:
            return
            
        # Count transitions
        for i in range(len(self.memory["mood_history"]) - 1):
            current = self.memory["mood_history"][i]["mood"]
            next_mood = self.memory["mood_history"][i + 1]["mood"]
            self._update_mood_transition(current, next_mood)
            
    def _update_mood_transition(self, from_mood: str, to_mood: str):
        """Update transition probabilities between moods."""
        # Count total transitions from this mood
        total = sum(self.mood_transitions[from_mood].values())
        
        # Update probability for this transition
        self.mood_transitions[from_mood][to_mood] += 1
        
        # Normalize probabilities
        for mood in self.mood_transitions[from_mood]:
            self.mood_transitions[from_mood][mood] /= (total + 1)
            
    def _get_recent_feedback(self) -> List[Dict]:
        """Get feedback entries from within the feedback window."""
        cutoff = datetime.now() - self.feedback_window
        return [
            f for f in self.memory["user_feedback"]
            if datetime.fromisoformat(f["timestamp"]) > cutoff
        ] 

    async def backup_to_cloud(self) -> Dict[str, bool]:
        """
        Backup memory to configured cloud services.
        
        Returns:
            Dict with status for each service
        """
        if not self.cloud_backup:
            logger.warning("Cloud backup not enabled")
            return {}
            
        results = {}
        
        # Ensure latest memory is saved
        self.save_memory()
        
        # Try Dropbox backup
        if self.cloud_backup.config["dropbox"]["enabled"]:
            config = self.cloud_backup.config["dropbox"]
            results["dropbox"] = await self.cloud_backup.backup_to_dropbox(
                str(self.memory_file),
                config["access_token"],
                config.get("backup_path")
            )
            
        # Try Google Drive backup
        if self.cloud_backup.config["google_drive"]["enabled"]:
            config = self.cloud_backup.config["google_drive"]
            results["google_drive"] = await self.cloud_backup.backup_to_drive(
                str(self.memory_file),
                config["credentials_json"],
                config.get("folder_id")
            )
            
        # Try AWS S3 backup
        if self.cloud_backup.config["aws"]["enabled"]:
            config = self.cloud_backup.config["aws"]
            results["aws_s3"] = await self.cloud_backup.backup_to_s3(
                str(self.memory_file),
                config["bucket"],
                config["access_key"],
                config["secret_key"],
                config.get("region", "us-east-1"),
                config.get("object_prefix", "samantha/memory")
            )
            
        return results
        
    def configure_cloud_backup(self, service: str, config: Dict):
        """
        Configure cloud backup for a specific service.
        
        Args:
            service: Service name (dropbox, google_drive, aws)
            config: Service configuration
        """
        if not self.cloud_backup:
            logger.warning("Cloud backup not enabled")
            return
            
        config["enabled"] = True
        self.cloud_backup.update_config(service, config)
        
    async def update_dns(
        self,
        api_user: str,
        api_key: str,
        domain: str,
        subdomain: str,
        ip_address: str
    ) -> bool:
        """
        Update Namecheap DNS for the memory service.
        
        Args:
            api_user: Namecheap API username
            api_key: Namecheap API key
            domain: Domain name
            subdomain: Subdomain to update
            ip_address: IP address to point to
            
        Returns:
            bool: True if update successful
        """
        if not self.cloud_backup:
            logger.warning("Cloud backup not enabled")
            return False
            
        return await self.cloud_backup.update_namecheap_dns(
            api_user,
            api_key,
            domain,
            subdomain,
            ip_address
        ) 