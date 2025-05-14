import asyncio
import logging
from secondbrain.voice.voice_processor import VoiceProcessor
from secondbrain.voice.voice_persona import VoicePersonaManager, EmotionType, VoiceStyle

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Initialize voice processor
    voice_proc = VoiceProcessor()
    await voice_proc.initialize()

    # Initialize persona manager
    persona_manager = VoicePersonaManager()

    # Set up Samantha as the default persona
    persona_manager.set_default("Samantha")
    samantha = persona_manager.get_persona("Samantha")

    # Enable voice output for Samantha
    samantha.enable_voice()

    # Example context for morning greeting
    context = {
        "time_of_day": "morning",
        "user_emotion": "neutral",
        "conversation_topic": "greeting",
    }

    # Demonstrate different emotional responses
    greetings = [
        (EmotionType.HAPPY, "Good morning! It's great to see you today!"),
        (EmotionType.CALM, "I hope you're having a peaceful start to your day."),
        (EmotionType.PROFESSIONAL, "Here's your morning briefing and schedule."),
    ]

    for emotion, message in greetings:
        logger.info(f"\nSpeaking with emotion: {emotion.name}")
        samantha.speak(message, emotion=emotion, context=context)
        await asyncio.sleep(2)  # Wait between messages

    # Demonstrate voice command processing
    test_commands = [
        "what's on my schedule today",
        "set a reminder for 2pm meeting",
        "send an email to John",
    ]

    for command in test_commands:
        logger.info(f"\nProcessing command: {command}")
        result = await voice_proc.process_command(command, None)
        logger.info(f"Command result: {result}")
        await asyncio.sleep(1)

    # Clean up
    await voice_proc.stop()


if __name__ == "__main__":
    asyncio.run(main())
