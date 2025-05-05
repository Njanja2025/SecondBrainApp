import logging
import asyncio
import speech_recognition as sr
from typing import Callable, Optional
import queue
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Handles voice input processing for SecondBrain."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    def __init__(self):
        self._running = False
        self.on_speech: Optional[Callable[[str], None]] = None
        self._recognizer = sr.Recognizer()
        self._mic = None
        self._audio_queue = queue.Queue()
        self._thread = None
        self._error_count = 0
        self.load_settings()
        
    def load_settings(self):
        """Load voice processor settings."""
        self.settings = {
            "energy_threshold": 4000,
            "dynamic_energy_threshold": True,
            "pause_threshold": 0.8,
            "phrase_threshold": 0.3,
            "non_speaking_duration": 0.5
        }
        
        try:
            settings_path = Path("voice_processor_settings.json")
            if settings_path.exists():
                import json
                self.settings.update(json.loads(settings_path.read_text()))
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
        
    def configure_recognizer(self):
        """Configure the speech recognizer with current settings."""
        self._recognizer.energy_threshold = self.settings["energy_threshold"]
        self._recognizer.dynamic_energy_threshold = self.settings["dynamic_energy_threshold"]
        self._recognizer.pause_threshold = self.settings["pause_threshold"]
        self._recognizer.phrase_threshold = self.settings["phrase_threshold"]
        self._recognizer.non_speaking_duration = self.settings["non_speaking_duration"]
        
    async def initialize(self):
        """Initialize voice processing components with retry logic."""
        logger.info("Initializing voice processor...")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Initialize microphone
                self._mic = sr.Microphone()
                with self._mic as source:
                    logger.info("Adjusting for ambient noise...")
                    self._recognizer.adjust_for_ambient_noise(source)
                
                # Configure recognizer
                self.configure_recognizer()
                
                logger.info("Voice processor initialized successfully")
                self._error_count = 0  # Reset error count on successful init
                return
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    raise RuntimeError("Failed to initialize voice processor after multiple attempts")
        
    async def start(self):
        """Start voice processing with health monitoring."""
        logger.info("Starting voice processor...")
        self._running = True
        
        # Start background thread for audio capture
        self._thread = threading.Thread(target=self._capture_audio, daemon=True)
        self._thread.start()
        
        # Start processing task and health monitor
        asyncio.create_task(self._process_audio_stream())
        asyncio.create_task(self._monitor_health())
        
    async def shutdown(self):
        """Shutdown voice processing cleanly."""
        logger.info("Shutting down voice processor...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            
    async def _monitor_health(self):
        """Monitor voice processor health and attempt recovery."""
        while self._running:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            if self._error_count > self.MAX_RETRIES:
                logger.warning("Too many errors, attempting recovery...")
                try:
                    # Reinitialize components
                    self._mic = sr.Microphone()
                    with self._mic as source:
                        self._recognizer.adjust_for_ambient_noise(source)
                    self.configure_recognizer()
                    self._error_count = 0
                    logger.info("Recovery successful")
                except Exception as e:
                    logger.error(f"Recovery failed: {e}")
        
    def _capture_audio(self):
        """Capture audio in a background thread with error handling."""
        logger.info("Starting audio capture thread")
        consecutive_errors = 0
        
        while self._running:
            try:
                with self._mic as source:
                    audio = self._recognizer.listen(
                        source,
                        timeout=1,
                        phrase_time_limit=10
                    )
                    self._audio_queue.put(audio)
                    consecutive_errors = 0  # Reset on success
                    
            except sr.WaitTimeoutError:
                continue  # No speech detected, continue listening
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error capturing audio: {e}")
                
                if consecutive_errors >= 3:
                    logger.warning("Multiple consecutive capture errors, waiting before retry...")
                    time.sleep(2)  # Wait before retrying
                    consecutive_errors = 0
                
    async def _process_audio_stream(self):
        """Process the audio stream for speech recognition with error handling."""
        logger.info("Started audio stream processing")
        while self._running:
            try:
                # Check for audio data
                try:
                    audio = self._audio_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                
                # Convert speech to text with multiple API attempts
                for attempt in range(self.MAX_RETRIES):
                    try:
                        text = self._recognizer.recognize_google(audio)
                        logger.info(f"Recognized speech: {text}")
                        self._error_count = 0  # Reset error count on success
                        
                        # Handle the recognized speech
                        if self.on_speech:
                            asyncio.create_task(self.on_speech(text))
                        break
                        
                    except sr.UnknownValueError:
                        logger.debug("Speech was unintelligible")
                        break  # Don't retry on unintelligible speech
                        
                    except sr.RequestError as e:
                        logger.error(f"API request error (attempt {attempt + 1}): {e}")
                        if attempt < self.MAX_RETRIES - 1:
                            await asyncio.sleep(self.RETRY_DELAY)
                        else:
                            self._error_count += 1
                            
            except Exception as e:
                logger.error(f"Error processing audio stream: {e}")
                self._error_count += 1
                await asyncio.sleep(1)  # Prevent tight error loop 