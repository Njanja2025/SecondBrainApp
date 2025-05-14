import logging
import asyncio
from typing import Callable, Optional
import sys
import os
import openai
from datetime import datetime
import json
from pathlib import Path

# Add the root directory to Python path to import voice_output
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from voice_output import speak

logger = logging.getLogger(__name__)


class Assistant:
    """Handles the AI assistant functionality for SecondBrain."""

    def __init__(self):
        self._running = False
        self.on_response: Optional[Callable[[str], None]] = None
        self.conversation_history = []
        self.load_settings()

    def load_settings(self):
        """Load assistant settings from file."""
        self.settings = {
            "model": "gpt-4-turbo-preview",
            "max_history": 10,
            "temperature": 0.7,
            "system_prompt": (
                "You are a helpful AI assistant integrated into SecondBrain, "
                "a voice-enabled application. Keep responses concise and natural, "
                "as they will be spoken aloud. Aim to be helpful while maintaining "
                "a conversational tone."
            ),
        }

        try:
            settings_path = Path("assistant_settings.json")
            if settings_path.exists():
                self.settings.update(json.loads(settings_path.read_text()))
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

        # Load OpenAI API key from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found in environment variables")

    async def initialize(self):
        """Initialize the assistant components."""
        logger.info("Initializing assistant...")

        if self.api_key:
            openai.api_key = self.api_key
            logger.info("OpenAI API initialized")
        else:
            logger.warning("Running without OpenAI integration")

    async def start(self):
        """Start the assistant service."""
        logger.info("Starting assistant...")
        self._running = True

    async def shutdown(self):
        """Shutdown the assistant cleanly."""
        logger.info("Shutting down assistant...")
        self._running = False

    def _prepare_messages(self, new_message: str) -> list:
        """Prepare message list for OpenAI API."""
        messages = [{"role": "system", "content": self.settings["system_prompt"]}]

        # Add conversation history
        for msg in self.conversation_history[-self.settings["max_history"] :]:
            role = "user" if msg["is_user"] else "assistant"
            messages.append({"role": role, "content": msg["text"]})

        # Add new message
        messages.append({"role": "user", "content": new_message})

        return messages

    async def process_voice_input(self, text: str):
        """Process voice input and generate a response."""
        if not self._running:
            logger.warning("Received input while assistant is not running")
            return

        try:
            logger.info(f"Processing input: {text}")

            # Store user message in history
            self.conversation_history.append(
                {"timestamp": datetime.now().isoformat(), "text": text, "is_user": True}
            )

            # Generate response
            if self.api_key:
                # Use OpenAI API
                messages = self._prepare_messages(text)
                response = await openai.ChatCompletion.acreate(
                    model=self.settings["model"],
                    messages=messages,
                    temperature=self.settings["temperature"],
                )
                response_text = response.choices[0].message.content
            else:
                # Fallback response
                response_text = f"I heard you say: {text}"

            # Store assistant response in history
            self.conversation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "text": response_text,
                    "is_user": False,
                }
            )

            # Trim history if needed
            while len(self.conversation_history) > self.settings["max_history"]:
                self.conversation_history.pop(0)

            # Speak the response
            speak(response_text)

            # Update GUI if handler is registered
            if self.on_response:
                self.on_response(response_text)
            else:
                logger.warning("Response generated but no handler registered")

        except Exception as e:
            logger.error(f"Error processing input: {e}")
            error_msg = "Sorry, I encountered an error processing your request."
            speak(error_msg)
            if self.on_response:
                self.on_response(error_msg)
