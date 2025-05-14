"""
Main integration module for the SecondBrain voice system.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from .voice_processor import VoiceProcessor, VoiceEngine
from .voice_persona import VoicePersonaManager, EmotionType
from .emotion_voice_adapter import EmotionVoiceAdapter
from .wake_word_listener import WakeWordListener
from .samantha_memory_dashboard import MemoryDashboard
from ..persona.calibrator import PersonaCalibrator
from ..ai.autonomous_executor import AutonomousExecutor

logger = logging.getLogger(__name__)


class SamanthaVoiceSystem:
    """Main voice system integration class."""

    def __init__(self):
        self.voice_engine = VoiceEngine("Samantha")
        self.emotion_adapter = EmotionVoiceAdapter(self.voice_engine)
        self.persona_manager = VoicePersonaManager()
        self.voice_processor = None
        self.wake_listener = None
        self.dashboard = None

        # Initialize new components
        self.calibrator = PersonaCalibrator(self)
        self.executor = AutonomousExecutor(self.calibrator, self)

        # Memory tracking
        self.interaction_history = []
        self.emotion_history = []

    async def initialize(self):
        """Initialize all system components."""
        try:
            logger.info("Initializing Samantha Voice System...")

            # Initialize voice processor
            self.voice_processor = VoiceProcessor()
            await self.voice_processor.initialize()

            # Set up wake word listener with enhanced wake words
            self.wake_listener = WakeWordListener(
                wake_words=["samantha", "hey samantha", "ok samantha", "assistant"],
                threshold=0.6,
            )

            # Configure default persona
            self.persona_manager.set_default("Samantha")
            samantha = self.persona_manager.get_persona("Samantha")
            samantha.enable_voice()

            # Initialize dashboard
            self.dashboard = MemoryDashboard()

            logger.info("Samantha Voice System initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize voice system: {str(e)}")
            raise

    def start(self):
        """Start the voice system."""
        try:
            # Start wake word listener with autonomous execution
            self.wake_listener.start(self._on_wake_word_autonomous)

            # Start dashboard
            self.dashboard.run()

            logger.info("Samantha Voice System started")

        except Exception as e:
            logger.error(f"Failed to start voice system: {str(e)}")
            raise

    async def stop(self):
        """Stop the voice system."""
        try:
            # Stop wake word listener
            if self.wake_listener:
                self.wake_listener.stop()

            # Stop voice processor
            if self.voice_processor:
                await self.voice_processor.stop()

            logger.info("Samantha Voice System stopped")

        except Exception as e:
            logger.error(f"Failed to stop voice system: {str(e)}")

    async def _on_wake_word_autonomous(self, text: str):
        """
        Handle wake word detection with autonomous execution.

        Args:
            text: Recognized text containing wake word
        """
        try:
            # Get current persona profile
            profile = self.calibrator.calibrate(text)

            # Generate wake word response
            response = await self.executor.run_command(text)

            # Update dashboard with wake word interaction
            self._update_dashboard(
                {
                    "wake_word_detected": text,
                    "response": response,
                    "profile": profile,
                    "type": "wake_word",
                }
            )

        except Exception as e:
            logger.error(f"Failed to handle wake word autonomously: {str(e)}")

    async def process_command(self, command: str):
        """
        Process a voice command with autonomous execution.

        Args:
            command: Voice command to process
        """
        try:
            # Execute command through autonomous executor
            result = await self.executor.run_command(command)

            # Update dashboard
            self._update_dashboard(
                {"command": command, "result": result, "type": "command"}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to process command: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def speak(self, text: str, emotion: str = None):
        """
        Speak text with emotion awareness.

        Args:
            text: Text to speak
            emotion: Optional emotion to use
        """
        try:
            # Get current profile if emotion not specified
            if not emotion:
                profile = self.calibrator.get_last_profile()
                if profile:
                    emotion = profile["emotion_context"]

            # Adjust voice based on emotion
            if emotion:
                self.emotion_adapter.adjust_voice(emotion)

            # Get current persona
            persona = self.persona_manager.get_default_persona()

            # Speak with emotion
            if emotion:
                persona.speak(text, emotion=EmotionType[emotion.upper()])
            else:
                persona.speak(text)

        except Exception as e:
            logger.error(f"Failed to speak: {str(e)}")

    def _update_dashboard(self, data: Dict[str, Any]):
        """
        Update dashboard with new data.

        Args:
            data: New data to display
        """
        try:
            if self.dashboard:
                # Update memory log
                self.dashboard.update_memory_log(data)

                # Update stats
                stats = {
                    "Total Interactions": len(self.interaction_history),
                    "Average Response Time": self._calculate_avg_response_time(),
                    "Successful Commands": self._count_successful_commands(),
                    "Memory Usage": len(str(self.interaction_history)),
                    "Active Learning Rate": self._calculate_learning_rate(),
                }
                self.dashboard.update_stats(stats)

                # Update emotion state if profile available
                if "profile" in data:
                    emotion_data = {
                        "current_emotion": data["profile"]["emotion_context"],
                        "intensity": data.get("result", {}).get("confidence", 1.0),
                        "history": self.emotion_history[-10:],
                    }
                    self.dashboard.update_emotion_state(emotion_data)

        except Exception as e:
            logger.error(f"Failed to update dashboard: {str(e)}")

    def _calculate_avg_response_time(self) -> float:
        """Calculate average command response time."""
        if not self.interaction_history:
            return 0.0

        total_time = sum(
            result.get("processing_time", 0)
            for entry in self.interaction_history
            for result in [entry.get("result", {})]
        )
        return total_time / len(self.interaction_history)

    def _count_successful_commands(self) -> int:
        """Count number of successful commands."""
        return sum(
            1
            for entry in self.interaction_history
            if entry.get("result", {}).get("status") == "success"
        )

    def _calculate_learning_rate(self) -> float:
        """Calculate system learning rate based on command success trend."""
        if len(self.interaction_history) < 2:
            return 0.0

        recent = self.interaction_history[-10:]  # Last 10 interactions
        success_rate = sum(
            1 for entry in recent if entry.get("result", {}).get("status") == "success"
        ) / len(recent)

        return success_rate


async def main():
    """Main entry point for the voice system."""
    try:
        # Initialize system
        system = SamanthaVoiceSystem()
        await system.initialize()

        # Start system
        system.start()

        # Example autonomous commands
        await system.process_command("Samantha, I'm feeling a bit sad today.")
        await system.process_command("What's the weather like tomorrow?")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            await system.stop()

    except Exception as e:
        logger.error(f"System error: {str(e)}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
