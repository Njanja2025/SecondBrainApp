"""
Wake Word Listener for voice activation system.
"""
import logging
import speech_recognition as sr
from typing import Callable, Optional, List
import threading
import queue
import time

logger = logging.getLogger(__name__)

class WakeWordListener:
    """Listens for wake words to activate voice processing."""
    
    def __init__(self, 
                 wake_words: List[str] = None,
                 threshold: float = 0.5,
                 timeout: int = 5):
        """
        Initialize wake word listener.
        
        Args:
            wake_words: List of wake words to listen for
            threshold: Confidence threshold for wake word detection
            timeout: Listening timeout in seconds
        """
        self.wake_words = [word.lower() for word in (wake_words or ["samantha"])]
        self.threshold = threshold
        self.timeout = timeout
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.listen_thread = None
        
        self._calibrate_noise()
        
    def _calibrate_noise(self):
        """Calibrate for ambient noise."""
        try:
            with self.microphone as source:
                logger.info("Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                logger.info("Noise calibration complete")
                
        except Exception as e:
            logger.error(f"Failed to calibrate noise: {str(e)}")
            
    def start(self, callback: Callable):
        """
        Start listening for wake words.
        
        Args:
            callback: Function to call when wake word is detected
        """
        if self.is_listening:
            logger.warning("Already listening for wake words")
            return
            
        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._listen_loop,
            args=(callback,),
            daemon=True
        )
        self.listen_thread.start()
        logger.info("Wake word listener started")
        
    def stop(self):
        """Stop listening for wake words."""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=1.0)
        logger.info("Wake word listener stopped")
        
    def _listen_loop(self, callback: Callable):
        """
        Main listening loop.
        
        Args:
            callback: Function to call when wake word is detected
        """
        while self.is_listening:
            try:
                with self.microphone as source:
                    logger.debug("Listening for wake word...")
                    audio = self.recognizer.listen(
                        source,
                        timeout=self.timeout,
                        phrase_time_limit=5
                    )
                    
                    # Process audio in separate thread to avoid blocking
                    threading.Thread(
                        target=self._process_audio,
                        args=(audio, callback),
                        daemon=True
                    ).start()
                    
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in listening loop: {str(e)}")
                time.sleep(1)  # Prevent rapid error loops
                
    def _process_audio(self, audio: sr.AudioData, callback: Callable):
        """
        Process audio data and check for wake words.
        
        Args:
            audio: Audio data to process
            callback: Function to call if wake word is detected
        """
        try:
            # Try multiple recognition engines
            text = self._recognize_audio(audio)
            
            if text:
                text = text.lower()
                logger.debug(f"Recognized: {text}")
                
                # Check for wake words
                if any(word in text for word in self.wake_words):
                    logger.info(f"Wake word detected: {text}")
                    callback(text)
                    
        except Exception as e:
            logger.error(f"Failed to process audio: {str(e)}")
            
    def _recognize_audio(self, audio: sr.AudioData) -> Optional[str]:
        """
        Try multiple recognition engines to transcribe audio.
        
        Args:
            audio: Audio data to transcribe
            
        Returns:
            Transcribed text if successful, None otherwise
        """
        # Try Google Speech Recognition
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            logger.warning("Could not request results from Google Speech Recognition")
            
        # Try Sphinx (offline recognition)
        try:
            return self.recognizer.recognize_sphinx(audio)
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            logger.warning("Sphinx error; missing PocketSphinx?")
            
        return None
        
    def add_wake_word(self, word: str):
        """
        Add a new wake word.
        
        Args:
            word: Wake word to add
        """
        word = word.lower()
        if word not in self.wake_words:
            self.wake_words.append(word)
            logger.info(f"Added wake word: {word}")
            
    def remove_wake_word(self, word: str):
        """
        Remove a wake word.
        
        Args:
            word: Wake word to remove
        """
        word = word.lower()
        if word in self.wake_words:
            self.wake_words.remove(word)
            logger.info(f"Removed wake word: {word}")
            
    def get_wake_words(self) -> List[str]:
        """Get list of current wake words."""
        return self.wake_words.copy()
        
    def set_threshold(self, threshold: float):
        """
        Set confidence threshold for wake word detection.
        
        Args:
            threshold: New threshold value (0.0 to 1.0)
        """
        self.threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Set wake word threshold to {self.threshold}")
        
    def recalibrate(self):
        """Recalibrate noise levels."""
        self._calibrate_noise() 