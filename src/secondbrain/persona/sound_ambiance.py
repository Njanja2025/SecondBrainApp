"""
Sound Ambiance System for Samantha's emotional expression through audio.
"""
import logging
import threading
import pygame
import os
from pathlib import Path
from typing import Optional, Dict
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class SoundAmbiance:
    """Manages background ambient sounds based on emotional state."""
    
    def __init__(self):
        self.current_track = None
        self.volume = 0.3
        self.is_playing = False
        self._setup_audio()
        
        # Sound mappings
        self.ambiance_map = {
            "calm": "calm_ambient.wav",
            "excited": "excited_theme.wav",
            "attentive": "focus_loop.wav",
            "thoughtful": "deep_thinking.wav",
            "neutral": "soft_idle.wav"
        }
        
        # Volume levels for different times of day
        self.time_volumes = {
            "morning": 0.4,    # 6-12
            "afternoon": 0.3,  # 12-18
            "evening": 0.2,    # 18-22
            "night": 0.1      # 22-6
        }
        
        # Ensure sounds directory exists
        self.sounds_dir = Path("assets/sounds")
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Track history
        self.playback_history = []
        
    def _setup_audio(self):
        """Initialize audio system."""
        try:
            pygame.mixer.init()
            logger.info("Audio system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            
    def _get_time_adjusted_volume(self) -> float:
        """Get volume adjusted for time of day."""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            return self.time_volumes["morning"]
        elif 12 <= hour < 18:
            return self.time_volumes["afternoon"]
        elif 18 <= hour < 22:
            return self.time_volumes["evening"]
        else:
            return self.time_volumes["night"]
            
    def play_ambiance(self, tone: str):
        """
        Play ambient sound matching the emotional tone.
        
        Args:
            tone: Emotional tone to match
        """
        try:
            # Get sound file
            sound_file = self.ambiance_map.get(tone, "soft_idle.wav")
            sound_path = self.sounds_dir / sound_file
            
            # Check if sound exists
            if not sound_path.exists():
                logger.warning(f"Sound file not found: {sound_path}")
                return
                
            # Stop current playback
            self.stop_ambiance()
            
            def loop_sound():
                try:
                    pygame.mixer.music.load(str(sound_path))
                    # Adjust volume based on time of day
                    volume = self._get_time_adjusted_volume()
                    pygame.mixer.music.set_volume(volume)
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    self.is_playing = True
                    self.current_track = sound_file
                    
                    # Log playback
                    self.playback_history.append({
                        "tone": tone,
                        "track": sound_file,
                        "volume": volume,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error in sound playback: {e}")
                    self.is_playing = False
                    
            # Start playback in separate thread
            threading.Thread(target=loop_sound, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to play ambiance: {e}")
            
    def stop_ambiance(self):
        """Stop current ambient sound."""
        try:
            if self.is_playing:
                pygame.mixer.music.stop()
                self.is_playing = False
                self.current_track = None
        except Exception as e:
            logger.error(f"Failed to stop ambiance: {e}")
            
    def set_volume(self, volume: float):
        """
        Set playback volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        try:
            self.volume = max(0.0, min(1.0, volume))
            if self.is_playing:
                pygame.mixer.music.set_volume(self.volume)
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            
    def fade_out(self, duration: float = 1.0):
        """
        Gradually fade out current sound.
        
        Args:
            duration: Fade duration in seconds
        """
        try:
            if self.is_playing:
                pygame.mixer.music.fadeout(int(duration * 1000))
                self.is_playing = False
                self.current_track = None
        except Exception as e:
            logger.error(f"Failed to fade out: {e}")
            
    def get_playback_analytics(self) -> Dict:
        """Get analytics about sound playback patterns."""
        try:
            if not self.playback_history:
                return {}
                
            # Analyze recent history
            recent = self.playback_history[-100:]  # Last 100 entries
            
            # Count tone frequencies
            tone_counts = {}
            for entry in recent:
                tone = entry["tone"]
                tone_counts[tone] = tone_counts.get(tone, 0) + 1
                
            # Calculate average volume
            avg_volume = sum(entry["volume"] for entry in recent) / len(recent)
            
            return {
                "current_track": self.current_track,
                "is_playing": self.is_playing,
                "tone_distribution": tone_counts,
                "average_volume": avg_volume,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get playback analytics: {e}")
            return {} 