"""
Self-training module for adaptive memory and emotion systems.
"""
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path
import json

from .memory_engine import MemoryEngine

logger = logging.getLogger(__name__)

class SelfTrainingManager:
    """Manages the self-training and adaptation of the memory and emotion systems."""
    
    def __init__(
        self,
        memory_engine: MemoryEngine,
        model_dir: str = "models/emotion",
        backup_suffix: str = "_backup"
    ):
        self.memory_engine = memory_engine
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.backup_suffix = backup_suffix
        
        # Training configuration
        self.config = {
            "min_samples_for_training": 100,
            "training_window_days": 30,
            "max_training_iterations": 5,
            "learning_rate": 0.01
        }
        
    async def check_and_retrain(self) -> bool:
        """
        Check if retraining is needed and perform it if necessary.
        
        Returns:
            bool: True if retraining was performed, False otherwise
        """
        try:
            if not self.memory_engine.needs_retraining():
                logger.info("No retraining needed at this time")
                return False
                
            logger.info("Starting retraining process...")
            
            # Backup current model state
            self._backup_current_model()
            
            # Get training data
            training_data = self._prepare_training_data()
            if not training_data:
                logger.warning("Insufficient training data available")
                return False
                
            # Perform retraining
            success = await self._retrain_model(training_data)
            
            if success:
                logger.info("Retraining completed successfully")
                self._update_training_timestamp()
                return True
            else:
                logger.error("Retraining failed, restoring backup")
                self._restore_from_backup()
                return False
                
        except Exception as e:
            logger.error(f"Error during retraining: {e}")
            self._restore_from_backup()
            return False
            
    def _backup_current_model(self):
        """Create a backup of the current model state."""
        try:
            model_files = list(self.model_dir.glob("*.json"))
            for file in model_files:
                backup_path = file.parent / f"{file.stem}{self.backup_suffix}{file.suffix}"
                with open(file, "r") as src, open(backup_path, "w") as dst:
                    json.dump(json.load(src), dst, indent=4)
                    
            logger.info("Created model backup")
            
        except Exception as e:
            logger.error(f"Failed to create model backup: {e}")
            raise
            
    def _restore_from_backup(self):
        """Restore model from backup after failed training."""
        try:
            backup_files = list(self.model_dir.glob(f"*{self.backup_suffix}.json"))
            for backup in backup_files:
                original = backup.parent / f"{backup.stem.replace(self.backup_suffix, '')}.json"
                with open(backup, "r") as src, open(original, "w") as dst:
                    json.dump(json.load(src), dst, indent=4)
                    
            logger.info("Restored model from backup")
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            raise
            
    def _prepare_training_data(self) -> Optional[dict]:
        """
        Prepare training data from memory and feedback history.
        
        Returns:
            dict: Training data or None if insufficient data
        """
        try:
            analytics = self.memory_engine.get_mood_analytics()
            
            if analytics["total_samples"] < self.config["min_samples_for_training"]:
                return None
                
            # Prepare training data structure
            training_data = {
                "mood_transitions": analytics["transition_probabilities"],
                "mood_distribution": analytics["mood_distribution"],
                "feedback_history": self.memory_engine.memory["user_feedback"],
                "config": self.config
            }
            
            return training_data
            
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return None
            
    async def _retrain_model(self, training_data: dict) -> bool:
        """
        Perform the actual model retraining.
        
        Args:
            training_data: Prepared training data
            
        Returns:
            bool: True if training succeeded, False otherwise
        """
        try:
            # Save new training data
            training_file = self.model_dir / "training_data.json"
            with open(training_file, "w") as f:
                json.dump(training_data, f, indent=4)
                
            # Update model parameters based on feedback
            model_params = self._update_model_parameters(training_data)
            
            # Save updated model
            model_file = self.model_dir / "emotion_model.json"
            with open(model_file, "w") as f:
                json.dump(model_params, f, indent=4)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to retrain model: {e}")
            return False
            
    def _update_model_parameters(self, training_data: dict) -> dict:
        """
        Update model parameters based on training data.
        
        Args:
            training_data: The prepared training data
            
        Returns:
            dict: Updated model parameters
        """
        # Extract feedback patterns
        correct_patterns = [
            f for f in training_data["feedback_history"]
            if f["feedback"]
        ]
        
        # Calculate new parameters
        params = {
            "mood_weights": {},
            "transition_bias": training_data["mood_transitions"],
            "distribution_prior": training_data["mood_distribution"],
            "learning_rate": self.config["learning_rate"],
            "last_updated": str(datetime.now())
        }
        
        # Update mood weights based on correct predictions
        total_correct = len(correct_patterns)
        if total_correct > 0:
            for pattern in correct_patterns:
                mood = pattern["mood"]
                if mood not in params["mood_weights"]:
                    params["mood_weights"][mood] = 0
                params["mood_weights"][mood] += 1
                
            # Normalize weights
            for mood in params["mood_weights"]:
                params["mood_weights"][mood] /= total_correct
                
        return params
        
    def _update_training_timestamp(self):
        """Update the last training timestamp in memory."""
        self.memory_engine.memory["learning_metrics"]["last_retrain"] = str(datetime.now())
        self.memory_engine.save_memory() 