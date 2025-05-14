"""
Autonomous Executor for handling voice commands with contextual awareness.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AutonomousExecutor:
    """Executes commands autonomously with persona-aware responses."""

    def __init__(self, calibrator, voice_system):
        """
        Initialize autonomous executor.

        Args:
            calibrator: PersonaCalibrator instance
            voice_system: Voice system instance
        """
        self.calibrator = calibrator
        self.voice_system = voice_system
        self.command_history = []
        self._init_response_templates()

    def _init_response_templates(self):
        """Initialize response templates for different contexts."""
        self.response_templates = {
            "empathetic": [
                "I understand you're feeling {emotion}. {response}",
                "I hear that you're {emotion}. Let me help you with {response}",
                "It sounds like you're feeling {emotion}. {response}",
            ],
            "cheerful": [
                "Great to hear from you! {response}",
                "I'm happy to help! {response}",
                "Wonderful! {response}",
            ],
            "calm": [
                "Let me help you with that. {response}",
                "I can assist you. {response}",
                "Here's what I found: {response}",
            ],
            "patient": [
                "Let me explain this clearly. {response}",
                "Take your time. {response}",
                "I'll guide you through this. {response}",
            ],
            "reassuring": [
                "Don't worry, I can help you with that. {response}",
                "I'm here to help. {response}",
                "We'll figure this out together. {response}",
            ],
            "professional": [
                "{response}",
                "Here's what I found: {response}",
                "According to my analysis: {response}",
            ],
        }

    async def run_command(self, command_text: str) -> Dict[str, Any]:
        """
        Process and execute a command with appropriate persona response.

        Args:
            command_text: Command text to process

        Returns:
            Response data dictionary
        """
        try:
            # Get persona profile for this command
            profile = self.calibrator.calibrate(command_text)

            # Process command
            command_result = await self._process_command(command_text, profile)

            # Generate appropriate response
            response = self._generate_response(command_result, profile)

            # Apply voice modulation
            self._apply_voice_settings(profile)

            # Speak response
            await self._speak_response(response, profile)

            # Update command history
            self._update_history(command_text, response, profile)

            return {
                "command": command_text,
                "response": response,
                "profile": profile,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            return self._generate_error_response(str(e))

    async def _process_command(
        self, command: str, profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a command with context awareness.

        Args:
            command: Command to process
            profile: Current persona profile

        Returns:
            Processed command result
        """
        try:
            # Add processing delay based on profile
            await self._apply_delay(profile["response_delay"])

            # Process command through voice system
            result = await self.voice_system.process_command(command)

            return {
                "status": "success",
                "result": result,
                "confidence": 0.9,  # Example confidence score
                "context": profile["emotion_context"],
            }

        except Exception as e:
            logger.error(f"Command processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "confidence": 0.0,
                "context": profile["emotion_context"],
            }

    def _generate_response(
        self, result: Dict[str, Any], profile: Dict[str, Any]
    ) -> str:
        """
        Generate appropriate response based on result and profile.

        Args:
            result: Command processing result
            profile: Current persona profile

        Returns:
            Generated response string
        """
        try:
            # Get appropriate response template
            templates = self.response_templates.get(
                profile["tone"], self.response_templates["professional"]
            )

            # Select template based on context
            template = templates[0]  # Could implement more sophisticated selection

            # Format response
            base_response = result.get("result", "I couldn't process that command.")
            response = template.format(
                emotion=profile["emotion_context"], response=base_response
            )

            return response

        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return "I apologize, but I'm having trouble formulating a response."

    def _apply_voice_settings(self, profile: Dict[str, Any]):
        """
        Apply voice modulation settings.

        Args:
            profile: Current persona profile
        """
        try:
            modulation = profile["voice_modulation"]
            self.voice_system.emotion_adapter.adjust_voice(
                profile["emotion_context"],
                intensity=0.8,  # Could be dynamic based on context
            )

        except Exception as e:
            logger.error(f"Failed to apply voice settings: {str(e)}")

    async def _speak_response(self, response: str, profile: Dict[str, Any]):
        """
        Speak response with appropriate timing and modulation.

        Args:
            response: Response text to speak
            profile: Current persona profile
        """
        try:
            # Apply any pre-speech delay
            await self._apply_delay(profile["response_delay"])

            # Speak through voice system
            await self.voice_system.speak(response)

        except Exception as e:
            logger.error(f"Failed to speak response: {str(e)}")

    async def _apply_delay(self, delay_type: str):
        """
        Apply appropriate response delay.

        Args:
            delay_type: Type of delay to apply
        """
        delays = {"slow": 2.0, "moderate": 1.0, "normal": 0.5}
        await asyncio.sleep(delays.get(delay_type, 0.5))

    def _update_history(self, command: str, response: str, profile: Dict[str, Any]):
        """
        Update command execution history.

        Args:
            command: Executed command
            response: Generated response
            profile: Used persona profile
        """
        self.command_history.append(
            {
                "command": command,
                "response": response,
                "profile": profile,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _generate_error_response(self, error: str) -> Dict[str, Any]:
        """
        Generate error response.

        Args:
            error: Error message

        Returns:
            Error response dictionary
        """
        return {
            "status": "error",
            "error": error,
            "response": "I apologize, but I encountered an error processing your request.",
            "timestamp": datetime.now().isoformat(),
        }

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get command execution history."""
        return self.command_history

    def clear_history(self):
        """Clear execution history."""
        self.command_history = []
        logger.info("Cleared execution history")
