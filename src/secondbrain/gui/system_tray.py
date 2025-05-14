"""
System tray application for SecondBrain.
"""

import logging
import asyncio
import threading
from typing import Optional, Dict, Any
import pystray
from PIL import Image
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from ..ai_agent import AIAgent
from ..voice.conversation_loop import ConversationLoop

logger = logging.getLogger(__name__)


class SystemTrayApp:
    def __init__(self):
        self.agent = AIAgent()
        self.conversation_loop = None
        self.icon: Optional[pystray.Icon] = None
        self.suggestion_window: Optional[tk.Tk] = None
        self.status_window: Optional[tk.Tk] = None
        self._stop_event = threading.Event()

    async def initialize(self):
        """Initialize system tray application."""
        try:
            # Initialize AI Agent
            await self.agent.start()

            # Initialize conversation loop
            self.conversation_loop = ConversationLoop(
                self.agent.voice_enhancer,
                self.agent.voice_processor,
                self.agent.recommendation_engine,
            )
            await self.conversation_loop.initialize()

            # Create system tray icon
            self._create_tray_icon()

            logger.info("System tray application initialized")

        except Exception as e:
            logger.error(f"Error initializing system tray app: {e}")
            raise

    def _create_tray_icon(self):
        """Create system tray icon and menu."""
        try:
            # Create icon image (placeholder - replace with actual icon)
            image = Image.new("RGB", (64, 64), color="blue")

            # Create menu
            menu = (
                pystray.MenuItem("Start Listening", self._start_listening),
                pystray.MenuItem("Stop Listening", self._stop_listening),
                pystray.MenuItem("Show Status", self._show_status_window),
                pystray.MenuItem("Show Suggestions", self._show_suggestion_window),
                pystray.MenuItem("Exit", self._quit_app),
            )

            # Create icon
            self.icon = pystray.Icon("SecondBrain", image, "SecondBrain AI", menu)

        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
            raise

    def _start_listening(self):
        """Start background listening."""
        try:
            if not self.conversation_loop.is_listening:
                self.conversation_loop.start_background_listening()
                asyncio.create_task(self.conversation_loop.process_audio_queue())
                self.icon.notify("SecondBrain is now listening")
        except Exception as e:
            logger.error(f"Error starting listening: {e}")
            self.icon.notify("Error starting listening")

    def _stop_listening(self):
        """Stop background listening."""
        try:
            if self.conversation_loop.is_listening:
                self.conversation_loop.stop_background_listening()
                self.icon.notify("SecondBrain stopped listening")
        except Exception as e:
            logger.error(f"Error stopping listening: {e}")
            self.icon.notify("Error stopping listening")

    def _show_status_window(self):
        """Show status window."""
        try:
            if self.status_window:
                self.status_window.destroy()

            self.status_window = tk.Tk()
            self.status_window.title("SecondBrain Status")
            self.status_window.geometry("400x300")

            # Create status display
            status_text = tk.Text(self.status_window, height=15, width=45)
            status_text.pack(padx=10, pady=10)

            async def update_status():
                while True:
                    try:
                        # Get status
                        agent_status = await self.agent.get_status()
                        conv_status = self.conversation_loop.get_status()

                        # Format status
                        status = json.dumps(
                            {**agent_status, "conversation": conv_status}, indent=2
                        )

                        # Update display
                        status_text.delete(1.0, tk.END)
                        status_text.insert(tk.END, status)

                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"Error updating status: {e}")

            # Start status updates
            asyncio.create_task(update_status())

        except Exception as e:
            logger.error(f"Error showing status window: {e}")

    def _show_suggestion_window(self):
        """Show suggestion window."""
        try:
            if self.suggestion_window:
                self.suggestion_window.destroy()

            self.suggestion_window = tk.Tk()
            self.suggestion_window.title("SecondBrain Suggestions")
            self.suggestion_window.geometry("300x400")

            # Create suggestion list
            suggestion_frame = ttk.Frame(self.suggestion_window)
            suggestion_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            suggestions_list = tk.Listbox(suggestion_frame, height=10)
            suggestions_list.pack(fill=tk.BOTH, expand=True)

            # Create speak button
            speak_button = ttk.Button(
                suggestion_frame,
                text="Speak Selected",
                command=lambda: self._speak_selected_suggestion(suggestions_list),
            )
            speak_button.pack(pady=5)

            # Update suggestions periodically
            async def update_suggestions():
                while True:
                    try:
                        # Get current context
                        context = self.agent.get_context()
                        if context:
                            # Get recommendations
                            recommendation = await self.agent.recommendation_engine.get_recommendation(
                                context.data
                            )

                            # Update suggestion list
                            suggestions = recommendation.get("content", {}).get(
                                "suggestions", []
                            )
                            suggestions_list.delete(0, tk.END)
                            for suggestion in suggestions:
                                suggestions_list.insert(tk.END, suggestion)

                        await asyncio.sleep(5)

                    except Exception as e:
                        logger.error(f"Error updating suggestions: {e}")

            # Start suggestion updates
            asyncio.create_task(update_suggestions())

        except Exception as e:
            logger.error(f"Error showing suggestion window: {e}")

    async def _speak_selected_suggestion(self, suggestions_list: tk.Listbox):
        """Speak the selected suggestion."""
        try:
            selection = suggestions_list.curselection()
            if selection:
                suggestion = suggestions_list.get(selection[0])
                await self.conversation_loop.speak_suggestion(suggestion)
        except Exception as e:
            logger.error(f"Error speaking suggestion: {e}")

    def _quit_app(self):
        """Quit the application."""
        try:
            self._stop_event.set()
            asyncio.create_task(self._shutdown())
        except Exception as e:
            logger.error(f"Error quitting app: {e}")

    async def _shutdown(self):
        """Shutdown the application."""
        try:
            # Stop conversation loop
            if self.conversation_loop:
                self.conversation_loop.stop_background_listening()

            # Stop AI agent
            await self.agent.stop()

            # Stop system tray icon
            if self.icon:
                self.icon.stop()

            # Close windows
            if self.status_window:
                self.status_window.destroy()
            if self.suggestion_window:
                self.suggestion_window.destroy()

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def run(self):
        """Run the system tray application."""
        try:
            # Initialize in background thread
            init_thread = threading.Thread(target=self._init_async)
            init_thread.start()
            init_thread.join()

            # Run icon
            self.icon.run()

        except Exception as e:
            logger.error(f"Error running system tray app: {e}")
            raise

    def _init_async(self):
        """Initialize async components."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.initialize())
        except Exception as e:
            logger.error(f"Error in async initialization: {e}")
            raise
