"""
Emotion Adapter for online sentiment analysis and emotional learning.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path
import asyncio
from collections import deque
import aiohttp
from textblob import TextBlob

logger = logging.getLogger(__name__)


class EmotionAdapter:
    """Manages online sentiment analysis and emotional learning."""

    def __init__(self, news_api_key: Optional[str] = None):
        self.news_api_key = news_api_key
        self.emotional_log = deque(maxlen=1000)  # Keep last 1000 entries
        self.learning_rate = 0.2
        self.last_update = None
        self.current_global_mood = "neutral"

        # Sentiment thresholds
        self.sentiment_thresholds = {"excited": 0.2, "calm": -0.2, "neutral": 0.0}

        # Learning weights
        self.source_weights = {
            "news": 0.4,
            "user_interaction": 0.3,
            "time_context": 0.2,
            "previous_state": 0.1,
        }

        # Ensure logs directory exists
        self.logs_dir = Path("logs/emotional")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Load previous learning state
        self._load_learning_state()

    async def get_global_mood(self) -> str:
        """
        Analyze global news sentiment to determine mood.

        Returns:
            Emotional tone based on global sentiment
        """
        try:
            if not self.news_api_key:
                logger.warning("News API key not provided")
                return "neutral"

            # Check if we need to update (cache for 1 hour)
            if self.last_update and datetime.now() - self.last_update < timedelta(
                hours=1
            ):
                return self.current_global_mood

            # Get headlines
            async with aiohttp.ClientSession() as session:
                url = "https://newsapi.org/v2/top-headlines"
                params = {"apiKey": self.news_api_key, "language": "en", "pageSize": 5}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        headlines = data.get("articles", [])
                    else:
                        logger.error(f"Failed to fetch news: {response.status}")
                        return self.current_global_mood

            # Analyze sentiment
            total_sentiment = 0
            count = 0

            for article in headlines:
                if description := article.get("description"):
                    blob = TextBlob(description)
                    total_sentiment += blob.sentiment.polarity
                    count += 1

            # Calculate average sentiment
            avg_sentiment = total_sentiment / count if count else 0

            # Determine mood
            if avg_sentiment > self.sentiment_thresholds["excited"]:
                mood = "excited"
            elif avg_sentiment < self.sentiment_thresholds["calm"]:
                mood = "calm"
            else:
                mood = "neutral"

            # Update state
            self.current_global_mood = mood
            self.last_update = datetime.now()

            # Log analysis
            self._log_sentiment_analysis(
                {"sentiment": avg_sentiment, "mood": mood, "sample_size": count}
            )

            return mood

        except Exception as e:
            logger.error(f"Failed to get global mood: {e}")
            return "neutral"

    def log_emotional_context(
        self, source: str, tone: str, info: Dict, feedback: Optional[bool] = None
    ):
        """
        Log emotional context for learning.

        Args:
            source: Source of emotional data
            tone: Detected emotional tone
            info: Additional context information
            feedback: Optional user feedback (True=correct, False=incorrect)
        """
        try:
            # Create log entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "tone": tone,
                "context": info,
                "feedback": feedback,
            }

            # Add to memory
            self.emotional_log.append(entry)

            # Save to file
            self._save_emotional_log()

            # Update learning if feedback provided
            if feedback is not None:
                self._update_learning(entry)

        except Exception as e:
            logger.error(f"Failed to log emotional context: {e}")

    def _update_learning(self, entry: Dict):
        """Update learning parameters based on feedback."""
        try:
            source = entry["source"]
            feedback = entry["feedback"]

            # Adjust source weight
            current_weight = self.source_weights.get(source, 0.1)
            if feedback:
                # Increase weight if correct
                new_weight = current_weight + (
                    self.learning_rate * (1 - current_weight)
                )
            else:
                # Decrease weight if incorrect
                new_weight = current_weight - (self.learning_rate * current_weight)

            self.source_weights[source] = max(0.1, min(0.5, new_weight))

            # Adjust sentiment thresholds
            if entry["context"].get("sentiment"):
                sentiment = entry["context"]["sentiment"]
                tone = entry["tone"]
                if tone in self.sentiment_thresholds:
                    current_threshold = self.sentiment_thresholds[tone]
                    if feedback:
                        # Move threshold closer to this sentiment
                        self.sentiment_thresholds[tone] = (
                            current_threshold * (1 - self.learning_rate)
                            + sentiment * self.learning_rate
                        )

            # Save updated learning state
            self._save_learning_state()

        except Exception as e:
            logger.error(f"Failed to update learning: {e}")

    def _log_sentiment_analysis(self, data: Dict):
        """Log sentiment analysis results."""
        try:
            log_file = self.logs_dir / "sentiment_analysis.json"

            # Load existing logs
            if log_file.exists():
                with open(log_file) as f:
                    logs = json.load(f)
            else:
                logs = []

            # Add new entry
            logs.append({"timestamp": datetime.now().isoformat(), **data})

            # Keep last 1000 entries
            logs = logs[-1000:]

            # Save updated logs
            with open(log_file, "w") as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log sentiment analysis: {e}")

    def _save_emotional_log(self):
        """Save emotional log to file."""
        try:
            log_file = self.logs_dir / "emotional_log.json"

            data = {
                "emotional_log": list(self.emotional_log),
                "timestamp": datetime.now().isoformat(),
            }

            with open(log_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save emotional log: {e}")

    def _save_learning_state(self):
        """Save current learning state."""
        try:
            state_file = self.logs_dir / "learning_state.json"

            state = {
                "sentiment_thresholds": self.sentiment_thresholds,
                "source_weights": self.source_weights,
                "learning_rate": self.learning_rate,
                "timestamp": datetime.now().isoformat(),
            }

            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save learning state: {e}")

    def _load_learning_state(self):
        """Load previous learning state."""
        try:
            state_file = self.logs_dir / "learning_state.json"

            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                self.sentiment_thresholds = state.get(
                    "sentiment_thresholds", self.sentiment_thresholds
                )
                self.source_weights = state.get("source_weights", self.source_weights)
                self.learning_rate = state.get("learning_rate", self.learning_rate)

        except Exception as e:
            logger.error(f"Failed to load learning state: {e}")

    def get_learning_analytics(self) -> Dict:
        """Get analytics about emotional learning."""
        try:
            if not self.emotional_log:
                return {}

            # Convert to list for analysis
            logs = list(self.emotional_log)

            # Analyze feedback accuracy
            feedback_counts = {"correct": 0, "incorrect": 0, "none": 0}
            for entry in logs:
                if entry["feedback"] is True:
                    feedback_counts["correct"] += 1
                elif entry["feedback"] is False:
                    feedback_counts["incorrect"] += 1
                else:
                    feedback_counts["none"] += 1

            # Calculate accuracy
            total_feedback = feedback_counts["correct"] + feedback_counts["incorrect"]
            accuracy = (
                feedback_counts["correct"] / total_feedback if total_feedback > 0 else 0
            )

            return {
                "current_global_mood": self.current_global_mood,
                "learning_rate": self.learning_rate,
                "source_weights": self.source_weights,
                "sentiment_thresholds": self.sentiment_thresholds,
                "feedback_counts": feedback_counts,
                "accuracy": accuracy,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get learning analytics: {e}")
            return {}
