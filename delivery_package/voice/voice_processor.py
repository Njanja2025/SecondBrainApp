import logging
from typing import Optional, Any, Dict, List, Callable
import asyncio
import re
from datetime import datetime
import whisper
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
import queue
import threading
from ..core.phantom_mcp import PhantomMCP

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, patterns: List[str], handler: Callable, description: str):
        self.patterns = [re.compile(pattern) for pattern in patterns]
        self.handler = handler
        self.description = description

class VoiceProcessor:
    def __init__(self):
        self.command_history = []
        self.response_history = []
        self.command_handlers = {}
        self.last_command_time = None
        self.command_cooldown = 1.0  # seconds
        self.phantom_mcp = PhantomMCP()
        self._initialize_handlers()
        
        # Initialize Whisper model
        self.whisper_model = None
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.listen_thread = None

    async def initialize(self):
        """Initialize voice processor with Whisper and Phantom MCP."""
        try:
            logger.info("Initializing voice processor...")
            
            # Initialize Phantom MCP
            await self.phantom_mcp.initialize()
            
            # Initialize Whisper model
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            
            # Initialize microphone
            self.microphone = sr.Microphone()
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source)
            
            # Optimize voice processing
            await self._optimize_voice_processing()
            
            # Start listening thread
            self.is_listening = True
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
            logger.info("Voice processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice processor: {str(e)}")
            raise

    def _listen_loop(self):
        """Continuous listening loop for voice input."""
        while self.is_listening:
            try:
                with self.microphone as source:
                    logger.debug("Listening for speech...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    self.audio_queue.put(audio)
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in listening loop: {str(e)}")
                continue

    async def process_audio(self):
        """Process audio from queue using Whisper."""
        try:
            while True:
                try:
                    audio = self.audio_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

                # Save audio to temporary file for Whisper
                with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as f:
                    f.write(audio.get_wav_data())
                    f.flush()
                    
                    # Use Whisper for transcription
                    result = self.whisper_model.transcribe(f.name)
                    text = result["text"].strip()
                    
                    if text:
                        logger.info(f"Transcribed: {text}")
                        await self.process_command(text, None)  # Replace None with agent reference

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")

    async def process_command(self, command_text: str, agent: Any) -> Dict[str, Any]:
        """Process a voice command with AI-backed analysis."""
        try:
            # Rate limiting and system health check
            current_time = datetime.now()
            if self.last_command_time and (current_time - self.last_command_time).total_seconds() < self.command_cooldown:
                return {"status": "error", "error": "Please wait before issuing another command"}
            
            # Get system status from Phantom MCP
            system_status = self.phantom_mcp.get_system_status()
            if system_status["system_health"] < 0.5:
                await self._optimize_voice_processing()
            
            self.last_command_time = current_time
            command_text = command_text.lower().strip()
            
            # Record command in history with system state
            self.command_history.append({
                "timestamp": current_time,
                "command": command_text,
                "system_state": system_status
            })

            # Input validation
            if not command_text:
                return await self._handle_empty_command()
            
            if len(command_text) > 500:
                return await self._handle_command_too_long()

            # AI-enhanced command matching
            for handler in self.handlers:
                for pattern in handler.patterns:
                    match = pattern.match(command_text)
                    if match:
                        logger.info(f"Matched command pattern: {pattern.pattern}")
                        return await handler.handler(command_text, agent, match.groups())

            return await self._handle_unknown_command(command_text)

        except Exception as e:
            error_msg = f"Error processing voice command: {str(e)}"
            logger.error(error_msg)
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def respond_with_voice(self, response_text: str):
        """Generate voice response using gTTS."""
        try:
            self.response_history.append({
                "timestamp": datetime.now(),
                "response": response_text
            })
            
            # Format response for logging
            formatted_response = f"🔊 {response_text}"
            logger.info(f"Voice Response: {response_text}")
            
            # Generate speech
            tts = gTTS(text=response_text, lang='en')
            with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as f:
                tts.save(f.name)
                os.system(f"afplay {f.name}")  # macOS audio playback
            
            return {"status": "success", "response": response_text}
            
        except Exception as e:
            logger.error(f"Failed to generate voice response: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _handle_empty_command(self) -> Dict[str, Any]:
        """Handle empty command input."""
        await self.respond_with_voice("Please provide a command. Say 'help' for available commands.")
        return {"status": "error", "error": "empty_command"}

    async def _handle_command_too_long(self) -> Dict[str, Any]:
        """Handle excessively long commands."""
        await self.respond_with_voice("Command is too long. Please be more concise.")
        return {"status": "error", "error": "command_too_long"}

    async def _handle_help(self, command_text: str, agent: Any, groups: tuple) -> Dict[str, Any]:
        """Handle help command."""
        help_text = "Available commands:\n"
        for handler in self.handlers:
            help_text += f"- {handler.description}\n"
        
        await self.respond_with_voice(help_text)
        return {"status": "success", "action": "help", "commands": help_text}

    async def _handle_contract_creation(self, command_text: str, agent: Any, groups: tuple) -> Dict[str, Any]:
        """Handle contract creation with enhanced validation."""
        try:
            contract_name = groups[0] if groups and groups[0] else "NjanjaToken"
            
            # Validate contract name
            if not re.match(r'^[a-zA-Z]\w*$', contract_name):
                raise ValueError("Invalid contract name. Use only letters, numbers, and underscores.")

            result = await agent.blockchain.generate_contract(contract_name)
            await self.respond_with_voice(f"Created contract {contract_name}")
            return {
                "status": "success", 
                "action": "create_contract", 
                "contract_name": contract_name,
                "result": result
            }

        except Exception as e:
            error_msg = f"Failed to create contract: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_contract_deployment(self, command_text: str, agent: Any) -> Dict[str, Any]:
        """Handle contract deployment commands."""
        try:
            # Extract contract path from command
            words = command_text.split()
            contract_path = None
            if "file" in words:
                path_index = words.index("file") + 1
                if path_index < len(words):
                    contract_path = words[path_index]
            
            if not contract_path:
                contract_path = "blockchain/contract_templates/NjanjaToken.sol"

            result = await agent.blockchain.deploy_contract(contract_path)
            await self.respond_with_voice(f"Deployed contract from {contract_path}")
            return {"status": "success", "action": "deploy_contract", "result": result}

        except Exception as e:
            error_msg = f"Failed to deploy contract: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_shutdown(self, agent: Any) -> Dict[str, Any]:
        """Handle agent shutdown command."""
        try:
            await self.respond_with_voice("Initiating shutdown sequence...")
            await agent.stop()
            return {"status": "success", "action": "shutdown"}
        except Exception as e:
            error_msg = f"Failed to shutdown: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_memory_query(self, command_text: str, agent: Any) -> Dict[str, Any]:
        """Handle memory-related commands."""
        try:
            if not hasattr(agent, 'memory'):
                raise AttributeError("Agent does not have memory capability")

            if "show" in command_text:
                memory_log = agent.memory.show_memory()
                await self.respond_with_voice("Here's what I remember:")
                print(memory_log)
                return {"status": "success", "action": "show_memory", "log": memory_log}

            elif "analyze" in command_text:
                analysis = agent.memory.analyze_performance()
                await self.respond_with_voice("Memory analysis complete")
                return {"status": "success", "action": "analyze_memory", "analysis": analysis}

        except Exception as e:
            error_msg = f"Failed to process memory command: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_status_query(self, agent: Any) -> Dict[str, Any]:
        """Handle status query commands."""
        try:
            status = {
                "blockchain_connected": hasattr(agent, 'blockchain') and agent.blockchain.network_manager.is_connected(),
                "memory_size": len(agent.memory.log) if hasattr(agent, 'memory') else 0,
                "command_history": len(self.command_history)
            }
            
            status_msg = f"Status: Connected to blockchain: {status['blockchain_connected']}, "
            status_msg += f"Memory entries: {status['memory_size']}, "
            status_msg += f"Commands processed: {status['command_history']}"
            
            await self.respond_with_voice(status_msg)
            return {"status": "success", "action": "status_query", "details": status}

        except Exception as e:
            error_msg = f"Failed to get status: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_unknown_command(self, command_text: str) -> Dict[str, Any]:
        """Handle unknown commands."""
        response = f"Sorry, I didn't understand the command: {command_text}"
        await self.respond_with_voice(response)
        return {"status": "error", "error": "unknown_command", "command": command_text}

    def get_command_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Return the history of processed commands with optional limit."""
        history = sorted(self.command_history, key=lambda x: x["timestamp"], reverse=True)
        return history[:limit] if limit else history

    def get_response_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Return the history of voice responses with optional limit."""
        history = sorted(self.response_history, key=lambda x: x["timestamp"], reverse=True)
        return history[:limit] if limit else history

    def clear_history(self, older_than: Optional[datetime] = None):
        """Clear command and response history, optionally only entries older than specified date."""
        if older_than:
            self.command_history = [
                cmd for cmd in self.command_history 
                if cmd["timestamp"] > older_than
            ]
            self.response_history = [
                resp for resp in self.response_history 
                if resp["timestamp"] > older_than
            ]
        else:
            self.command_history = []
            self.response_history = []

    # New AI-backed command handlers

    async def _handle_system_optimization(self, command_text: str, agent: Any, groups: tuple) -> Dict[str, Any]:
        """Handle system optimization using Phantom MCP."""
        try:
            await self.respond_with_voice("Initiating system optimization...")
            
            # Perform system-wide optimization
            memory_result = await self.phantom_mcp.improve_system("memory_optimization")
            process_result = await self.phantom_mcp.improve_system("process_optimization")
            learning_result = await self.phantom_mcp.improve_system("learning_optimization")
            
            # Get updated system status
            status = self.phantom_mcp.get_system_status()
            
            response = f"System optimization complete. Health: {status['system_health']*100:.1f}%"
            await self.respond_with_voice(response)
            
            return {
                "status": "success",
                "action": "system_optimization",
                "results": {
                    "memory": memory_result,
                    "process": process_result,
                    "learning": learning_result
                }
            }
        except Exception as e:
            error_msg = f"Failed to optimize system: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_pattern_analysis(self, command_text: str, agent: Any, groups: tuple) -> Dict[str, Any]:
        """Handle pattern analysis and insights."""
        try:
            status = self.phantom_mcp.get_system_status()
            evolution = self.phantom_mcp.evolution_history[-5:]  # Get last 5 improvements
            
            insights = f"System Health: {status['system_health']*100:.1f}%\n"
            insights += f"Active Processes: {len(status['active_processes'])}\n"
            insights += f"Memory Usage: {status['memory_usage']*100:.1f}%\n"
            insights += "\nRecent Improvements:\n"
            
            for improvement in evolution:
                insights += f"- {improvement['area']}: {improvement['pattern']}\n"
            
            await self.respond_with_voice(insights)
            return {
                "status": "success",
                "action": "pattern_analysis",
                "insights": insights
            }
        except Exception as e:
            error_msg = f"Failed to analyze patterns: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_backup_creation(self, command_text: str, agent: Any, groups: tuple) -> Dict[str, Any]:
        """Handle system backup creation."""
        try:
            result = await self.phantom_mcp.create_backup()
            if result["status"] == "success":
                await self.respond_with_voice(f"Backup created successfully. ID: {result['backup_id']}")
            else:
                await self.respond_with_voice(f"Failed to create backup: {result['message']}")
            return result
        except Exception as e:
            error_msg = f"Failed to create backup: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _handle_backup_restore(self, command_text: str, agent: Any, groups: tuple) -> Dict[str, Any]:
        """Handle system backup restoration."""
        try:
            backup_id = groups[0]
            result = await self.phantom_mcp.restore_from_backup(backup_id)
            if result["status"] == "success":
                await self.respond_with_voice(f"System restored from backup {backup_id}")
            else:
                await self.respond_with_voice(f"Failed to restore backup: {result['message']}")
            return result
        except Exception as e:
            error_msg = f"Failed to restore backup: {str(e)}"
            await self.respond_with_voice(error_msg)
            return {"status": "error", "error": error_msg}

    async def _optimize_voice_processing(self):
        """Optimize voice processing using Phantom MCP."""
        try:
            # Apply memory optimization for voice processing
            await self.phantom_mcp.improve_system("memory_optimization")
            
            # Apply process optimization for command handling
            await self.phantom_mcp.improve_system("process_optimization")
            
            # Apply learning optimization for pattern recognition
            await self.phantom_mcp.improve_system("learning_optimization")
            
        except Exception as e:
            logger.error(f"Failed to optimize voice processing: {str(e)}")

    async def stop(self):
        """Stop voice processing gracefully."""
        try:
            logger.info("Stopping voice processor...")
            self.is_listening = False
            
            if self.listen_thread:
                self.listen_thread.join(timeout=1.0)
            
            # Create backup before shutdown
            await self.phantom_mcp.create_backup("voice_shutdown")
            
            logger.info("Voice processor stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping voice processor: {str(e)}")
            raise 