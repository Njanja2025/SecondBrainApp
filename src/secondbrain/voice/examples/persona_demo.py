"""
Demo script showing how to use different voice personas with emotions and advanced features.
"""

import asyncio
import logging
import json
from pprint import pprint
from ..voice_enhancement import VoiceEnhancer
from ..voice_persona import EmotionType
from ..config import CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_basic_personas():
    """Demonstrate basic persona capabilities."""
    enhancer = VoiceEnhancer()
    await enhancer.initialize()

    # Test different personas with emotions
    scenarios = [
        {
            "persona": "Samantha",
            "emotion": EmotionType.HAPPY,
            "message": "Great news! Your project was a huge success!",
            "context": {"time_of_day": "morning", "user_emotion": "excited"},
        },
        {
            "persona": "Commander",
            "emotion": EmotionType.SERIOUS,
            "message": "Alert: Security protocols have been updated.",
            "context": {"conversation_topic": "security"},
        },
        {
            "persona": "Commander",
            "emotion": EmotionType.EXCITED,
            "message": "Outstanding work, team! Mission accomplished!",
            "context": {"conversation_topic": "project_success"},
        },
        {
            "persona": "HumorBot",
            "emotion": EmotionType.PLAYFUL,
            "message": "Why don't programmers like nature? It has too many bugs! 🐛",
            "context": {"conversation_topic": "casual"},
        },
    ]

    # Demonstrate each persona with emotions and context
    for scenario in scenarios:
        logger.info(
            f"\nTesting {scenario['persona']} persona with {scenario['emotion'].name} emotion:"
        )
        result = enhancer.enhance_voice(
            scenario["message"],
            persona_name=scenario["persona"],
            emotion=scenario["emotion"],
            context=scenario["context"],
        )
        logger.info(f"Original: {result['original']}")
        logger.info(f"Enhanced: {result['enhanced']}")
        logger.info(f"Profile used: {json.dumps(result['profile_used'], indent=2)}")

        # Simulate user rating (random for demo)
        import random

        rating = random.uniform(0.7, 1.0)
        enhancer.rate_response(scenario["message"], rating, scenario["persona"])
        logger.info(f"Response rated: {rating:.2f}")


async def demo_advanced_features():
    """Demonstrate advanced persona features."""
    enhancer = VoiceEnhancer()
    await enhancer.initialize()

    # 1. Demonstrate adaptation over multiple interactions
    logger.info("\nDemonstrating persona adaptation:")
    message = "This is a technical explanation of quantum computing."
    context = {"conversation_topic": "technical", "user_emotion": "focused"}

    for i in range(3):
        logger.info(f"\nIteration {i + 1}:")
        result = enhancer.enhance_voice(
            message,
            persona_name="Commander",
            emotion=EmotionType.SERIOUS,
            context=context,
        )
        logger.info(f"Enhanced: {result['enhanced']}")

        # Simulate user feedback
        rating = 0.5 if i == 0 else 0.9  # First attempt "needs improvement"
        enhancer.rate_response(message, rating)
        logger.info(f"User rating: {rating}")

    # 2. Show persona statistics
    logger.info("\nPersona Statistics:")
    stats = enhancer.get_persona_stats()
    print(json.dumps(stats, indent=2))

    # Bind enhanced Samantha capabilities
    if CONFIG["default_voice"] == "samantha":
        enhancer.persona_manager.bind_voice_persona(
            name="Samantha",
            tone="warm",
            emotion_range=["focused", "serious", "encouraging"],
            memory_persistence=True,
            command_mode=True,
        )
        logger.info(
            "Samantha voice persona now active with memory and emotion tracking."
        )

    # 3. Demonstrate Samantha's enhanced capabilities
    logger.info("\nDemonstrating Samantha's enhanced capabilities:")

    # Test time-aware responses
    time_contexts = [
        {"time_of_day": "morning", "user_emotion": "focused"},
        {"time_of_day": "afternoon", "user_emotion": "tired"},
        {"time_of_day": "evening", "user_emotion": "relaxed"},
    ]

    for ctx in time_contexts:
        result = enhancer.enhance_voice(
            "Let's review your progress.",
            persona_name="Samantha",
            emotion=EmotionType.ENCOURAGING,
            context=ctx,
        )
        logger.info(
            f"\nTime context: {ctx['time_of_day']}, User emotion: {ctx['user_emotion']}"
        )
        logger.info(f"Enhanced: {result['enhanced']}")

    # Test emotion adaptation
    emotion_scenarios = [
        ("I'm feeling stuck on this problem.", "frustrated"),
        ("I just solved a complex issue!", "excited"),
        ("I need to focus on this task.", "focused"),
    ]

    for message, user_emotion in emotion_scenarios:
        context = {"user_emotion": user_emotion, "conversation_topic": "work_progress"}
        result = enhancer.enhance_voice(
            message,
            persona_name="Samantha",
            emotion=EmotionType.EMPATHETIC,
            context=context,
        )
        logger.info(f"\nUser emotion: {user_emotion}")
        logger.info(f"Message: {message}")
        logger.info(f"Samantha's response: {result['enhanced']}")

        # Simulate positive feedback for adaptation
        enhancer.rate_response(message, 0.95)

    # 4. Demonstrate context memory
    logger.info("\nDemonstrating context memory:")
    conversation_flow = [
        {
            "message": "Let's start working on the project.",
            "emotion": EmotionType.FOCUSED,
            "context": {"conversation_topic": "project_start"},
        },
        {
            "message": "You're making excellent progress!",
            "emotion": EmotionType.ENCOURAGING,
            "context": {"conversation_topic": "project_progress"},
        },
        {
            "message": "Here's a summary of what we've accomplished.",
            "emotion": EmotionType.PROFESSIONAL,
            "context": {"conversation_topic": "project_summary"},
        },
    ]

    for step in conversation_flow:
        result = enhancer.enhance_voice(
            step["message"],
            persona_name="Samantha",
            emotion=step["emotion"],
            context=step["context"],
        )
        logger.info(f"\nContext: {step['context']['conversation_topic']}")
        logger.info(f"Emotion: {step['emotion'].name}")
        logger.info(f"Enhanced: {result['enhanced']}")


async def main():
    logger.info("Starting enhanced voice persona demonstration...")

    logger.info("\n=== Basic Persona Features ===")
    await demo_basic_personas()

    logger.info("\n=== Advanced Features ===")
    await demo_advanced_features()

    logger.info("\nDemonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
