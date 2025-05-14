"""
Example usage of the memory engine and integration with emotion adapter.
"""

import asyncio
import logging
from datetime import datetime

from ..memory.memory_engine import MemoryEngine
from ..memory.memory_integration import MemoryIntegration
from ..persona.emotion_adapter import EmotionAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Example usage of memory and emotion integration."""
    try:
        # Initialize components
        memory_engine = MemoryEngine(memory_file="example_memory.json")
        emotion_adapter = EmotionAdapter()
        integration = MemoryIntegration(memory_engine, emotion_adapter)

        # Example 1: Process and track mood
        logger.info("Example 1: Processing mood")
        mood = await integration.process_mood(
            "excited", context={"source": "user_input", "confidence": 0.8}
        )
        logger.info(f"Processed mood: {mood}")

        # Example 2: Provide feedback
        logger.info("\nExample 2: Providing feedback")
        integration.provide_feedback(
            "excited", is_correct=True, context={"source": "user_feedback"}
        )

        # Example 3: Get mood analysis
        logger.info("\nExample 3: Getting mood analysis")
        analysis = await integration.get_mood_analysis()
        logger.info("Current Analysis:")
        logger.info(f"- Global Mood: {analysis['current_global_mood']}")
        logger.info("- Memory Analytics:")
        for key, value in analysis["memory_analytics"].items():
            logger.info(f"  {key}: {value}")

        # Example 4: Simulate mood changes over time
        logger.info("\nExample 4: Simulating mood changes")
        moods = ["excited", "calm", "neutral", "excited"]
        for mood in moods:
            await integration.process_mood(mood, context={"source": "simulation"})
            logger.info(f"Recorded mood: {mood}")
            await asyncio.sleep(1)  # Simulate time passing

        # Example 5: Check retraining status
        logger.info("\nExample 5: Checking retraining status")
        needs_retraining = memory_engine.needs_retraining()
        logger.info(f"Needs retraining: {needs_retraining}")

        # Example 6: Get mood predictions
        logger.info("\nExample 6: Mood predictions")
        current_mood = memory_engine.get_last_mood()
        predicted = memory_engine.predict_next_mood(current_mood)
        logger.info(f"Current mood: {current_mood}")
        logger.info(f"Predicted next mood: {predicted}")

        # Keep the integration running for a bit to see background tasks
        logger.info("\nRunning background tasks...")
        await asyncio.sleep(10)

    except Exception as e:
        logger.error(f"Error in example: {e}")
    finally:
        # In a real application, you'd want to properly clean up background tasks
        for task in integration.tasks:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
