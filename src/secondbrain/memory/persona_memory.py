"""
Memory persistence engine for SecondBrain personas.
Enables personas to maintain context and learn from past interactions.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class MemoryEngine:
    def __init__(self, storage_dir: Optional[str] = None):
        self.entries: List[Dict[str, Any]] = []
        self.persona: Optional[str] = None
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), "storage"
        )
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)

    def link_to(self, persona_name: str):
        """Link this memory engine to a specific persona."""
        self.persona = persona_name
        self._load_memories()
        logger.info(f"Memory engine linked to persona: {persona_name}")

    def store(self, context: Dict[str, Any], feedback: Dict[str, Any]):
        """Store a new memory entry with context and feedback."""
        if not self.persona:
            raise ValueError(
                "Memory engine must be linked to a persona before storing memories"
            )

        entry = {
            "timestamp": datetime.now().isoformat(),
            "persona": self.persona,
            "context": context,
            "feedback": feedback,
        }
        self.entries.append(entry)
        self._save_memories()
        logger.debug(f"Stored new memory for {self.persona}")

    def retrieve(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memory entries, optionally filtered by criteria.

        Args:
            filters: Optional dictionary of filter criteria
                    e.g. {"context.user_emotion": "frustrated"}
        """
        if not filters:
            return self.entries

        filtered_entries = []
        for entry in self.entries:
            matches = True
            for key, value in filters.items():
                # Handle nested dictionary keys (e.g. "context.user_emotion")
                parts = key.split(".")
                current = entry
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        matches = False
                        break
                if current != value:
                    matches = False
                    break
            if matches:
                filtered_entries.append(entry)

        return filtered_entries

    def get_emotional_history(
        self, timespan_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze emotional interaction history.

        Args:
            timespan_hours: Optional number of hours to look back

        Returns:
            Dictionary containing emotional interaction statistics
        """
        emotions = {}
        total_interactions = 0

        for entry in self.entries:
            if "context" in entry and "user_emotion" in entry["context"]:
                emotion = entry["context"]["user_emotion"]
                emotions[emotion] = emotions.get(emotion, 0) + 1
                total_interactions += 1

        return {
            "emotion_distribution": {
                emotion: count / total_interactions
                for emotion, count in emotions.items()
            },
            "total_interactions": total_interactions,
            "most_common_emotion": (
                max(emotions.items(), key=lambda x: x[1])[0] if emotions else None
            ),
        }

    def get_interaction_patterns(self) -> Dict[str, Any]:
        """Analyze interaction patterns to identify trends."""
        patterns = {
            "time_of_day": {},
            "emotional_transitions": [],
            "successful_responses": [],
        }

        prev_emotion = None
        for entry in self.entries:
            # Track time of day patterns
            timestamp = datetime.fromisoformat(entry["timestamp"])
            hour = timestamp.hour
            time_category = (
                "morning"
                if 5 <= hour < 12
                else (
                    "afternoon"
                    if 12 <= hour < 17
                    else "evening" if 17 <= hour < 22 else "night"
                )
            )
            patterns["time_of_day"][time_category] = (
                patterns["time_of_day"].get(time_category, 0) + 1
            )

            # Track emotional transitions
            if "context" in entry and "user_emotion" in entry["context"]:
                current_emotion = entry["context"]["user_emotion"]
                if prev_emotion and prev_emotion != current_emotion:
                    patterns["emotional_transitions"].append(
                        {
                            "from": prev_emotion,
                            "to": current_emotion,
                            "timestamp": entry["timestamp"],
                        }
                    )
                prev_emotion = current_emotion

            # Track successful responses
            if "feedback" in entry and "effectiveness" in entry["feedback"]:
                if entry["feedback"]["effectiveness"] >= 0.8:
                    patterns["successful_responses"].append(
                        {"context": entry["context"], "feedback": entry["feedback"]}
                    )

        return patterns

    def _save_memories(self):
        """Save memories to persistent storage."""
        if not self.persona:
            return

        filepath = os.path.join(
            self.storage_dir, f"{self.persona.lower()}_memories.json"
        )
        try:
            with open(filepath, "w") as f:
                json.dump(
                    {
                        "persona": self.persona,
                        "last_updated": datetime.now().isoformat(),
                        "entries": self.entries,
                    },
                    f,
                    indent=2,
                )
            logger.debug(f"Saved memories for {self.persona}")
        except Exception as e:
            logger.error(f"Failed to save memories for {self.persona}: {str(e)}")

    def _load_memories(self):
        """Load memories from persistent storage."""
        if not self.persona:
            return

        filepath = os.path.join(
            self.storage_dir, f"{self.persona.lower()}_memories.json"
        )
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    self.entries = data.get("entries", [])
                logger.info(f"Loaded {len(self.entries)} memories for {self.persona}")
            except Exception as e:
                logger.error(f"Failed to load memories for {self.persona}: {str(e)}")
                self.entries = []
