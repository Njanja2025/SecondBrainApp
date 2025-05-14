"""
Real-time conversation loop manager for SecondBrain.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import threading
import queue
import sounddevice as sd
import numpy as np
from ..core.phantom_mcp import PhantomMCP

logger = logging.getLogger(__name__)


class ConversationLoop:
    def __init__(self, voice_enhancer, voice_processor, recommendation_engine):
        self.voice_enhancer = voice_enhancer
        self.voice_processor = voice_processor
        self.recommendation_engine = recommendation_engine
        self.phantom_mcp = PhantomMCP()

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024

        # State management
        self.is_listening = False
        self.is_processing = False
        self.audio_queue = queue.Queue()
        self.background_thread = None
        self._stop_event = threading.Event()

    async def initialize(self):
        """Initialize conversation loop."""
        try:
            await self.phantom_mcp.initialize()
            logger.info("Conversation loop initialized")
        except Exception as e:
            logger.error(f"Error initializing conversation loop: {e}")
            raise

    def start_background_listening(self):
        """Start background listening thread."""
        try:
            self._stop_event.clear()
            self.is_listening = True
            self.background_thread = threading.Thread(target=self._audio_capture_loop)
            self.background_thread.daemon = True
            self.background_thread.start()
            logger.info("Background listening started")
        except Exception as e:
            logger.error(f"Error starting background listening: {e}")
            raise

    def stop_background_listening(self):
        """Stop background listening thread."""
        try:
            self._stop_event.set()
            self.is_listening = False
            if self.background_thread:
                self.background_thread.join()
            logger.info("Background listening stopped")
        except Exception as e:
            logger.error(f"Error stopping background listening: {e}")

    def _audio_capture_loop(self):
        """Continuous audio capture loop."""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
            ):
                while not self._stop_event.is_set():
                    self._stop_event.wait(0.1)
        except Exception as e:
            logger.error(f"Error in audio capture loop: {e}")
            self.is_listening = False

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input."""
        try:
            if status:
                logger.warning(f"Audio callback status: {status}")
            if not self.is_processing:
                self.audio_queue.put(indata.copy())
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")

    async def process_audio_queue(self):
        """Process audio from queue."""
        try:
            while self.is_listening:
                if not self.audio_queue.empty():
                    self.is_processing = True

                    # Get audio chunk
                    audio_data = self.audio_queue.get()

                    # Enhance audio
                    enhanced_audio, metrics = await self.voice_enhancer.enhance_audio(
                        audio_data
                    )

                    # Process for speech
                    command = await self.voice_processor.process_audio(enhanced_audio)

                    if command:
                        # Get AI recommendation
                        context = {
                            "command": command,
                            "audio_metrics": metrics,
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                        recommendation = (
                            await self.recommendation_engine.get_recommendation(context)
                        )

                        # Generate and enhance response
                        response = await self._generate_response(
                            command, recommendation
                        )
                        enhanced_response = (
                            await self.voice_enhancer.enhance_voice_output(
                                response, recommendation.get("delivery", {})
                            )
                        )

                        # Play response
                        await self.voice_processor.play_audio(enhanced_response)

                    self.is_processing = False

                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error processing audio queue: {e}")
            self.is_processing = False

    async def _generate_response(
        self, command: str, recommendation: Dict[str, Any]
    ) -> str:
        """Generate response based on command and recommendation."""
        try:
            content = recommendation.get("content", {})
            message = content.get("message", "")
            suggestions = content.get("suggestions", [])

            response = message
            if suggestions:
                response += "\nSuggestions:\n" + "\n".join(
                    f"- {s}" for s in suggestions
                )

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I understood: {command}"

    async def speak_suggestion(self, suggestion: str):
        """Speak a specific suggestion."""
        try:
            # Get recommendation for delivery
            context = {
                "type": "suggestion",
                "text": suggestion,
                "timestamp": asyncio.get_event_loop().time(),
            }
            recommendation = await self.recommendation_engine.get_recommendation(
                context
            )

            # Enhance and play audio
            enhanced_audio = await self.voice_enhancer.enhance_voice_output(
                suggestion, recommendation.get("delivery", {})
            )
            await self.voice_processor.play_audio(enhanced_audio)

            logger.info(f"Spoke suggestion: {suggestion}")

        except Exception as e:
            logger.error(f"Error speaking suggestion: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get current conversation loop status."""
        return {
            "is_listening": self.is_listening,
            "is_processing": self.is_processing,
            "queue_size": self.audio_queue.qsize(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
        }

    async def health_check(self) -> str:
        """Perform health check."""
        try:
            if not self.is_listening:
                return "stopped"
            if not self.background_thread or not self.background_thread.is_alive():
                return "error"
            return "running"
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return "error"
