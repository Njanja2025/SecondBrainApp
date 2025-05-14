"""
Emotion Voice Adapter for dynamic voice modulation based on emotional states.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmotionVoiceAdapter:
    """Adapts voice characteristics based on emotional states."""

    def __init__(self, voice_engine):
        self.voice_engine = voice_engine
        self._init_emotion_profiles()

    def _init_emotion_profiles(self):
        """Initialize default emotion profiles with voice characteristics."""
        self.emotion_profiles = {
            "sad": {"rate": 150, "volume": 0.7, "pitch": 0.8},
            "angry": {"rate": 220, "volume": 0.9, "pitch": 1.2},
            "calm": {"rate": 180, "volume": 0.8, "pitch": 1.0},
            "happy": {"rate": 200, "volume": 0.85, "pitch": 1.1},
            "excited": {"rate": 210, "volume": 0.9, "pitch": 1.15},
            "thoughtful": {"rate": 170, "volume": 0.75, "pitch": 0.95},
        }

    def adjust_voice(self, emotion: str, intensity: float = 1.0) -> None:
        """
        Adjust voice characteristics based on emotion and intensity.

        Args:
            emotion: The emotional state to adapt to
            intensity: Intensity of the emotion (0.0 to 1.0)
        """
        try:
            # Get emotion profile or default to neutral
            profile = self.emotion_profiles.get(
                emotion.lower(), {"rate": 200, "volume": 0.8, "pitch": 1.0}
            )

            # Apply intensity modulation
            rate = self._modulate_parameter(profile["rate"], intensity)
            volume = self._modulate_parameter(profile["volume"], intensity)
            pitch = self._modulate_parameter(profile["pitch"], intensity)

            # Set voice properties
            self.voice_engine.engine.setProperty("rate", rate)
            self.voice_engine.engine.setProperty("volume", volume)

            # Some engines might not support pitch modification
            try:
                self.voice_engine.engine.setProperty("pitch", pitch)
            except Exception as e:
                logger.warning(f"Pitch modification not supported: {str(e)}")

            logger.debug(
                f"Adjusted voice for emotion '{emotion}' with intensity {intensity}"
            )

        except Exception as e:
            logger.error(f"Failed to adjust voice: {str(e)}")
            # Fallback to default settings
            self._set_default_voice()

    def _modulate_parameter(self, base_value: float, intensity: float) -> float:
        """
        Modulate a voice parameter based on emotion intensity.

        Args:
            base_value: The base parameter value
            intensity: Emotion intensity (0.0 to 1.0)

        Returns:
            Modulated parameter value
        """
        # Ensure intensity is within bounds
        intensity = max(0.0, min(1.0, intensity))

        # Calculate modulation factor
        mod_factor = 0.5 + (intensity * 0.5)

        # Apply modulation
        return base_value * mod_factor

    def _set_default_voice(self) -> None:
        """Reset voice to default settings."""
        try:
            self.voice_engine.engine.setProperty("rate", 200)
            self.voice_engine.engine.setProperty("volume", 0.8)
            self.voice_engine.engine.setProperty("pitch", 1.0)
        except Exception as e:
            logger.error(f"Failed to set default voice: {str(e)}")

    def add_emotion_profile(self, emotion: str, profile: Dict[str, float]) -> None:
        """
        Add or update an emotion profile.

        Args:
            emotion: Name of the emotion
            profile: Dictionary containing rate, volume, and pitch values
        """
        required_keys = {"rate", "volume", "pitch"}
        if not all(key in profile for key in required_keys):
            raise ValueError(f"Profile must contain all required keys: {required_keys}")

        self.emotion_profiles[emotion.lower()] = profile
        logger.info(f"Added/updated profile for emotion: {emotion}")

    def get_current_profile(self) -> Dict[str, float]:
        """Get current voice profile settings."""
        return {
            "rate": self.voice_engine.engine.getProperty("rate"),
            "volume": self.voice_engine.engine.getProperty("volume"),
            "pitch": self.voice_engine.engine.getProperty("pitch"),
        }
