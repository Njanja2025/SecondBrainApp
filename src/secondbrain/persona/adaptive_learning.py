"""
Adaptive Learning Module implementation for SecondBrain
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class PersonaLearningModule:
    """Module for adaptive learning and persona development."""
    
    def __init__(self, memory_file: str = "long_term_persona.json"):
        """Initialize the learning module."""
        self.interactions: List[Dict[str, Any]] = []
        self.max_interactions = 1000
        self.current_persona = "neutral"
        self.memory_file = memory_file
        self.emotional_state = {
            "current": "neutral",
            "history": [],
            "intensity": 0.5
        }
        self.learning_patterns = defaultdict(int)
        self.interaction_stats = {
            "total": 0,
            "by_type": defaultdict(int),
            "by_emotion": defaultdict(int),
            "success_rate": 0.0
        }
        self.learning_rate = 0.1
        self.persona_weights = {
            "analytical": 0.0,
            "positive": 0.0,
            "empathetic": 0.0,
            "neutral": 1.0
        }
        
        # Load existing memory if available
        self._load_memory()
        
    def learn_from_interaction(
        self,
        interaction_type: str,
        content: str,
        emotion: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Learn from an interaction.
        
        Args:
            interaction_type: Type of interaction
            content: Interaction content
            emotion: Emotional context
            metadata: Optional additional metadata
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "content": content,
            "emotion": emotion,
            "metadata": metadata or {}
        }
        
        self.interactions.append(interaction)
        
        # Update statistics
        self._update_stats(interaction)
        
        # Update learning patterns
        self._update_learning_patterns(interaction)
        
        # Update emotional state
        self._update_emotional_state(emotion)
        
        # Update persona based on interaction
        self._update_persona(interaction)
        
        # Adjust learning rate based on interaction success
        self._adjust_learning_rate(interaction)
        
        # Trim interactions if exceeding max size
        if len(self.interactions) > self.max_interactions:
            self.interactions = self.interactions[-self.max_interactions:]
            
        # Log the interaction
        logger.info(
            f"Learned from {interaction_type} interaction | "
            f"Emotion: {emotion} | "
            f"Metadata: {metadata}"
        )
        
    def _update_stats(self, interaction: Dict[str, Any]):
        """Update interaction statistics."""
        self.interaction_stats["total"] += 1
        self.interaction_stats["by_type"][interaction["type"]] += 1
        self.interaction_stats["by_emotion"][interaction["emotion"]] += 1
        
        # Calculate success rate based on metadata
        if interaction["metadata"].get("success", False):
            self.interaction_stats["success_rate"] = (
                (self.interaction_stats["success_rate"] * (self.interaction_stats["total"] - 1) + 1) /
                self.interaction_stats["total"]
            )
            
    def _update_learning_patterns(self, interaction: Dict[str, Any]):
        """Update learning patterns based on interaction."""
        pattern_key = f"{interaction['type']}_{interaction['emotion']}"
        self.learning_patterns[pattern_key] += 1
        
    def _update_emotional_state(self, emotion: str):
        """Update emotional state with new emotion."""
        self.emotional_state["history"].append({
            "emotion": emotion,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 emotional states
        if len(self.emotional_state["history"]) > 100:
            self.emotional_state["history"] = self.emotional_state["history"][-100:]
            
        # Update current emotional state
        self.emotional_state["current"] = emotion
        
        # Calculate emotional intensity
        recent_emotions = [e["emotion"] for e in self.emotional_state["history"][-10:]]
        self.emotional_state["intensity"] = len(set(recent_emotions)) / 10.0
        
    def _update_persona(self, interaction: Dict[str, Any]):
        """
        Update the current persona based on interaction.
        
        Args:
            interaction: The interaction to learn from
        """
        emotion = interaction["emotion"]
        
        # Update persona weights based on emotion
        for persona in self.persona_weights:
            if persona == "analytical" and emotion == "analytical":
                self.persona_weights[persona] += self.learning_rate
            elif persona == "positive" and emotion in ["happy", "excited"]:
                self.persona_weights[persona] += self.learning_rate
            elif persona == "empathetic" and emotion in ["sad", "concerned"]:
                self.persona_weights[persona] += self.learning_rate
            elif persona == "neutral" and emotion == "neutral":
                self.persona_weights[persona] += self.learning_rate
            else:
                self.persona_weights[persona] -= self.learning_rate / 2
                
        # Normalize weights
        total = sum(self.persona_weights.values())
        if total > 0:
            self.persona_weights = {k: v/total for k, v in self.persona_weights.items()}
            
        # Set current persona based on highest weight
        self.current_persona = max(self.persona_weights.items(), key=lambda x: x[1])[0]
        
    def _adjust_learning_rate(self, interaction: Dict[str, Any]):
        """Adjust learning rate based on interaction success."""
        if interaction["metadata"].get("success", False):
            self.learning_rate = min(0.2, self.learning_rate * 1.1)
        else:
            self.learning_rate = max(0.01, self.learning_rate * 0.9)
            
    def get_current_persona(self) -> str:
        """
        Get the current persona state.
        
        Returns:
            Current persona identifier
        """
        return self.current_persona
        
    def get_recent_learnings(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent learning interactions.
        
        Args:
            count: Number of interactions to return
            
        Returns:
            List of recent interactions
        """
        return self.interactions[-count:]
        
    def analyze_emotional_trends(self) -> Dict[str, Any]:
        """
        Analyze emotional trends over time.
        
        Returns:
            Dictionary containing emotional analysis
        """
        if not self.emotional_state["history"]:
            return {"stability": 1.0, "dominant_emotion": "neutral"}
            
        recent_emotions = [e["emotion"] for e in self.emotional_state["history"][-50:]]
        emotion_counts = defaultdict(int)
        for emotion in recent_emotions:
            emotion_counts[emotion] += 1
            
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        stability = 1.0 - (len(set(recent_emotions)) / len(recent_emotions))
        
        return {
            "stability": stability,
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": dict(emotion_counts)
        }
        
    def summarize_behavior(self) -> Dict[str, Any]:
        """
        Summarize learning behavior and patterns.
        
        Returns:
            Dictionary containing behavior summary
        """
        return {
            "total_interactions": self.interaction_stats["total"],
            "success_rate": self.interaction_stats["success_rate"],
            "learning_rate": self.learning_rate,
            "persona_weights": self.persona_weights,
            "emotional_stability": self.analyze_emotional_trends()["stability"],
            "top_patterns": dict(sorted(
                self.learning_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5])
        }
        
    def save_memory(self, filepath: Optional[str] = None) -> None:
        """
        Save learning memory to file.
        
        Args:
            filepath: Optional custom filepath to save to
        """
        save_path = filepath or self.memory_file
        memory_data = {
            "interactions": self.interactions[-self.max_interactions:],
            "emotional_state": self.emotional_state,
            "learning_patterns": dict(self.learning_patterns),
            "interaction_stats": self.interaction_stats,
            "learning_rate": self.learning_rate,
            "persona_weights": self.persona_weights
        }
        
        try:
            with open(save_path, 'w') as f:
                json.dump(memory_data, f, indent=2)
            logger.info(f"Learning memory saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save learning memory: {str(e)}")
            
    def _load_memory(self) -> None:
        """Load learning memory from file if available."""
        if not os.path.exists(self.memory_file):
            return
            
        try:
            with open(self.memory_file, 'r') as f:
                memory_data = json.load(f)
                
            self.interactions = memory_data.get("interactions", [])
            self.emotional_state = memory_data.get("emotional_state", self.emotional_state)
            self.learning_patterns = defaultdict(int, memory_data.get("learning_patterns", {}))
            self.interaction_stats = memory_data.get("interaction_stats", self.interaction_stats)
            self.learning_rate = memory_data.get("learning_rate", self.learning_rate)
            self.persona_weights = memory_data.get("persona_weights", self.persona_weights)
            
            logger.info(f"Learning memory loaded from {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to load learning memory: {str(e)}")
            
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights about the learning process.
        
        Returns:
            Dictionary containing learning insights
        """
        recent_interactions = self.interactions[-100:]
        if not recent_interactions:
            return {"status": "no_data"}
            
        # Calculate success rate for recent interactions
        recent_success = sum(1 for i in recent_interactions if i["metadata"].get("success", False))
        recent_success_rate = recent_success / len(recent_interactions)
        
        # Analyze emotional patterns
        emotional_trends = self.analyze_emotional_trends()
        
        # Get most common interaction types
        type_counts = defaultdict(int)
        for interaction in recent_interactions:
            type_counts[interaction["type"]] += 1
            
        return {
            "recent_success_rate": recent_success_rate,
            "emotional_stability": emotional_trends["stability"],
            "dominant_emotion": emotional_trends["dominant_emotion"],
            "common_interactions": dict(sorted(
                type_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]),
            "learning_rate": self.learning_rate,
            "current_persona": self.current_persona
        } 