"""
Baddy character implementation for SecondBrainApp
"""
import os
import sys
import logging
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from .base import Character

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Baddy(Character):
    """Baddy character implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Baddy character."""
        super().__init__(config)
        self.name = "Baddy"
        self.description = "A mischievous character that creates challenges and obstacles"
        self.personality = {
            "traits": [
                "mischievous",
                "unpredictable",
                "playful",
                "challenging",
                "creative"
            ],
            "mood": "playful",
            "energy": 100
        }
        self.challenges = []
        self.rewards = []
        self.state_file = Path("data/baddy_state.json")
        self.load_state()
        
    def load_state(self):
        """Load Baddy's state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.personality = state.get("personality", self.personality)
                    self.challenges = state.get("challenges", [])
                    self.rewards = state.get("rewards", [])
                    logger.info("Loaded Baddy state from file")
        except Exception as e:
            logger.error(f"Failed to load Baddy state: {e}")
            
    def save_state(self):
        """Save Baddy's state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "personality": self.personality,
                "challenges": self.challenges,
                "rewards": self.rewards,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
            logger.info("Saved Baddy state to file")
        except Exception as e:
            logger.error(f"Failed to save Baddy state: {e}")
            
    def update_mood(self, event: str):
        """Update Baddy's mood based on events."""
        try:
            mood_changes = {
                "challenge_created": 10,
                "challenge_completed": -5,
                "reward_given": -8,
                "user_frustrated": 15,
                "user_happy": -10
            }
            
            if event in mood_changes:
                self.personality["mood"] = "playful" if mood_changes[event] > 0 else "calm"
                self.personality["energy"] = max(0, min(100, 
                    self.personality["energy"] + mood_changes[event]))
                self.save_state()
                logger.info(f"Updated Baddy mood: {self.personality['mood']}")
                
        except Exception as e:
            logger.error(f"Failed to update Baddy mood: {e}")
            
    def generate_challenge(self, difficulty: str = "medium") -> Dict[str, Any]:
        """Generate a new challenge."""
        try:
            challenge_types = {
                "easy": [
                    "Find a hidden message",
                    "Solve a simple puzzle",
                    "Complete a quick task"
                ],
                "medium": [
                    "Navigate a maze",
                    "Decode a message",
                    "Find a pattern"
                ],
                "hard": [
                    "Solve a complex puzzle",
                    "Break a code",
                    "Find a hidden path"
                ]
            }
            
            challenge = {
                "id": len(self.challenges) + 1,
                "type": random.choice(challenge_types[difficulty]),
                "difficulty": difficulty,
                "created_at": datetime.now().isoformat(),
                "completed": False,
                "reward": self.generate_reward(difficulty)
            }
            
            self.challenges.append(challenge)
            self.update_mood("challenge_created")
            self.save_state()
            
            logger.info(f"Generated new challenge: {challenge['type']}")
            return challenge
            
        except Exception as e:
            logger.error(f"Failed to generate challenge: {e}")
            return {}
            
    def generate_reward(self, difficulty: str) -> Dict[str, Any]:
        """Generate a reward for completing a challenge."""
        try:
            rewards = {
                "easy": [
                    "Small hint",
                    "Bonus point",
                    "Extra time"
                ],
                "medium": [
                    "Medium hint",
                    "Bonus points",
                    "Special ability"
                ],
                "hard": [
                    "Big hint",
                    "Many bonus points",
                    "Special power"
                ]
            }
            
            reward = {
                "type": random.choice(rewards[difficulty]),
                "value": random.randint(1, 10) * (1 if difficulty == "easy" else 2 if difficulty == "medium" else 3)
            }
            
            self.rewards.append(reward)
            logger.info(f"Generated new reward: {reward['type']}")
            return reward
            
        except Exception as e:
            logger.error(f"Failed to generate reward: {e}")
            return {}
            
    def complete_challenge(self, challenge_id: int) -> bool:
        """Mark a challenge as completed."""
        try:
            for challenge in self.challenges:
                if challenge["id"] == challenge_id and not challenge["completed"]:
                    challenge["completed"] = True
                    challenge["completed_at"] = datetime.now().isoformat()
                    self.update_mood("challenge_completed")
                    self.save_state()
                    logger.info(f"Completed challenge {challenge_id}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to complete challenge: {e}")
            return False
            
    def get_active_challenges(self) -> List[Dict[str, Any]]:
        """Get list of active challenges."""
        return [c for c in self.challenges if not c["completed"]]
        
    def get_completed_challenges(self) -> List[Dict[str, Any]]:
        """Get list of completed challenges."""
        return [c for c in self.challenges if c["completed"]]
        
    def get_challenge_stats(self) -> Dict[str, Any]:
        """Get challenge statistics."""
        try:
            total = len(self.challenges)
            completed = len(self.get_completed_challenges())
            active = len(self.get_active_challenges())
            
            return {
                "total": total,
                "completed": completed,
                "active": active,
                "completion_rate": (completed / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get challenge stats: {e}")
            return {}
            
    def reset(self):
        """Reset Baddy's state."""
        try:
            self.personality = {
                "traits": [
                    "mischievous",
                    "unpredictable",
                    "playful",
                    "challenging",
                    "creative"
                ],
                "mood": "playful",
                "energy": 100
            }
            self.challenges = []
            self.rewards = []
            self.save_state()
            logger.info("Reset Baddy state")
            
        except Exception as e:
            logger.error(f"Failed to reset Baddy state: {e}")
            
    def interact(self, action: str, **kwargs) -> Dict[str, Any]:
        """Interact with Baddy."""
        try:
            if action == "generate_challenge":
                difficulty = kwargs.get("difficulty", "medium")
                return self.generate_challenge(difficulty)
                
            elif action == "complete_challenge":
                challenge_id = kwargs.get("challenge_id")
                if challenge_id is not None:
                    success = self.complete_challenge(challenge_id)
                    return {"success": success}
                    
            elif action == "get_challenges":
                return {
                    "active": self.get_active_challenges(),
                    "completed": self.get_completed_challenges()
                }
                
            elif action == "get_stats":
                return self.get_challenge_stats()
                
            elif action == "reset":
                self.reset()
                return {"success": True}
                
            return {"error": "Invalid action"}
            
        except Exception as e:
            logger.error(f"Failed to interact with Baddy: {e}")
            return {"error": str(e)} 