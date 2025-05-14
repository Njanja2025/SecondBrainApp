"""
Voice Assistant - Voice Interaction System
Handles voice input/output and voice command processing.
"""

import logging
import threading
import queue
import speech_recognition as sr
import pyttsx3
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from typing import Optional, Callable, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from .error_handler import ErrorHandler, ErrorSeverity
import json
import os
import zipfile
import shutil
import csv
import yaml
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CommandContext:
    """Context information for command processing."""

    timestamp: datetime
    confidence: float
    raw_text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class VoiceAssistant:
    """Manages voice interaction capabilities."""

    def __init__(self):
        """Initialize the voice assistant."""
        self.is_listening = False
        self.command_queue = queue.Queue()
        self.command_handlers: Dict[str, Callable] = {}
        self.context: Dict[str, Any] = {}
        self.recognizer = None
        self.engine = None
        self.plugins: Dict[str, Any] = {}
        self.error_handler = ErrorHandler()
        self._setup()
        self._register_builtin_commands()

    def _setup(self) -> None:
        """Set up voice recognition and synthesis."""
        try:
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = (
                0.8  # Shorter pause threshold for more responsive commands
            )

            # Initialize text-to-speech engine
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)  # Speed of speech
            self.engine.setProperty("volume", 0.9)  # Volume level

            # Set default voice
            voices = self.engine.getProperty("voices")
            if voices:
                self.engine.setProperty("voice", voices[0].id)

            # Download NLTK data if needed
            self._setup_nltk()

            logger.info("Voice assistant initialized successfully")
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.CRITICAL)
            raise

    def _setup_nltk(self) -> None:
        """Set up NLTK resources."""
        try:
            required_packages = [
                "punkt",
                "averaged_perceptron_tagger",
                "maxent_ne_chunker",
                "words",
            ]
            for package in required_packages:
                try:
                    nltk.data.find(
                        f"tokenizers/{package}"
                        if package == "punkt"
                        else f"taggers/{package}"
                    )
                except LookupError:
                    nltk.download(package)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            raise

    def register_plugin(self, plugin: Any) -> bool:
        """Register a plugin with the voice assistant."""
        try:
            if hasattr(plugin, "is_plugin") and plugin.is_plugin:
                plugin_name = plugin.name.lower()
                self.plugins[plugin_name] = plugin
                if hasattr(plugin, "register_commands"):
                    plugin.register_commands(self)
                logger.info(f"Registered plugin: {plugin_name}")
                return True
            return False
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return False

    def start_listening(self) -> None:
        """Start listening for voice commands."""
        if self.is_listening:
            return

        self.is_listening = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        logger.info("Voice assistant started listening")

    def stop_listening(self) -> None:
        """Stop listening for voice commands."""
        self.is_listening = False
        logger.info("Voice assistant stopped listening")

    def _listen_loop(self) -> None:
        """Main loop for listening to voice input."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            while self.is_listening:
                try:
                    audio = self.recognizer.listen(
                        source, timeout=5, phrase_time_limit=5
                    )
                    text = self.recognizer.recognize_google(audio)
                    confidence = self.recognizer.recognize_google(
                        audio, show_all=True
                    ).get("confidence", 0.0)

                    logger.info(f"Recognized: {text} (confidence: {confidence:.2f})")

                    # Create command context
                    context = CommandContext(
                        timestamp=datetime.now(),
                        confidence=confidence,
                        raw_text=text,
                        user_id=self.context.get("user_id"),
                        session_id=self.context.get("session_id"),
                    )

                    # Process the command with NLP
                    command, args = self._parse_command(text)
                    result = self.process_command(command, args, context)

                    if result:
                        self.speak(str(result))
                    else:
                        self.speak("I'm sorry, I didn't understand that command.")

                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    logger.debug("Could not understand audio")
                except sr.RequestError as e:
                    error_msg = self.error_handler.handle_error(
                        e,
                        ErrorSeverity.ERROR,
                        command="speech_recognition",
                        user_id=self.context.get("user_id"),
                        session_id=self.context.get("session_id"),
                    )
                    self.speak(error_msg)
                except Exception as e:
                    error_msg = self.error_handler.handle_error(
                        e,
                        ErrorSeverity.ERROR,
                        command="voice_recognition",
                        user_id=self.context.get("user_id"),
                        session_id=self.context.get("session_id"),
                    )
                    self.speak(error_msg)

    def _parse_command(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Parse natural language command into command and arguments."""
        try:
            # Tokenize and tag parts of speech
            tokens = word_tokenize(text.lower())
            tagged = pos_tag(tokens)

            # Extract command and arguments
            command = tokens[0] if tokens else ""
            args = {}

            # Look for location arguments (proper nouns)
            locations = [word for word, tag in tagged if tag == "NNP"]
            if locations:
                args["location"] = locations[0]

            # Look for time arguments
            time_words = ["now", "today", "tomorrow", "yesterday"]
            for word in tokens:
                if word in time_words:
                    args["time"] = word

            # Look for numeric arguments
            numbers = [word for word, tag in tagged if tag == "CD"]
            if numbers:
                args["number"] = float(numbers[0])

            # Look for boolean arguments
            bool_words = ["yes", "no", "true", "false"]
            for word in tokens:
                if word in bool_words:
                    args["boolean"] = word in ["yes", "true"]

            return command, args
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return text.lower(), {}

    def register_command(self, command: str, handler: Callable) -> None:
        """Register a command handler."""
        self.command_handlers[command.lower()] = handler
        logger.info(f"Registered command handler for: {command}")

    def process_command(
        self,
        command: str,
        args: Dict[str, Any] = None,
        context: Optional[CommandContext] = None,
    ) -> Optional[Any]:
        """Process a voice command with arguments."""
        try:
            command = command.lower()

            # Check if command exists in handlers
            if command in self.command_handlers:
                return self.command_handlers[command](**(args or {}))

            # Check if command exists in plugins
            for plugin in self.plugins.values():
                if hasattr(plugin, f"_handle_{command}_command"):
                    handler = getattr(plugin, f"_handle_{command}_command")
                    return handler(**(args or {}))

            return None
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorSeverity.ERROR,
                command=command,
                args=args,
                user_id=context.user_id if context else None,
                session_id=context.session_id if context else None,
            )
            return None

    def speak(self, text: str) -> None:
        """Convert text to speech."""
        try:
            if self.engine:
                # Add a small pause between sentences
                text = text.replace(".", ". ").replace("!", "! ").replace("?", "? ")
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)

    def set_voice(self, voice_id: str) -> bool:
        """Set the voice for text-to-speech."""
        try:
            if self.engine:
                self.engine.setProperty("voice", voice_id)
                return True
            return False
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return False

    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices."""
        try:
            if self.engine:
                voices = self.engine.getProperty("voices")
                return [{"id": v.id, "name": v.name} for v in voices]
            return []
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return []

    def set_context(self, key: str, value: Any) -> None:
        """Set context value."""
        self.context[key] = value

    def get_context(self, key: str) -> Optional[Any]:
        """Get context value."""
        return self.context.get(key)

    def clear_context(self) -> None:
        """Clear all context values."""
        self.context.clear()

    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """Get information about registered plugins."""
        try:
            return [
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "commands": plugin.get_commands(),
                }
                for plugin in self.plugins.values()
            ]
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return []

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        return self.error_handler.get_summary()

    def _register_builtin_commands(self) -> None:
        """Register built-in voice commands."""
        try:
            # Basic commands
            self.register_command("help", self._handle_help_command)
            self.register_command("status", self._handle_status_command)
            self.register_command("volume", self._handle_volume_command)
            self.register_command("language", self._handle_language_command)
            self.register_command("clear", self._handle_clear_command)
            self.register_command("exit", self._handle_exit_command)

            # Speech control
            self.register_command("rate", self._handle_rate_command)
            self.register_command("pause", self._handle_pause_command)
            self.register_command("resume", self._handle_resume_command)
            self.register_command("stop", self._handle_stop_command)
            self.register_command("voices", self._handle_list_voices_command)

            # Context and debugging
            self.register_command("context", self._handle_context_command)
            self.register_command("debug", self._handle_debug_command)

            # Settings management
            self.register_command("save", self._handle_save_command)
            self.register_command("load", self._handle_load_command)
            self.register_command("reset", self._handle_reset_command)
            self.register_command("backup", self._handle_backup_command)
            self.register_command("restore", self._handle_restore_command)
            self.register_command("update", self._handle_update_command)
            self.register_command("sync", self._handle_sync_command)

            # Voice control
            self.register_command("mute", self._handle_mute_command)
            self.register_command("unmute", self._handle_unmute_command)
            self.register_command("speed", self._handle_speed_command)
            self.register_command("pitch", self._handle_pitch_command)

            # Settings import/export
            self.register_command("export", self._handle_export_command)
            self.register_command("import", self._handle_import_command)
            self.register_command("config", self._handle_config_command)

            # Plugin management
            self.register_command("plugins", self._handle_plugins_command)
            self.register_command("version", self._handle_version_command)
            self.register_command("health", self._handle_health_command)

            # New command
            self.register_command("system", self._handle_system_command)

            logger.info("Registered built-in commands")
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)

    def _handle_help_command(self) -> str:
        """Handle help command."""
        try:
            commands = []

            # Add built-in commands
            commands.extend(
                [
                    "help - Show this help message",
                    "status - Show system status",
                    "volume <number> - Set volume (0-100)",
                    "language <code> - Set language",
                    "clear - Clear context",
                    "exit - Exit the program",
                    "rate <number> - Set speech rate",
                    "pause - Pause speech",
                    "resume - Resume speech",
                    "stop - Stop speech",
                    "voices - List available voices",
                    "context - Show context",
                    "debug - Show debug info",
                    "save <file> - Save settings",
                    "load <file> - Load settings",
                    "reset - Reset settings",
                    "backup - Create backup",
                    "restore - Restore backup",
                    "update - Update system",
                    "sync - Sync settings",
                    "mute - Mute voice",
                    "unmute - Unmute voice",
                    "speed <number> - Set speech speed",
                    "pitch <number> - Set speech pitch",
                    "export <format> - Export settings",
                    "import <file> - Import settings",
                    "config <key> <value> - Set config",
                    "plugins - List plugins",
                    "version - Show version",
                    "health - Check system health",
                ]
            )

            # Add plugin commands
            for plugin in self.plugins.values():
                if hasattr(plugin, "get_commands"):
                    commands.extend(plugin.get_commands().split("\n"))

            return "\n".join(commands)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error getting help information"

    def _handle_status_command(self) -> str:
        """Handle status command."""
        try:
            status = [
                "System Status:",
                f"Listening: {'Yes' if self.is_listening else 'No'}",
                f"Plugins: {len(self.plugins)}",
                f"Commands: {len(self.command_handlers)}",
                f"Context: {len(self.context)} items",
            ]

            # Add plugin status
            for plugin in self.plugins.values():
                if hasattr(plugin, "get_status"):
                    status.append(f"{plugin.name}: {plugin.get_status()}")

            return "\n".join(status)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error getting status information"

    def _handle_volume_command(self, args: List[str]) -> str:
        """Handle volume command."""
        try:
            if not args or "number" not in args:
                return "Please specify a volume level (0-100)"

            volume = float(args["number"])
            if not 0 <= volume <= 100:
                return "Volume must be between 0 and 100"

            if self.engine:
                self.engine.setProperty("volume", volume / 100)
                return f"Volume set to {volume}%"
            return "Error setting volume"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error setting volume"

    def _handle_language_command(self, args: List[str]) -> str:
        """Handle language command."""
        try:
            if not args or "location" not in args:
                return "Please specify a language code"

            language = args["location"]
            if self.recognizer:
                self.recognizer.language = language
                return f"Language set to {language}"
            return "Error setting language"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error setting language"

    def _handle_clear_command(self) -> str:
        """Handle clear command."""
        try:
            self.clear_context()
            return "Context cleared"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error clearing context"

    def _handle_exit_command(self) -> str:
        """Handle exit command."""
        try:
            self.stop_listening()
            return "Goodbye!"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error stopping voice assistant"

    def _handle_rate_command(self, number: float) -> str:
        """Handle rate command."""
        try:
            if not 0.5 <= number <= 2.0:
                return "Rate must be between 0.5 and 2.0"

            if self.engine:
                self.engine.setProperty("rate", 150 * number)
                return f"Speech rate set to {number}x"
            return "Error setting speech rate"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error setting speech rate"

    def _handle_pause_command(self) -> str:
        """Handle pause command."""
        try:
            if self.engine:
                self.engine.stop()
                return "Speech paused"
            return "Error pausing speech"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error pausing speech"

    def _handle_resume_command(self) -> str:
        """Handle resume command."""
        try:
            if self.engine:
                self.engine.runAndWait()
                return "Speech resumed"
            return "Error resuming speech"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error resuming speech"

    def _handle_stop_command(self) -> str:
        """Handle stop command."""
        try:
            if self.engine:
                self.engine.stop()
                return "Speech stopped"
            return "Error stopping speech"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error stopping speech"

    def _handle_list_voices_command(self) -> str:
        """Handle list voices command."""
        try:
            voices = self.get_available_voices()
            if not voices:
                return "No voices available"

            response = ["Available voices:"]
            for voice in voices:
                response.append(f"{voice['name']} ({voice['id']})")

            return "\n".join(response)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error listing voices"

    def _handle_context_command(self) -> str:
        """Handle context command."""
        try:
            if not self.context:
                return "No context items"

            response = ["Context items:"]
            for key, value in self.context.items():
                response.append(f"{key}: {value}")

            return "\n".join(response)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error getting context"

    def _handle_debug_command(self) -> str:
        """Handle debug command."""
        try:
            debug_info = [
                "Debug Information:",
                f"Python Version: {sys.version}",
                f"Platform: {sys.platform}",
                f"Voice Assistant Version: {self.version}",
                f"Plugins: {len(self.plugins)}",
                f"Commands: {len(self.command_handlers)}",
                f"Context: {len(self.context)} items",
                f"Error Count: {len(self.error_handler.get_summary())}",
            ]

            return "\n".join(debug_info)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error getting debug information"

    def _handle_save_command(self, args: List[str]) -> str:
        """Handle save command."""
        try:
            if not args or "location" not in args:
                return "Please specify a file path"

            file_path = args["location"]
            settings = {
                "version": self.version,
                "context": self.context,
                "plugins": {
                    name: plugin.get_info() for name, plugin in self.plugins.items()
                },
            }

            with open(file_path, "w") as f:
                json.dump(settings, f, indent=2)

            return f"Settings saved to {file_path}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error saving settings"

    def _handle_load_command(self, args: List[str]) -> str:
        """Handle load command."""
        try:
            if not args or "location" not in args:
                return "Please specify a file path"

            file_path = args["location"]
            with open(file_path, "r") as f:
                settings = json.load(f)

            # Update context
            self.context.update(settings.get("context", {}))

            # Update plugins
            for name, info in settings.get("plugins", {}).items():
                if name in self.plugins:
                    plugin = self.plugins[name]
                    if hasattr(plugin, "update_settings"):
                        plugin.update_settings(info)

            return f"Settings loaded from {file_path}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error loading settings"

    def _handle_reset_command(self, args: List[str]) -> str:
        """Handle reset command."""
        try:
            # Reset context
            self.clear_context()

            # Reset plugins
            for plugin in self.plugins.values():
                if hasattr(plugin, "reset"):
                    plugin.reset()

            return "Settings reset to defaults"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error resetting settings"

    def _handle_backup_command(self, args: List[str]) -> str:
        """Handle backup command."""
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.zip"

            with zipfile.ZipFile(backup_file, "w") as zipf:
                # Backup settings
                settings = {
                    "version": self.version,
                    "context": self.context,
                    "plugins": {
                        name: plugin.get_info() for name, plugin in self.plugins.items()
                    },
                }

                zipf.writestr("settings.json", json.dumps(settings, indent=2))

                # Backup plugin data
                for name, plugin in self.plugins.items():
                    if hasattr(plugin, "backup"):
                        plugin_data = plugin.backup()
                        if plugin_data:
                            zipf.writestr(
                                f"plugins/{name}.json",
                                json.dumps(plugin_data, indent=2),
                            )

            return f"Backup created at {backup_file}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error creating backup"

    def _handle_restore_command(self, args: List[str]) -> str:
        """Handle restore command."""
        try:
            if not args or "location" not in args:
                return "Please specify a backup file"

            backup_file = Path(args["location"])
            if not backup_file.exists():
                return f"Backup file not found: {backup_file}"

            with zipfile.ZipFile(backup_file, "r") as zipf:
                # Restore settings
                settings = json.loads(zipf.read("settings.json"))

                # Update context
                self.context.update(settings.get("context", {}))

                # Update plugins
                for name, info in settings.get("plugins", {}).items():
                    if name in self.plugins:
                        plugin = self.plugins[name]
                        if hasattr(plugin, "update_settings"):
                            plugin.update_settings(info)

                # Restore plugin data
                for name, plugin in self.plugins.items():
                    try:
                        plugin_data = json.loads(zipf.read(f"plugins/{name}.json"))
                        if hasattr(plugin, "restore"):
                            plugin.restore(plugin_data)
                    except KeyError:
                        continue

            return f"Backup restored from {backup_file}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error restoring backup"

    def _handle_update_command(self, args: List[str]) -> str:
        """Handle update command."""
        try:
            # Update plugins
            updated = []
            for plugin in self.plugins.values():
                if hasattr(plugin, "update"):
                    if plugin.update():
                        updated.append(plugin.name)

            if updated:
                return f"Updated plugins: {', '.join(updated)}"
            return "No updates available"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error updating system"

    def _handle_sync_command(self, args: List[str]) -> str:
        """Handle sync command."""
        try:
            # Sync plugins
            synced = []
            for plugin in self.plugins.values():
                if hasattr(plugin, "sync"):
                    if plugin.sync():
                        synced.append(plugin.name)

            if synced:
                return f"Synced plugins: {', '.join(synced)}"
            return "No sync needed"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error syncing system"

    def _handle_mute_command(self) -> str:
        """Handle mute command."""
        try:
            if self.engine:
                self.engine.setProperty("volume", 0)
                return "Voice muted"
            return "Error muting voice"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error muting voice"

    def _handle_unmute_command(self) -> str:
        """Handle unmute command."""
        try:
            if self.engine:
                self.engine.setProperty("volume", 0.9)
                return "Voice unmuted"
            return "Error unmuting voice"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error unmuting voice"

    def _handle_speed_command(self, number: float) -> str:
        """Handle speed command."""
        try:
            if not 0.5 <= number <= 2.0:
                return "Speed must be between 0.5 and 2.0"

            if self.engine:
                self.engine.setProperty("rate", 150 * number)
                return f"Speech speed set to {number}x"
            return "Error setting speech speed"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error setting speech speed"

    def _handle_pitch_command(self, number: float) -> str:
        """Handle pitch command."""
        try:
            if not 0.5 <= number <= 2.0:
                return "Pitch must be between 0.5 and 2.0"

            if self.engine:
                self.engine.setProperty("pitch", number)
                return f"Speech pitch set to {number}x"
            return "Error setting speech pitch"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error setting speech pitch"

    def _handle_export_command(self, args: List[str]) -> str:
        """Handle export command."""
        try:
            if not args or "location" not in args:
                return "Please specify a format (json/yaml/csv)"

            format = args["location"].lower()
            if format not in ["json", "yaml", "csv"]:
                return "Format must be json, yaml, or csv"

            # Create exports directory
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_settings_{timestamp}.{format}"
            file_path = export_dir / filename

            # Export settings
            settings = {
                "version": self.version,
                "context": self.context,
                "plugins": {
                    name: plugin.get_info() for name, plugin in self.plugins.items()
                },
            }

            if format == "json":
                with open(file_path, "w") as f:
                    json.dump(settings, f, indent=2)
            elif format == "yaml":
                with open(file_path, "w") as f:
                    yaml.dump(settings, f, default_flow_style=False)
            else:  # csv
                with open(file_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Key", "Value"])
                    for key, value in settings.items():
                        writer.writerow([key, json.dumps(value)])

            return f"Settings exported to {file_path}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error exporting settings"

    def _handle_import_command(self, args: List[str]) -> str:
        """Handle import command."""
        try:
            if not args or "location" not in args:
                return "Please specify a file path"

            file_path = Path(args["location"])
            if not file_path.exists():
                return f"File not found: {file_path}"

            # Import settings based on file extension
            format = file_path.suffix.lower()[1:]
            if format not in ["json", "yaml", "csv"]:
                return "Unsupported file format"

            if format == "json":
                with open(file_path, "r") as f:
                    settings = json.load(f)
            elif format == "yaml":
                with open(file_path, "r") as f:
                    settings = yaml.safe_load(f)
            else:  # csv
                settings = {}
                with open(file_path, "r", newline="") as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for key, value in reader:
                        settings[key] = json.loads(value)

            # Update context
            self.context.update(settings.get("context", {}))

            # Update plugins
            for name, info in settings.get("plugins", {}).items():
                if name in self.plugins:
                    plugin = self.plugins[name]
                    if hasattr(plugin, "update_settings"):
                        plugin.update_settings(info)

            return f"Settings imported from {file_path}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error importing settings"

    def _handle_config_command(self, args: List[str]) -> str:
        """Handle config command."""
        try:
            if not args:
                return "Please specify a setting and value"

            if len(args) == 1:
                # Get current value
                key = args[0]
                value = self.context.get(key)
                if value is not None:
                    return f"{key}: {value}"
                return f"Setting not found: {key}"

            # Set new value
            key = args[0]
            value = args[1]
            self.context[key] = value
            return f"Set {key} to {value}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error configuring settings"

    def _handle_plugins_command(self) -> str:
        """Handle plugins command."""
        try:
            if not self.plugins:
                return "No plugins installed"

            response = ["Installed plugins:"]
            for plugin in self.plugins.values():
                response.append(f"{plugin.name} v{plugin.version}")
                response.append(f"Description: {plugin.description}")
                response.append("Available commands:")
                response.extend(plugin.get_commands().split("\n"))
                response.append("")

            return "\n".join(response)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error listing plugins"

    def _handle_version_command(self) -> str:
        """Handle version command."""
        try:
            return f"Voice Assistant v{self.version}"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error getting version"

    def _handle_health_command(self) -> str:
        """Handle health command."""
        try:
            health = [
                "System Health:",
                f"Voice Assistant: {'OK' if self.engine and self.recognizer else 'ERROR'}",
                f"Speech Recognition: {'OK' if self.recognizer else 'ERROR'}",
                f"Text-to-Speech: {'OK' if self.engine else 'ERROR'}",
                f"Plugins: {len(self.plugins)}",
            ]

            # Check plugin health
            for plugin in self.plugins.values():
                if hasattr(plugin, "check_health"):
                    status = plugin.check_health()
                    health.append(f"{plugin.name}: {status}")

            return "\n".join(health)
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error checking system health"

    def _handle_system_command(self) -> str:
        """Handle system command."""
        try:
            # Implementation of the system command
            return "System command executed"
        except Exception as e:
            self.error_handler.handle_error(e, ErrorSeverity.ERROR)
            return "Error executing system command"
