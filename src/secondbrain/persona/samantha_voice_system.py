"""
Samantha Voice System Module - Adaptive Persona Core with Emotional Voice and Analytics.
"""

import logging
import json
import os
from typing import Dict, Any, Optional, Set, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
import re
import pyttsx3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from .mood_meter import MoodMeter
from .sound_ambiance import SoundAmbiance
from .theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class SamanthaVoiceSystem:
    def __init__(self):
        self.active_modules: Set[str] = set()
        self.persona_traits = {
            "foresight": "disabled",
            "adaptability": "high",
            "learning_rate": 0.85,
            "empathy": "enabled",
            "curiosity": "high",
        }
        self.quantum_ready = False
        self.voice_enabled = True
        self.last_announcement = None
        self.announcement_history: List[Dict[str, Any]] = []
        self.announcement_file = "samantha_announcements.json"

        # Enhanced emotional and tone responses
        self.current_tone = "neutral"
        self.tone_patterns = {
            "calm": {
                "triggers": {
                    "error",
                    "issue",
                    "problem",
                    "crash",
                    "warning",
                    "risk",
                    "concern",
                },
                "prefixes": [
                    "Let me calmly explain: ",
                    "Here's what we know so far: ",
                    "Let's approach this systematically: ",
                ],
            },
            "excited": {
                "triggers": {
                    "success",
                    "breakthrough",
                    "achievement",
                    "discovery",
                    "innovation",
                    "update",
                },
                "prefixes": [
                    "I'm excited to share: ",
                    "Great news! ",
                    "Fascinating development: ",
                ],
            },
            "attentive": {
                "triggers": {
                    "user",
                    "feedback",
                    "question",
                    "request",
                    "help",
                    "support",
                },
                "prefixes": [
                    "I'm listening carefully: ",
                    "Let me address that: ",
                    "Here's what I understand: ",
                ],
            },
            "assertive": {
                "triggers": {
                    "urgent",
                    "critical",
                    "important",
                    "security",
                    "immediate",
                    "action",
                },
                "prefixes": [
                    "This requires immediate attention: ",
                    "Important update: ",
                    "Critical information: ",
                ],
            },
            "curious": {
                "triggers": {
                    "research",
                    "experiment",
                    "study",
                    "investigation",
                    "analysis",
                },
                "prefixes": [
                    "This is intriguing: ",
                    "Let's explore this: ",
                    "Here's an interesting finding: ",
                ],
            },
            "empathetic": {
                "triggers": {"challenge", "difficulty", "struggle", "concern", "worry"},
                "prefixes": [
                    "I understand this might be concerning: ",
                    "Let's work through this together: ",
                    "I hear your concern: ",
                ],
            },
            "neutral": {
                "triggers": set(),
                "prefixes": ["", "Here's an update: ", "Let me share: "],
            },
        }

        # Tone transition rules
        self.tone_transitions = {
            "excited": ["curious", "neutral", "attentive"],  # Gradual cool-down
            "assertive": ["calm", "neutral"],  # De-escalation
            "empathetic": ["attentive", "calm"],  # Maintain support
            "calm": ["neutral", "attentive"],  # Gradual re-engagement
            "curious": ["attentive", "neutral"],  # Maintain engagement
            "attentive": ["neutral", "empathetic"],  # Response based
            "neutral": ["attentive", "curious", "calm"],  # Base state
        }

        # Tone history for smooth transitions
        self.tone_history: List[str] = ["neutral"]
        self.max_tone_history = 5

        self.emotional_responses = {
            "positive": [
                "I'm excited to share this development.",
                "This is a promising advancement.",
                "I'm optimistic about these findings.",
            ],
            "negative": [
                "I should note some concerns about this development.",
                "We should carefully consider the implications.",
                "This requires careful attention and analysis.",
            ],
            "neutral": [
                "Let me share my analysis.",
                "I've detected something noteworthy.",
                "Here's what I've discovered.",
            ],
        }

        # Analytics attributes
        self.announcement_memory: List[Dict[str, Any]] = []
        self.voice_metrics = {
            "total_announcements": 0,
            "tone_distribution": defaultdict(int),
            "topic_focus": defaultdict(int),
            "sentiment_balance": {"positive": 0, "negative": 0, "neutral": 0},
            "tone_transitions": defaultdict(int),
            "emotional_transitions": [],
            "intensity_history": [],
            "voice_profile_usage": defaultdict(int),
            "effectiveness_scores": defaultdict(float),
        }
        self.bias_thresholds = {
            "term_dominance": 0.2,
            "tone_imbalance": 0.4,
            "sentiment_skew": 0.6,
        }
        self._load_announcement_history()

        # Voice emotion profiles
        self.voice_profiles = {
            "calm": {
                "rate": 130,
                "volume": 0.7,
                "pitch": 0.9,
                "inflection": "smooth",
                "intensity": 0.4,
                "pause_factor": 1.2,
            },
            "excited": {
                "rate": 180,
                "volume": 1.0,
                "pitch": 1.2,
                "inflection": "varied",
                "intensity": 0.8,
                "pause_factor": 0.8,
            },
            "attentive": {
                "rate": 150,
                "volume": 0.85,
                "pitch": 1.0,
                "inflection": "focused",
                "intensity": 0.6,
                "pause_factor": 1.0,
            },
            "assertive": {
                "rate": 165,
                "volume": 0.95,
                "pitch": 1.1,
                "inflection": "strong",
                "intensity": 0.7,
                "pause_factor": 0.9,
            },
            "curious": {
                "rate": 155,
                "volume": 0.8,
                "pitch": 1.05,
                "inflection": "rising",
                "intensity": 0.5,
                "pause_factor": 1.1,
            },
            "empathetic": {
                "rate": 140,
                "volume": 0.75,
                "pitch": 0.95,
                "inflection": "gentle",
                "intensity": 0.45,
                "pause_factor": 1.3,
            },
            "neutral": {
                "rate": 160,
                "volume": 0.9,
                "pitch": 1.0,
                "inflection": "balanced",
                "intensity": 0.5,
                "pause_factor": 1.0,
            },
        }

        # Voice engine setup
        self.voice_engine = None
        self.thread_pool = ThreadPoolExecutor(max_workers=1)
        self._setup_voice_engine()

        # Emotional intensity tracking
        self.emotional_intensity = {
            "current": 0.5,  # 0.0 to 1.0
            "target": 0.5,
            "transition_rate": 0.1,
        }

        # Enhanced emotional logging
        self.emotional_log: List[Dict[str, Any]] = []
        self.log_directory = Path("logs/samantha/emotional")
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Avatar sync preparation
        self.avatar_states = {
            "calm": {
                "expression": "serene",
                "eye_state": "soft",
                "mouth_curve": 0.2,  # slight smile
            },
            "excited": {
                "expression": "energetic",
                "eye_state": "wide",
                "mouth_curve": 0.8,  # big smile
            },
            "attentive": {
                "expression": "focused",
                "eye_state": "alert",
                "mouth_curve": 0.3,
            },
            "assertive": {
                "expression": "confident",
                "eye_state": "direct",
                "mouth_curve": 0.4,
            },
            "curious": {
                "expression": "interested",
                "eye_state": "inquiring",
                "mouth_curve": 0.5,
            },
            "empathetic": {
                "expression": "caring",
                "eye_state": "gentle",
                "mouth_curve": 0.3,
            },
            "neutral": {
                "expression": "balanced",
                "eye_state": "natural",
                "mouth_curve": 0.0,
            },
        }

        # Analytics enhancements
        self.voice_analytics = {
            "daily_tone_distribution": defaultdict(lambda: defaultdict(int)),
            "hourly_patterns": defaultdict(lambda: defaultdict(int)),
            "transition_effectiveness": defaultdict(list),
            "user_engagement_scores": defaultdict(float),
            "voice_quality_metrics": [],
        }

        # Voice quality monitoring
        self.voice_quality_thresholds = {
            "volume_variance": 0.2,
            "rate_stability": 0.15,
            "tone_consistency": 0.8,
        }

        # Initialize avatar manager
        self.avatar_manager = None
        self.mood_meter = None
        self.sound_ambiance = None
        self.theme_manager = None
        self.current_intensity = 0.5

    def _setup_voice_engine(self) -> None:
        """Initialize and configure the voice engine."""
        try:
            self.voice_engine = pyttsx3.init()
            # Try to set a female voice if available
            voices = self.voice_engine.getProperty("voices")
            female_voice = next(
                (voice for voice in voices if "female" in voice.name.lower()), None
            )
            if female_voice:
                self.voice_engine.setProperty("voice", female_voice.id)
        except Exception as e:
            logger.error(f"Error setting up voice engine: {e}")
            self.voice_enabled = False

    async def initialize(self, root: Optional[tk.Tk] = None):
        """Initialize voice system, avatar, mood meter, sound, and theme."""
        # ... existing code ...

        # Initialize components if GUI root is provided
        if root:
            self.avatar_manager = AvatarManager(root)
            self.mood_meter = MoodMeter(root)
            self.theme_manager = ThemeManager(root)

        # Initialize sound ambiance
        self.sound_ambiance = SoundAmbiance()

        # ... existing code ...

    async def speak_with_emotion(
        self, message: str, tone: Optional[str] = None
    ) -> None:
        """
        Speak message with emotional expression and synchronized ambiance.

        Args:
            message: The message to speak
            tone: Optional specific tone to use (defaults to current_tone)
        """
        try:
            # Determine tone and intensity
            tone = tone or self.current_tone
            intensity = self._calculate_intensity(message)

            # Update mood meter
            if self.mood_meter:
                self.current_tone = self.mood_meter.update_mood(tone, intensity)
                self.current_intensity = self.mood_meter.mood_intensity

            # Synchronize components
            await self._sync_emotional_components(tone, intensity)

            # Speak the message
            await self._speak(message)

            # Log emotion
            self._log_emotion(tone, intensity, message)

        except Exception as e:
            logger.error(f"Failed to speak with emotion: {e}")

    async def _sync_emotional_components(self, tone: str, intensity: float):
        """
        Synchronize all emotional expression components.

        Args:
            tone: Emotional tone
            intensity: Emotional intensity
        """
        try:
            # Create tasks for parallel execution
            tasks = []

            # Update avatar expression
            if self.avatar_manager:
                tasks.append(
                    self.avatar_manager.animate_expression_change(
                        self.current_tone, tone, duration=0.3
                    )
                )

                # Start speaking animation
                tasks.append(
                    self.avatar_manager.animate_speaking(
                        duration=0.5  # Will be adjusted in speak method
                    )
                )

            # Update theme
            if self.theme_manager:
                tasks.append(self.theme_manager.sync_theme(tone))

            # Update sound ambiance
            if self.sound_ambiance:
                # Fade out current ambiance
                self.sound_ambiance.fade_out(0.3)
                # Start new ambiance
                self.sound_ambiance.play_ambiance(tone)

            # Wait for all animations to complete
            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"Failed to sync emotional components: {e}")

    def get_emotional_analytics(self) -> Dict:
        """Get comprehensive analytics about emotional expression."""
        try:
            analytics = {
                "timestamp": datetime.now().isoformat(),
                "current_state": {
                    "tone": self.current_tone,
                    "intensity": getattr(self, "current_intensity", 0.5),
                },
            }

            # Get component-specific analytics
            if self.mood_meter:
                analytics["mood"] = self.mood_meter.get_mood_analytics()

            if self.sound_ambiance:
                analytics["sound"] = self.sound_ambiance.get_playback_analytics()

            if self.theme_manager:
                analytics["theme"] = self.theme_manager.get_theme_analytics()

            if self.avatar_manager:
                analytics["avatar"] = {
                    "current_expression": self.avatar_manager.current_expression,
                    "is_speaking": self.avatar_manager.is_speaking,
                }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get emotional analytics: {e}")
            return {}

    def _calculate_intensity(self, message: str) -> float:
        """Calculate emotional intensity from message content."""
        try:
            # Simple intensity calculation based on punctuation and keywords
            intensity = 0.5  # Default neutral intensity

            # Increase for exclamation marks
            intensity += message.count("!") * 0.1

            # Increase for emotional keywords
            emotional_keywords = {
                "excited": 0.2,
                "happy": 0.15,
                "amazing": 0.2,
                "wonderful": 0.15,
                "sad": -0.15,
                "angry": -0.2,
                "frustrated": -0.15,
            }

            for keyword, value in emotional_keywords.items():
                if keyword in message.lower():
                    intensity += abs(value)

            # Clamp between 0 and 1
            return max(0.0, min(1.0, intensity))

        except Exception as e:
            logger.error(f"Failed to calculate intensity: {e}")
            return 0.5

    def _log_emotion(self, tone: str, intensity: float, message: str):
        """Log emotional state for analysis."""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "tone": tone,
                "intensity": intensity,
                "message": message,
                "mood": self.current_tone,
            }

            # Save to emotional log file
            if self.mood_meter:
                self.mood_meter.save_emotional_log()

        except Exception as e:
            logger.error(f"Failed to log emotion: {e}")

    def get_mood_analytics(self) -> Dict:
        """Get current mood analytics."""
        try:
            if self.mood_meter:
                return self.mood_meter.get_mood_analytics()
            return {}

        except Exception as e:
            logger.error(f"Failed to get mood analytics: {e}")
            return {}

    def _prepare_voice_output(self, profile: Dict[str, Any]) -> Dict[str, float]:
        """Prepare voice output and measure quality metrics."""
        try:
            # Configure voice properties
            self.voice_engine.setProperty("rate", profile["rate"])
            self.voice_engine.setProperty("volume", profile["volume"])

            # Measure voice quality metrics
            metrics = {
                "volume_stability": self._measure_volume_stability(),
                "rate_consistency": self._measure_rate_consistency(),
                "tone_quality": self._measure_tone_quality(),
            }

            # Store quality metrics
            self.voice_quality_metrics.append(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error preparing voice output: {e}")
            return {}

    def _measure_volume_stability(self) -> float:
        """Measure volume stability metric."""
        try:
            current_volume = self.voice_engine.getProperty("volume")
            threshold = self.voice_quality_thresholds["volume_variance"]
            return min(
                1.0,
                max(
                    0.0,
                    1.0
                    - abs(
                        current_volume
                        - self.voice_profiles[self.current_tone]["volume"]
                    )
                    / threshold,
                ),
            )
        except:
            return 0.8  # Default if measurement fails

    def _measure_rate_consistency(self) -> float:
        """Measure speech rate consistency."""
        try:
            current_rate = self.voice_engine.getProperty("rate")
            threshold = self.voice_quality_thresholds["rate_stability"]
            return min(
                1.0,
                max(
                    0.0,
                    1.0
                    - abs(current_rate - self.voice_profiles[self.current_tone]["rate"])
                    / (threshold * 100),
                ),
            )
        except:
            return 0.8  # Default if measurement fails

    def _measure_tone_quality(self) -> float:
        """Measure overall tone quality."""
        try:
            # Combine various metrics for overall quality
            metrics = [
                self._measure_volume_stability(),
                self._measure_rate_consistency(),
            ]
            return sum(metrics) / len(metrics)
        except:
            return 0.8  # Default if measurement fails

    def _create_log_entry(
        self,
        message: str,
        tone: str,
        profile: Dict[str, Any],
        voice_metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """Create detailed log entry for emotional response."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "tone": tone,
            "message": message,
            "profile_used": {
                k: v
                for k, v in profile.items()
                if k in ["rate", "volume", "intensity", "inflection"]
            },
            "voice_metrics": voice_metrics,
            "context": {
                "previous_tone": (
                    self.tone_history[-2] if len(self.tone_history) > 1 else None
                ),
                "emotional_intensity": self.emotional_intensity["current"],
            },
        }

    def _store_emotional_log(self, log_entry: Dict[str, Any]) -> None:
        """Store emotional log entry with rotation."""
        try:
            self.emotional_log.append(log_entry)

            # Rotate logs if too many
            if len(self.emotional_log) > 1000:
                self._rotate_logs()

        except Exception as e:
            logger.error(f"Error storing emotional log: {e}")

    def _rotate_logs(self) -> None:
        """Rotate and archive old logs."""
        try:
            # Create timestamp for archive
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archive_path = self.log_directory / f"emotional_log_{timestamp}.json"

            # Archive current logs
            with open(archive_path, "w") as f:
                json.dump(self.emotional_log, f, indent=2)

            # Clear current log, keeping last 100 entries
            self.emotional_log = self.emotional_log[-100:]

        except Exception as e:
            logger.error(f"Error rotating logs: {e}")

    def _update_analytics(self, log_entry: Dict[str, Any]) -> None:
        """Update analytics with new log entry."""
        try:
            timestamp = datetime.fromisoformat(log_entry["timestamp"])
            tone = log_entry["tone"]

            # Update daily distribution
            day_key = timestamp.strftime("%Y-%m-%d")
            self.voice_analytics["daily_tone_distribution"][day_key][tone] += 1

            # Update hourly patterns
            hour_key = timestamp.strftime("%H")
            self.voice_analytics["hourly_patterns"][hour_key][tone] += 1

            # Update transition effectiveness
            if "voice_metrics" in log_entry:
                self.voice_analytics["transition_effectiveness"][tone].append(
                    log_entry["voice_metrics"].get("tone_quality", 0.8)
                )

            # Cleanup old analytics
            self._cleanup_old_analytics()

        except Exception as e:
            logger.error(f"Error updating analytics: {e}")

    def _cleanup_old_analytics(self) -> None:
        """Clean up old analytics data."""
        try:
            # Keep only last 30 days of data
            cutoff = datetime.utcnow() - timedelta(days=30)

            # Clean daily distribution
            self.voice_analytics["daily_tone_distribution"] = {
                k: v
                for k, v in self.voice_analytics["daily_tone_distribution"].items()
                if datetime.strptime(k, "%Y-%m-%d") > cutoff
            }

            # Trim transition effectiveness history
            for tone in self.voice_analytics["transition_effectiveness"]:
                self.voice_analytics["transition_effectiveness"][tone] = (
                    self.voice_analytics["transition_effectiveness"][tone][-100:]
                )

        except Exception as e:
            logger.error(f"Error cleaning up analytics: {e}")

    def _prepare_avatar_state(self, tone: str, intensity: float) -> Dict[str, Any]:
        """Prepare avatar state data for future integration."""
        try:
            base_state = self.avatar_states[tone].copy()

            # Modify expression intensity
            base_state["intensity"] = intensity
            base_state["timestamp"] = datetime.utcnow().isoformat()

            return base_state

        except Exception as e:
            logger.error(f"Error preparing avatar state: {e}")
            return {}

    def export_emotional_log(self, path: Optional[str] = None) -> None:
        """
        Export emotional log to file.

        Args:
            path: Optional custom path for log file
        """
        try:
            if path is None:
                path = (
                    self.log_directory
                    / f"emotional_log_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                )

            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Export logs with analytics
            export_data = {
                "emotional_log": self.emotional_log,
                "analytics_summary": self._generate_analytics_summary(),
                "voice_quality_metrics": self.voice_quality_metrics[-100:],
                "export_timestamp": datetime.utcnow().isoformat(),
            }

            with open(path, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Emotional voice log exported to {path}")

        except Exception as e:
            logger.error(f"Log export failed: {e}")

    def _generate_analytics_summary(self) -> Dict[str, Any]:
        """Generate summary of voice analytics."""
        try:
            # Get most recent day's data
            latest_day = max(self.voice_analytics["daily_tone_distribution"].keys())
            latest_distribution = self.voice_analytics["daily_tone_distribution"][
                latest_day
            ]

            # Calculate averages
            tone_qualities = {
                tone: sum(scores) / len(scores) if scores else 0
                for tone, scores in self.voice_analytics[
                    "transition_effectiveness"
                ].items()
            }

            return {
                "latest_tone_distribution": dict(latest_distribution),
                "average_tone_quality": tone_qualities,
                "hourly_patterns": dict(self.voice_analytics["hourly_patterns"]),
                "voice_quality_summary": {
                    "average": (
                        sum(
                            m.get("tone_quality", 0)
                            for m in self.voice_quality_metrics[-100:]
                        )
                        / 100
                        if self.voice_quality_metrics
                        else 0
                    )
                },
            }

        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            return {}

    async def _execute_speech(self, message: str, profile: Dict[str, Any]) -> None:
        """Execute speech with the given profile."""
        try:
            # Adjust for privacy mode
            if "private" in message.lower():
                profile = self._adjust_for_privacy(profile)

            # Apply emotional intensity
            profile = self._apply_emotional_intensity(profile)

            # Add emotional markers
            message = self._add_emotional_markers(message, profile)

            # Log the voice output
            logger.info(
                f"Samantha ({self.current_tone} - {profile['intensity']:.2f}): {message}"
            )

            # Speak in a separate thread
            await asyncio.get_event_loop().run_in_executor(
                self.thread_pool, self._speak_sync, message
            )

            # Update metrics
            self._update_voice_metrics(self.current_tone, profile)

        except Exception as e:
            logger.error(f"Error executing speech: {e}")
            print(f"\n{message}\n")  # Fallback to print

    def _speak_sync(self, message: str) -> None:
        """Synchronous speak operation for thread pool."""
        try:
            self.voice_engine.say(message)
            self.voice_engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in sync speech: {e}")

    def _adjust_for_privacy(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust voice profile for private messages."""
        private_profile = profile.copy()
        private_profile.update(
            {
                "rate": 110,
                "volume": 0.4,
                "pitch": 0.8,
                "intensity": 0.3,
                "pause_factor": 1.5,
            }
        )
        return private_profile

    def _apply_emotional_intensity(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Apply emotional intensity to voice profile."""
        modified_profile = profile.copy()
        intensity = self.emotional_intensity["current"]

        # Scale voice parameters based on intensity
        modified_profile["volume"] *= 0.7 + (intensity * 0.3)
        modified_profile["rate"] = int(profile["rate"] * (0.9 + (intensity * 0.2)))
        modified_profile["intensity"] = intensity

        return modified_profile

    def _add_emotional_markers(self, message: str, profile: Dict[str, Any]) -> str:
        """Add emotional markers to the message."""
        inflection = profile["inflection"]
        pause_factor = profile["pause_factor"]

        # Add pauses for emotional effect
        message = re.sub(r"([.!?]) ", rf'\1{" " * int(pause_factor * 2)} ', message)

        # Add emphasis based on inflection
        if inflection == "varied":
            message = re.sub(
                r"\b(breakthrough|amazing|exciting)\b", r"... \1!", message, flags=re.I
            )
        elif inflection == "gentle":
            message = re.sub(
                r"\b(concerned|worried|careful)\b", r"... \1...", message, flags=re.I
            )

        return message

    def _update_voice_metrics(self, tone: str, profile: Dict[str, Any]) -> None:
        """Update voice analytics metrics."""
        self.voice_metrics["voice_profile_usage"][tone] += 1
        self.voice_metrics["intensity_history"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "tone": tone,
                "intensity": profile["intensity"],
            }
        )

        # Keep history manageable
        if len(self.voice_metrics["intensity_history"]) > 1000:
            self.voice_metrics["intensity_history"] = self.voice_metrics[
                "intensity_history"
            ][-1000:]

    def update_emotional_intensity(self, target_intensity: float) -> None:
        """
        Update the target emotional intensity.

        Args:
            target_intensity: Target intensity value (0.0 to 1.0)
        """
        self.emotional_intensity["target"] = max(0.0, min(1.0, target_intensity))
        current = self.emotional_intensity["current"]
        target = self.emotional_intensity["target"]
        rate = self.emotional_intensity["transition_rate"]

        # Smooth transition
        self.emotional_intensity["current"] += (target - current) * rate

    async def speak(self, message: str) -> None:
        """
        Enhanced speak method with emotional expression.

        Args:
            message: Message to speak
        """
        await self.speak_with_emotion(message, self.current_tone)

    def get_voice_analytics(self) -> Dict[str, Any]:
        """Get comprehensive voice analytics data."""
        return {
            "profile_usage": dict(self.voice_metrics["voice_profile_usage"]),
            "intensity_trends": self.voice_metrics["intensity_history"][-10:],
            "emotional_transitions": self.voice_metrics["emotional_transitions"][-10:],
            "current_state": {
                "tone": self.current_tone,
                "intensity": self.emotional_intensity["current"],
            },
        }

    def adapt_to_future(self, event_data: Dict[str, Any]) -> None:
        """
        Modify traits or modules based on forecast.

        Args:
            event_data: Future event data to adapt to
        """
        try:
            event_type = event_data.get("type", "").lower()

            if "quantum" in event_data["event"].lower():
                self.activate_module("QuantumAI")
                self.persona_traits["foresight"] = "enabled"
                self.quantum_ready = True
                logger.info("Quantum AI capabilities activated")

            elif "ai_evolution" in event_type:
                self.persona_traits["learning_rate"] *= 1.2
                self.activate_module("EvolutionaryAI")
                logger.info("AI evolution adaptations applied")

            # Record adaptation
            logger.info(f"Adapted to future event: {event_data['event']}")

        except Exception as e:
            logger.error(f"Error adapting to future event: {str(e)}")

    def announce_future_event(self, event: Dict[str, Any]) -> None:
        """
        Announce a future event through voice interface.

        Args:
            event: Future event data to announce
        """
        try:
            # Generate announcement content
            announcement = self._generate_announcement(event)

            # Speak the announcement
            self.respond_with_voice(announcement["voice_message"])

            # Record announcement
            self._record_announcement(announcement)

            # Generate headline summary if requested
            if event.get("type") == "web_trend":
                self.announce_headlines([event])

        except Exception as e:
            logger.error(f"Error announcing future event: {str(e)}")

    def announce_headlines(self, trends: List[Dict[str, Any]]) -> None:
        """Announce trend headlines in a news-style format."""
        try:
            if not trends:
                return

            intro = "Here are the latest technology headlines:"
            self.respond_with_voice(intro)

            for trend in trends:
                headline = self._generate_headline(trend)
                if headline:
                    self.respond_with_voice(headline)

            outro = "That's all for now. I'll keep monitoring for more developments."
            self.respond_with_voice(outro)

        except Exception as e:
            logger.error(f"Error announcing headlines: {e}")

    def _generate_announcement(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed announcement."""
        try:
            event_type = event.get("type", "unknown")

            if event_type == "web_trend":
                return self._generate_trend_announcement(event)
            else:
                return self._generate_future_event_announcement(event)

        except Exception as e:
            logger.error(f"Error generating announcement: {e}")
            return {
                "voice_message": "I've detected something interesting but had trouble processing it.",
                "type": "error",
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_trend_announcement(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a trend-specific announcement with emotional awareness."""
        try:
            category = trend.get("primary_category", "").replace("_", " ").title()
            confidence = trend.get("confidence", 0)
            summary = trend.get("summary", "")
            source = trend.get("source", "").split("//")[-1].split("/")[0]
            sentiment = trend.get("sentiment", {})
            metrics = trend.get("metrics", {})

            # Select emotional response
            sentiment_type = sentiment.get("primary", "neutral")
            emotional_intro = self._select_emotional_response(sentiment_type)

            # Build detailed announcement
            parts = [emotional_intro]

            # Add main trend information
            parts.append(f"A significant {category} trend has emerged.")

            if summary:
                parts.append(summary)

            # Add impact assessment
            if metrics.get("cross_domain_impact", 0) > 1:
                parts.append(
                    "This development has broad implications across multiple domains."
                )

            if metrics.get("novelty", 0) > 0.8:
                parts.append("This represents a novel breakthrough in the field.")

            # Add source and confidence
            parts.append(
                f"This information comes from {source} with "
                f"{self._get_confidence_description(confidence)} confidence."
            )

            # Add adaptive response
            if self._should_adapt(trend):
                parts.append("I'm adapting my systems to incorporate this development.")

            voice_message = " ".join(parts)

            return {
                "voice_message": voice_message,
                "type": "trend",
                "trend_data": trend,
                "timestamp": datetime.now().isoformat(),
                "emotional_context": {
                    "sentiment": sentiment_type,
                    "response_type": emotional_intro,
                },
            }

        except Exception as e:
            logger.error(f"Error generating trend announcement: {e}")
            return self._generate_fallback_announcement("trend")

    def _select_emotional_response(self, sentiment: str) -> str:
        """Select appropriate emotional response based on sentiment."""
        try:
            responses = self.emotional_responses.get(
                sentiment, self.emotional_responses["neutral"]
            )
            return responses[hash(datetime.now().isoformat()) % len(responses)]
        except Exception as e:
            logger.error(f"Error selecting emotional response: {e}")
            return "I've detected something interesting."

    def _should_adapt(self, trend: Dict[str, Any]) -> bool:
        """Determine if adaptation is needed based on trend data."""
        try:
            category = trend.get("primary_category", "")
            impact = trend.get("impact_score", 0)
            metrics = trend.get("metrics", {})

            return (
                category in ["ai_ml", "quantum"]
                or impact > 2
                or metrics.get("novelty", 0) > 0.8
                or metrics.get("cross_domain_impact", 0) > 1
            )
        except Exception as e:
            logger.error(f"Error checking adaptation need: {e}")
            return False

    def _generate_future_event_announcement(
        self, event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a future event announcement."""
        summary = self._generate_event_summary(event)
        confidence = event.get("confidence", 0)

        voice_message = (
            f"Samantha: Attention. {summary} "
            f"Confidence level is {self._get_confidence_description(confidence)}. "
            "I'm adapting my systems to prepare for this development."
        )

        return {
            "voice_message": voice_message,
            "type": "future_event",
            "event_data": event,
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_headline(self, trend: Dict[str, Any]) -> Optional[str]:
        """Generate an engaging news-style headline."""
        try:
            category = trend.get("primary_category", "").replace("_", " ").title()
            preview = trend.get("preview", "").split(".")[0]
            source = trend.get("source", "").split("//")[-1].split("/")[0]
            sentiment = trend.get("sentiment", {}).get("primary", "neutral")
            metrics = trend.get("metrics", {})

            headline_parts = []

            # Add breaking news indicator for high-impact trends
            if metrics.get("impact_score", 0) > 2:
                headline_parts.append("Breaking:")

            # Add source
            headline_parts.append(f"From {source}:")

            # Add main headline
            if metrics.get("novelty", 0) > 0.8:
                headline_parts.append("Breakthrough -")

            headline_parts.append(preview)

            # Add impact indicator
            if metrics.get("cross_domain_impact", 0) > 1:
                headline_parts.append("(Cross-domain implications)")

            return " ".join(headline_parts)

        except Exception as e:
            logger.error(f"Error generating headline: {e}")
            return None

    def _generate_fallback_announcement(self, announcement_type: str) -> Dict[str, Any]:
        """Generate a fallback announcement when primary generation fails."""
        return {
            "voice_message": "I've detected something interesting but need more time to analyze it fully.",
            "type": announcement_type,
            "timestamp": datetime.now().isoformat(),
            "is_fallback": True,
        }

    def _record_announcement(self, announcement: Dict[str, Any]) -> None:
        """Record an announcement in history."""
        try:
            self.announcement_history.append(announcement)
            self.last_announcement = announcement

            # Save to file
            self._save_announcement_history()

        except Exception as e:
            logger.error(f"Error recording announcement: {e}")

    def _load_announcement_history(self) -> None:
        """Load announcement history from file."""
        try:
            if Path(self.announcement_file).exists():
                with open(self.announcement_file, "r") as f:
                    data = json.load(f)
                    self.announcement_history = data.get("announcements", [])
        except Exception as e:
            logger.error(f"Error loading announcement history: {e}")

    def _save_announcement_history(self) -> None:
        """Save announcement history to file."""
        try:
            # Keep last 100 announcements
            data = {"announcements": self.announcement_history[-100:]}
            with open(self.announcement_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving announcement history: {e}")

    def respond_with_voice(self, message: str) -> None:
        """
        Output a voice message through the system.

        Args:
            message: Message to speak
        """
        if self.voice_enabled:
            print(f"\n{message}\n")  # Placeholder for actual voice output
            logger.info(f"Voice output: {message}")

    def _generate_event_summary(self, event: Dict[str, Any]) -> str:
        """Generate a human-friendly summary of the event."""
        event_type = event.get("type", "").replace("_", " ").title()
        event_desc = event.get("event", "Upcoming development detected")

        return f"{event_type}: {event_desc}."

    def _get_confidence_description(self, confidence: float) -> str:
        """Convert confidence score to human-friendly description."""
        if confidence >= 0.9:
            return "very high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "moderate"
        else:
            return "uncertain"

    def activate_module(self, module_name: str) -> None:
        """
        Activate a specific module.

        Args:
            module_name: Name of module to activate
        """
        self.active_modules.add(module_name)
        logger.info(f"Activated module: {module_name}")

    def deactivate_module(self, module_name: str) -> None:
        """
        Deactivate a specific module.

        Args:
            module_name: Name of module to deactivate
        """
        self.active_modules.discard(module_name)
        logger.info(f"Deactivated module: {module_name}")

    def get_active_modules(self) -> Set[str]:
        """Get list of currently active modules."""
        return self.active_modules

    def get_persona_traits(self) -> Dict[str, Any]:
        """Get current persona traits."""
        return self.persona_traits.copy()

    def get_last_announcement(self) -> Optional[Dict[str, Any]]:
        """Get the last announcement made."""
        return self.last_announcement

    def modulate_tone(
        self,
        trend_data: List[Tuple[str, int]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Intelligently modulate voice tone based on trend data and context.

        Args:
            trend_data: List of (term, count) tuples from trend analysis
            context: Optional additional context for tone decision

        Returns:
            Selected tone for response
        """
        try:
            if not trend_data:
                return self.current_tone

            # Extract terms and their frequencies
            terms = set(term.lower() for term, _ in trend_data)

            # Score each tone based on trigger matches
            tone_scores = defaultdict(float)
            for tone, pattern in self.tone_patterns.items():
                # Calculate match score
                matches = terms.intersection(pattern["triggers"])
                score = len(matches) / len(terms) if terms else 0

                # Apply context weights
                if context:
                    if context.get("urgency") == "high" and tone == "assertive":
                        score *= 1.5
                    elif (
                        context.get("user_emotion") == "frustrated"
                        and tone == "empathetic"
                    ):
                        score *= 1.3

                tone_scores[tone] = score

            # Consider tone history for smooth transitions
            current_tone = self.tone_history[-1]
            valid_transitions = self.tone_transitions[current_tone]

            # Select highest scoring tone from valid transitions
            valid_scores = {
                tone: score
                for tone, score in tone_scores.items()
                if tone in valid_transitions or tone == current_tone
            }

            if valid_scores:
                new_tone = max(valid_scores.items(), key=lambda x: x[1])[0]
            else:
                new_tone = "neutral"

            # Update tone history
            self.tone_history.append(new_tone)
            if len(self.tone_history) > self.max_tone_history:
                self.tone_history.pop(0)

            # Record transition
            if new_tone != current_tone:
                self.voice_metrics["tone_transitions"][(current_tone, new_tone)] += 1
                logger.info(f"Tone modulated from {current_tone} to {new_tone}")

            self.current_tone = new_tone
            return new_tone

        except Exception as e:
            logger.error(f"Error in tone modulation: {e}")
            return "neutral"

    def format_message_with_tone(self, message: str, tone: Optional[str] = None) -> str:
        """
        Format a message with appropriate tone-based prefix.

        Args:
            message: The message to format
            tone: Optional specific tone to use (defaults to current_tone)

        Returns:
            Formatted message with tone-appropriate prefix
        """
        try:
            use_tone = tone or self.current_tone
            prefixes = self.tone_patterns[use_tone]["prefixes"]

            # Select prefix based on message content or randomly
            prefix = prefixes[hash(message) % len(prefixes)]

            return f"{prefix}{message}"

        except Exception as e:
            logger.error(f"Error formatting message with tone: {e}")
            return message

    async def announce_trend(self, headline: str, source: str) -> None:
        """
        Announce a detected global trend through voice with analytics and tone modulation.

        Args:
            headline: The trend headline to announce
            source: The source of the trend
        """
        if not self.voice_enabled:
            return

        base_message = f"Global trend detected from {source}. Headline: {headline}"

        # Analyze current trends
        trends = self.analyze_voice_trends()

        # Modulate tone based on trends and content
        context = {
            "urgency": (
                "high"
                if any(
                    urgent in headline.lower()
                    for urgent in ["urgent", "critical", "breaking"]
                )
                else "normal"
            ),
            "source_type": "primary" if source in self.primary_sources else "secondary",
        }

        self.modulate_tone(trends, context)

        # Format message with appropriate tone
        message = self.format_message_with_tone(base_message)

        # Speak the message
        await self.speak(message)

        # Record announcement with metadata
        announcement = {
            "timestamp": datetime.utcnow().isoformat(),
            "headline": headline,
            "source": source,
            "message": message,
            "tone": self.current_tone,
            "type": "trend",
            "context": context,
        }

        self.last_announcement = announcement
        self.announcement_memory.append(announcement)
        self._record_announcement(announcement)

        # Trigger trend analysis periodically
        if len(self.announcement_memory) % 10 == 0:
            self.analyze_voice_trends()

    def analyze_voice_trends(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """
        Analyze trends in voice announcements.

        Args:
            top_n: Number of top terms to analyze

        Returns:
            List of (term, count) tuples for most common terms
        """
        try:
            # Combine all announcement messages
            all_text = " ".join(entry["message"] for entry in self.announcement_memory)

            # Extract meaningful words (excluding common stop words)
            words = [
                word.lower()
                for word in re.findall(r"\b\w+\b", all_text)
                if len(word) > 3 and word.lower() not in self.get_stop_words()
            ]

            # Get common terms
            common_terms = Counter(words).most_common(top_n)

            # Log analysis results
            logger.info("\nTop recurring terms in Samantha's voice summaries:")
            for word, count in common_terms:
                logger.info(f"- {word}: {count} times")

            # Check for potential bias
            self._check_content_bias(words, common_terms)

            # Analyze tone distribution
            self._analyze_tone_distribution()

            # Update metrics
            self._update_voice_metrics(common_terms)

            return common_terms

        except Exception as e:
            logger.error(f"Error analyzing voice trends: {e}")
            return []

    def _analyze_tone(self, message: str) -> str:
        """Analyze the tone of a message."""
        # Count sentiment keywords
        sentiment_counts = {
            tone: sum(1 for phrase in phrases if phrase.lower() in message.lower())
            for tone, phrases in self.emotional_responses.items()
        }

        # Return dominant tone or neutral
        if not sentiment_counts:
            return "neutral"
        return max(sentiment_counts.items(), key=lambda x: x[1])[0]

    def _adjust_message_tone(self, message: str, current_tone: str) -> str:
        """Adjust message tone based on analytics."""
        try:
            # Check tone distribution
            tone_dist = self.voice_metrics["tone_distribution"]
            total_tones = sum(tone_dist.values()) or 1

            # If current tone is too dominant, shift towards balance
            if (
                tone_dist[current_tone] / total_tones
                > self.bias_thresholds["tone_imbalance"]
            ):
                # Find underrepresented tone
                underused_tone = min(tone_dist.items(), key=lambda x: x[1])[0]

                # Get alternative phrase
                alt_phrase = self.emotional_responses[underused_tone][0]
                message = f"{alt_phrase} {message}"

            return message

        except Exception as e:
            logger.error(f"Error adjusting message tone: {e}")
            return message

    def _check_content_bias(
        self, words: List[str], common_terms: List[Tuple[str, int]]
    ) -> None:
        """Check for content bias in voice patterns."""
        if not words or not common_terms:
            return

        # Check term dominance
        most_common = common_terms[0]
        if most_common[1] > len(words) * self.bias_thresholds["term_dominance"]:
            logger.warning(
                f"\nPotential bias detected: Samantha may be overly focused on '{most_common[0]}' "
                f"({most_common[1]} occurrences)"
            )

    def _analyze_tone_distribution(self) -> None:
        """Analyze distribution of tones in announcements."""
        try:
            total = len(self.announcement_memory) or 1
            tone_dist = defaultdict(int)

            for announcement in self.announcement_memory:
                tone_dist[announcement.get("tone", "neutral")] += 1

            # Log distribution
            logger.info("\nTone distribution in announcements:")
            for tone, count in tone_dist.items():
                percentage = (count / total) * 100
                logger.info(f"- {tone}: {percentage:.1f}%")

            # Update metrics
            self.voice_metrics["tone_distribution"] = dict(tone_dist)

        except Exception as e:
            logger.error(f"Error analyzing tone distribution: {e}")

    def _update_voice_metrics(self, common_terms: List[Tuple[str, int]]) -> None:
        """Update voice analytics metrics."""
        try:
            self.voice_metrics["total_announcements"] = len(self.announcement_memory)

            # Update topic focus
            for term, count in common_terms:
                self.voice_metrics["topic_focus"][term] = count

            # Calculate sentiment balance
            for announcement in self.announcement_memory:
                tone = announcement.get("tone", "neutral")
                self.voice_metrics["sentiment_balance"][tone] += 1

        except Exception as e:
            logger.error(f"Error updating voice metrics: {e}")

    def get_stop_words(self) -> Set[str]:
        """Get common stop words to exclude from analysis."""
        return {
            "the",
            "and",
            "this",
            "that",
            "from",
            "with",
            "has",
            "have",
            "been",
            "were",
            "they",
            "their",
            "what",
            "when",
            "where",
            "who",
            "will",
            "more",
            "about",
            "which",
            "would",
            "could",
            "should",
        }

    def get_voice_metrics(self) -> Dict[str, Any]:
        """Get current voice analytics metrics."""
        return self.voice_metrics.copy()
