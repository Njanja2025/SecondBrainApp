"""
Voice configuration settings for SecondBrain.
"""
from typing import Dict, Any

CONFIG: Dict[str, Any] = {
    "default_voice": "samantha",
    "voice_profiles": {
        "samantha": {
            "base_tone": "warm",
            "emotion_range": [
                "focused", "serious", "encouraging",
                "curious", "empathetic", "professional"
            ],
            "memory_persistence": True,
            "command_mode": True,
            "tone_modulation": {
                "warm": {"pitch": 1.05, "speed": 0.98},
                "focused": {"pitch": 1.0, "speed": 0.95},
                "encouraging": {"pitch": 1.1, "speed": 1.05}
            },
            "context_weights": {
                "time_of_day": 0.3,
                "user_emotion": 0.4,
                "conversation_history": 0.3
            },
            "adaptation_settings": {
                "learning_rate": 0.1,
                "feedback_threshold": 0.8,
                "memory_window": 100
            }
        }
    }
} 