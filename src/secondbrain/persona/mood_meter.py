"""
Mood Meter for tracking and visualizing Samantha's emotional state over time.
"""

import logging
import tkinter as tk
from tkinter import ttk
from collections import Counter, deque
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


class MoodMeter:
    """Tracks and visualizes emotional state over time."""

    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root
        self.mood_frame = None
        self.mood_canvas = None
        self.mood_label = None
        self.emotional_log = deque(maxlen=1000)  # Keep last 1000 emotions
        self.current_mood = "neutral"
        self.mood_intensity = 0.5  # 0.0 to 1.0

        # Color mapping for different moods
        self.color_map = {
            "calm": "#4FB0C6",  # Serene blue
            "excited": "#FFB347",  # Warm orange
            "attentive": "#98FB98",  # Mint green
            "neutral": "#E0E0E0",  # Light gray
            "thoughtful": "#DDA0DD",  # Soft purple
            "focused": "#87CEEB",  # Sky blue
        }

        # Mood transition weights
        self.mood_weights = {
            "calm": 0.2,
            "excited": 0.3,
            "attentive": 0.25,
            "thoughtful": 0.15,
            "focused": 0.25,
            "neutral": 0.1,
        }

        self._setup_mood_display()

    def _setup_mood_display(self):
        """Set up the mood meter display."""
        if not self.root:
            return

        # Create mood frame
        self.mood_frame = ttk.Frame(self.root)
        self.mood_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.Y)

        # Create mood label
        self.mood_label = ttk.Label(
            self.mood_frame,
            text="Current Mood: Neutral",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.mood_label.pack(pady=5)

        # Create mood canvas
        self.mood_canvas = tk.Canvas(
            self.mood_frame, width=30, height=200, bg=self.color_map["neutral"]
        )
        self.mood_canvas.pack(pady=5)

        # Create intensity scale
        self.intensity_scale = ttk.Scale(
            self.mood_frame, from_=1.0, to=0.0, orient=tk.VERTICAL, length=200
        )
        self.intensity_scale.set(0.5)
        self.intensity_scale.pack(pady=5, padx=5)

    def update_mood(self, tone: str, intensity: float = 0.5) -> str:
        """
        Update the mood based on new emotional input.

        Args:
            tone: The emotional tone
            intensity: Emotional intensity (0.0 to 1.0)

        Returns:
            Current mood
        """
        try:
            # Log the emotion
            self.emotional_log.append(
                {
                    "tone": tone,
                    "intensity": intensity,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Calculate mood from recent history
            recent_tones = [log["tone"] for log in list(self.emotional_log)[-10:]]
            tone_counts = Counter(recent_tones)

            # Weight the emotions
            weighted_counts = {
                tone: count * self.mood_weights.get(tone, 0.1)
                for tone, count in tone_counts.items()
            }

            # Get dominant mood
            if weighted_counts:
                self.current_mood = max(weighted_counts.items(), key=lambda x: x[1])[0]
            else:
                self.current_mood = "neutral"

            # Update intensity with smoothing
            self.mood_intensity = (self.mood_intensity * 0.7) + (intensity * 0.3)

            # Update display
            self._update_display()

            return self.current_mood

        except Exception as e:
            logger.error(f"Failed to update mood: {e}")
            return "neutral"

    def _update_display(self):
        """Update the mood meter display."""
        if not all([self.mood_canvas, self.mood_label, self.intensity_scale]):
            return

        try:
            # Update color
            color = self.color_map.get(self.current_mood, self.color_map["neutral"])
            self.mood_canvas.configure(bg=color)

            # Update label
            self.mood_label.configure(text=f"Current Mood: {self.current_mood.title()}")

            # Update intensity scale
            self.intensity_scale.set(self.mood_intensity)

        except Exception as e:
            logger.error(f"Failed to update mood display: {e}")

    def get_mood_analytics(self) -> Dict:
        """Get analytics about emotional patterns."""
        try:
            if not self.emotional_log:
                return {}

            # Convert to list for analysis
            logs = list(self.emotional_log)

            # Get overall tone distribution
            tone_dist = Counter(log["tone"] for log in logs)
            total = sum(tone_dist.values()) or 1

            # Calculate average intensity
            avg_intensity = sum(log["intensity"] for log in logs) / len(logs)

            # Get mood transitions
            transitions = []
            for i in range(1, len(logs)):
                prev = logs[i - 1]["tone"]
                curr = logs[i]["tone"]
                if prev != curr:
                    transitions.append((prev, curr))

            return {
                "current_mood": self.current_mood,
                "mood_intensity": self.mood_intensity,
                "tone_distribution": {
                    tone: count / total for tone, count in tone_dist.items()
                },
                "average_intensity": avg_intensity,
                "common_transitions": Counter(transitions).most_common(5),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate mood analytics: {e}")
            return {}

    def save_emotional_log(self, filepath: str = "emotional_log.json"):
        """Save emotional log to file."""
        try:
            data = {
                "emotional_log": list(self.emotional_log),
                "current_mood": self.current_mood,
                "mood_intensity": self.mood_intensity,
                "timestamp": datetime.now().isoformat(),
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save emotional log: {e}")

    def load_emotional_log(self, filepath: str = "emotional_log.json"):
        """Load emotional log from file."""
        try:
            if not os.path.exists(filepath):
                return

            with open(filepath, "r") as f:
                data = json.load(f)

            self.emotional_log = deque(data["emotional_log"], maxlen=1000)
            self.current_mood = data.get("current_mood", "neutral")
            self.mood_intensity = data.get("mood_intensity", 0.5)

            # Update display
            self._update_display()

        except Exception as e:
            logger.error(f"Failed to load emotional log: {e}")
