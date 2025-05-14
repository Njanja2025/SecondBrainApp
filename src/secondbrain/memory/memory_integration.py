"""
Integration module to connect memory engine with emotion adapter.
"""

import logging
import asyncio
from typing import Optional, Dict
from datetime import datetime

from ..persona.emotion_adapter import EmotionAdapter
from .memory_engine import MemoryEngine
from .self_train import SelfTrainingManager

logger = logging.getLogger(__name__)


class MemoryIntegration:
    """Integrates memory engine with emotion adapter for unified mood tracking."""

    def __init__(
        self,
        memory_engine: Optional[MemoryEngine] = None,
        emotion_adapter: Optional[EmotionAdapter] = None,
    ):
        self.memory_engine = memory_engine or MemoryEngine()
        self.emotion_adapter = emotion_adapter or EmotionAdapter()
        self.training_manager = SelfTrainingManager(self.memory_engine)

        # Start background tasks
        self.tasks = []
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background tasks for periodic operations."""
        loop = asyncio.get_event_loop()
        self.tasks.extend(
            [
                loop.create_task(self._periodic_retraining()),
                loop.create_task(self._periodic_mood_sync()),
            ]
        )

    async def _periodic_retraining(self):
        """Periodically check and perform retraining if needed."""
        while True:
            try:
                await self.training_manager.check_and_retrain()
            except Exception as e:
                logger.error(f"Error in periodic retraining: {e}")
            finally:
                await asyncio.sleep(3600)  # Check every hour

    async def _periodic_mood_sync(self):
        """Periodically sync mood state between systems."""
        while True:
            try:
                await self._sync_mood_state()
            except Exception as e:
                logger.error(f"Error in mood sync: {e}")
            finally:
                await asyncio.sleep(300)  # Sync every 5 minutes

    async def _sync_mood_state(self):
        """Synchronize mood state between memory and emotion systems."""
        try:
            # Get current global mood
            global_mood = await self.emotion_adapter.get_global_mood()

            # Get last recorded mood from memory
            last_mood = self.memory_engine.get_last_mood()

            # If mood has changed, update memory
            if global_mood != last_mood:
                self.memory_engine.remember_mood(
                    global_mood, context={"source": "global_sync"}
                )

        except Exception as e:
            logger.error(f"Failed to sync mood state: {e}")

    async def process_mood(self, mood: str, context: Optional[Dict] = None) -> str:
        """
        Process and record a new mood observation.

        Args:
            mood: The detected mood
            context: Optional context about the mood

        Returns:
            str: The processed/adjusted mood
        """
        try:
            # Get predicted next mood
            predicted_mood = self.memory_engine.predict_next_mood(mood)

            # Record the actual mood
            self.memory_engine.remember_mood(mood, context)

            # If prediction was different, get feedback from emotion adapter
            if predicted_mood != mood:
                sentiment = await self._get_mood_sentiment(mood)
                self.memory_engine.remember_feedback(
                    predicted_mood,
                    feedback=False,
                    context={"actual": mood, "sentiment": sentiment},
                )

            return mood

        except Exception as e:
            logger.error(f"Error processing mood: {e}")
            return mood

    async def _get_mood_sentiment(self, mood: str) -> float:
        """Get sentiment score for a mood from emotion adapter."""
        try:
            # This is a simplified version - extend based on emotion adapter capabilities
            if hasattr(self.emotion_adapter, "analyze_sentiment"):
                return await self.emotion_adapter.analyze_sentiment(mood)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get mood sentiment: {e}")
            return 0.0

    def provide_feedback(
        self, mood: str, is_correct: bool, context: Optional[Dict] = None
    ):
        """
        Provide feedback about mood prediction accuracy.

        Args:
            mood: The mood being evaluated
            is_correct: Whether the prediction was correct
            context: Optional context about the feedback
        """
        try:
            self.memory_engine.remember_feedback(mood, is_correct, context)

        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")

    async def get_mood_analysis(self) -> Dict:
        """
        Get comprehensive mood analysis from both systems.

        Returns:
            Dict containing combined mood analytics
        """
        try:
            # Get analytics from both systems
            memory_analytics = self.memory_engine.get_mood_analytics()
            global_mood = await self.emotion_adapter.get_global_mood()

            # Combine analytics
            return {
                "current_global_mood": global_mood,
                "memory_analytics": memory_analytics,
                "timestamp": str(datetime.now()),
            }

        except Exception as e:
            logger.error(f"Failed to get mood analysis: {e}")
            return {}
