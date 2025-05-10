"""
Persona Calibrator for dynamic personality adaptation.
"""
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class PersonaCalibrator:
    """Calibrates persona responses based on user interaction context."""
    
    def __init__(self, system):
        """
        Initialize the persona calibrator.
        
        Args:
            system: Reference to the main voice system
        """
        self.system = system
        self.history: List[Tuple[str, Dict[str, Any]]] = []
        self._init_emotion_keywords()
        self._init_context_patterns()
        
    def _init_emotion_keywords(self):
        """Initialize enhanced emotion keyword mappings."""
        self.emotion_keywords = {
            "sad": [
                "sad", "unhappy", "depressed", "down", "blue", "upset",
                "heartbroken", "miserable", "lonely", "hopeless", "grief"
            ],
            "happy": [
                "happy", "joy", "excited", "great", "wonderful", "good",
                "delighted", "thrilled", "ecstatic", "pleased", "blessed"
            ],
            "angry": [
                "angry", "mad", "frustrated", "annoyed", "upset",
                "furious", "outraged", "irritated", "hostile", "enraged"
            ],
            "confused": [
                "confused", "unsure", "don't understand", "what do you mean",
                "puzzled", "perplexed", "lost", "uncertain", "unclear"
            ],
            "anxious": [
                "worried", "anxious", "nervous", "stressed", "concerned",
                "uneasy", "apprehensive", "fearful", "panicked", "tense"
            ],
            "tired": [
                "tired", "exhausted", "sleepy", "fatigued",
                "drained", "worn out", "weary", "lethargic"
            ],
            "empathetic": [
                "help", "please", "need", "could you", "would you",
                "understand", "feel for", "care about", "support"
            ],
            "excited": [
                "excited", "thrilled", "eager", "enthusiastic", "pumped",
                "energetic", "passionate", "motivated", "inspired"
            ],
            "grateful": [
                "thank", "grateful", "appreciate", "thankful", "blessed",
                "indebted", "moved", "touched", "appreciative"
            ],
            "curious": [
                "curious", "interested", "wonder", "tell me", "how does",
                "what if", "why is", "how come", "fascinating"
            ],
            "confident": [
                "sure", "certain", "confident", "know", "absolutely",
                "definitely", "positive", "convinced", "assured"
            ],
            "skeptical": [
                "doubt", "skeptical", "not sure", "really?", "prove",
                "suspicious", "unconvinced", "questionable"
            ]
        }
        
    def _init_context_patterns(self):
        """Initialize context detection patterns."""
        self.context_patterns = {
            "urgency": re.compile(
                r"(urgent|asap|emergency|quickly|right now|immediate)",
                re.IGNORECASE
            ),
            "formality": re.compile(
                r"(sir|madam|please|kindly|would you|could you|formal)",
                re.IGNORECASE
            ),
            "technical": re.compile(
                r"(code|program|error|bug|system|function|api|data)",
                re.IGNORECASE
            ),
            "personal": re.compile(
                r"(i feel|i am|i'm|my|mine|myself|personally)",
                re.IGNORECASE
            )
        }
        
        # Initialize voice modulation profiles
        self.voice_profiles = {
            "sad": {
                "pitch": 0.9,
                "speed": 0.8,
                "volume": 0.7,
                "emphasis": 0.6,
                "breathiness": 0.4
            },
            "happy": {
                "pitch": 1.1,
                "speed": 1.1,
                "volume": 0.9,
                "emphasis": 0.8,
                "breathiness": 0.2
            },
            "angry": {
                "pitch": 1.2,
                "speed": 1.2,
                "volume": 0.9,
                "emphasis": 1.0,
                "breathiness": 0.1
            },
            "confused": {
                "pitch": 1.0,
                "speed": 0.9,
                "volume": 0.8,
                "emphasis": 0.7,
                "breathiness": 0.3
            },
            "anxious": {
                "pitch": 1.1,
                "speed": 1.2,
                "volume": 0.8,
                "emphasis": 0.9,
                "breathiness": 0.4
            },
            "tired": {
                "pitch": 0.9,
                "speed": 0.8,
                "volume": 0.7,
                "emphasis": 0.5,
                "breathiness": 0.5
            },
            "empathetic": {
                "pitch": 1.0,
                "speed": 0.9,
                "volume": 0.8,
                "emphasis": 0.7,
                "breathiness": 0.3
            },
            "excited": {
                "pitch": 1.2,
                "speed": 1.2,
                "volume": 0.9,
                "emphasis": 0.9,
                "breathiness": 0.2
            },
            "grateful": {
                "pitch": 1.1,
                "speed": 1.0,
                "volume": 0.8,
                "emphasis": 0.7,
                "breathiness": 0.3
            },
            "curious": {
                "pitch": 1.1,
                "speed": 1.0,
                "volume": 0.8,
                "emphasis": 0.8,
                "breathiness": 0.2
            },
            "confident": {
                "pitch": 1.1,
                "speed": 1.0,
                "volume": 0.9,
                "emphasis": 0.9,
                "breathiness": 0.1
            },
            "skeptical": {
                "pitch": 1.0,
                "speed": 0.9,
                "volume": 0.8,
                "emphasis": 0.8,
                "breathiness": 0.2
            }
        }
        
    def calibrate(self, input_text: str) -> Dict[str, Any]:
        """Enhanced calibration with context awareness."""
        try:
            text = input_text.lower()
            
            # Detect primary and secondary emotions
            emotions = self._detect_emotions(text)
            primary_emotion = emotions[0] if emotions else "neutral"
            
            # Analyze context
            context = self._analyze_context(text)
            
            # Build enhanced profile
            profile = {
                "tone": self._determine_tone(primary_emotion, context),
                "response_delay": self._calculate_delay(text, primary_emotion, context),
                "voice_modulation": self._get_voice_modulation(primary_emotion, context),
                "emotion_context": {
                    "primary": primary_emotion,
                    "secondary": emotions[1] if len(emotions) > 1 else None,
                    "intensity": self._calculate_emotion_intensity(text, primary_emotion)
                },
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            self.history.append((input_text, profile))
            logger.debug(f"Calibrated enhanced profile for input: {input_text}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to calibrate persona: {str(e)}")
            return self._get_default_profile()
            
    def _detect_emotions(self, text: str) -> List[str]:
        """Detect multiple emotions with intensity scoring."""
        emotion_scores = {}
        words = text.split()
        
        for emotion, keywords in self.emotion_keywords.items():
            # Calculate weighted score based on keyword matches and position
            score = 0
            for i, word in enumerate(words):
                if any(keyword in word for keyword in keywords):
                    # Words at the beginning have higher weight
                    position_weight = 1.0 - (i / len(words) * 0.5)
                    score += position_weight
                    
            emotion_scores[emotion] = score
            
        # Sort emotions by score and return top ones
        sorted_emotions = sorted(
            emotion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return emotions with non-zero scores
        return [emotion for emotion, score in sorted_emotions if score > 0]
        
    def _analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze conversation context."""
        context = {
            "urgency": bool(self.context_patterns["urgency"].search(text)),
            "formality": bool(self.context_patterns["formality"].search(text)),
            "technical": bool(self.context_patterns["technical"].search(text)),
            "personal": bool(self.context_patterns["personal"].search(text)),
            "complexity": self._calculate_complexity(text)
        }
        
        return context
        
    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        # Simple complexity scoring based on sentence length and word length
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words)
        sentence_length = len(words)
        
        # Normalize scores
        length_score = min(sentence_length / 20.0, 1.0)  # Cap at 20 words
        word_score = min(avg_word_length / 8.0, 1.0)    # Cap at 8 chars
        
        return (length_score + word_score) / 2
        
    def _calculate_emotion_intensity(self, text: str, emotion: str) -> float:
        """Calculate emotion intensity based on keyword frequency and modifiers."""
        intensity = 0.0
        words = text.split()
        
        # Check for intensity modifiers
        intensity_modifiers = {
            "very": 0.3,
            "really": 0.3,
            "extremely": 0.4,
            "so": 0.2,
            "totally": 0.3,
            "completely": 0.4,
            "absolutely": 0.4
        }
        
        # Base intensity from keyword matches
        keywords = self.emotion_keywords.get(emotion, [])
        matches = sum(1 for word in words if any(keyword in word for keyword in keywords))
        base_intensity = min(matches / len(words) * 2.0, 1.0)
        
        # Add modifier effects
        for word in words:
            if word in intensity_modifiers:
                intensity += intensity_modifiers[word]
                
        # Combine and normalize
        total_intensity = min(base_intensity + intensity, 1.0)
        return max(total_intensity, 0.1)  # Ensure minimum intensity
        
    def _get_default_profile(self) -> Dict[str, Any]:
        """Get default profile with full structure."""
        return {
            "tone": "neutral",
            "response_delay": "normal",
            "voice_modulation": self.voice_profiles["neutral"],
            "emotion_context": {
                "primary": "neutral",
                "secondary": None,
                "intensity": 0.5
            },
            "context": {
                "urgency": False,
                "formality": False,
                "technical": False,
                "personal": False,
                "complexity": 0.5
            },
            "timestamp": datetime.now().isoformat()
        }
        
    def analyze_trends(self) -> Dict[str, Any]:
        """Enhanced trend analysis."""
        if not self.history:
            return {}
            
        # Extract data
        emotions = [
            profile["emotion_context"]["primary"]
            for _, profile in self.history
        ]
        contexts = [
            profile["context"]
            for _, profile in self.history
        ]
        intensities = [
            profile["emotion_context"]["intensity"]
            for _, profile in self.history
        ]
        
        # Calculate trends
        return {
            "dominant_emotion": max(set(emotions), key=emotions.count),
            "average_intensity": sum(intensities) / len(intensities),
            "context_distribution": {
                context_type: sum(1 for ctx in contexts if ctx[context_type])
                for context_type in ["urgency", "formality", "technical", "personal"]
            },
            "emotion_progression": self._calculate_emotion_progression(),
            "interaction_patterns": self._analyze_interaction_patterns()
        }
        
    def _calculate_emotion_progression(self) -> Dict[str, Any]:
        """Analyze emotion changes over time."""
        if len(self.history) < 2:
            return {}
            
        changes = []
        for i in range(1, len(self.history)):
            prev = self.history[i-1][1]["emotion_context"]["primary"]
            curr = self.history[i][1]["emotion_context"]["primary"]
            if prev != curr:
                changes.append((prev, curr))
                
        return {
            "total_changes": len(changes),
            "common_transitions": self._get_common_transitions(changes)
        }
        
    def _analyze_interaction_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in user interactions."""
        if not self.history:
            return {}
            
        # Analyze timing patterns
        times = [
            datetime.fromisoformat(profile["timestamp"])
            for _, profile in self.history
        ]
        
        intervals = [
            (times[i] - times[i-1]).total_seconds()
            for i in range(1, len(times))
        ]
        
        return {
            "average_interval": sum(intervals) / len(intervals) if intervals else 0,
            "interaction_frequency": len(self.history) / (
                (times[-1] - times[0]).total_seconds() / 3600
            ) if len(times) > 1 else 0
        }
        
    def show_history(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get calibration history."""
        return self.history
        
    def get_last_profile(self) -> Dict[str, Any]:
        """Get most recent calibration profile."""
        return self.history[-1][1] if self.history else None
        
    def clear_history(self):
        """Clear calibration history."""
        self.history = []
        logger.info("Cleared calibration history")
        
    def _determine_tone(self, emotion: str, context: Dict[str, Any]) -> str:
        """
        Determine appropriate response tone.
        
        Args:
            emotion: Detected emotion
            context: Conversation context
            
        Returns:
            Appropriate tone string
        """
        tone_mapping = {
            "sad": "empathetic",
            "happy": "cheerful",
            "angry": "calm",
            "confused": "patient",
            "anxious": "reassuring",
            "tired": "gentle",
            "empathetic": "supportive",
            "neutral": "professional"
        }
        return tone_mapping.get(emotion, "neutral")
        
    def _calculate_delay(self, text: str, emotion: str, context: Dict[str, Any]) -> str:
        """
        Calculate appropriate response delay.
        
        Args:
            text: Input text
            emotion: Detected emotion
            context: Conversation context
            
        Returns:
            Delay setting string
        """
        # Slower response for emotional or complex queries
        if emotion in ["sad", "confused", "anxious"]:
            return "slow"
        elif len(text.split()) > 15:  # Complex query
            return "moderate"
        else:
            return "normal"
            
    def _get_voice_modulation(self, emotion: str, context: Dict[str, Any]) -> Dict[str, float]:
        """
        Get voice modulation parameters.
        
        Args:
            emotion: Detected emotion
            context: Conversation context
            
        Returns:
            Voice modulation parameters
        """
        modulation_params = {
            "sad": {"pitch": 0.9, "speed": 0.8, "volume": 0.7},
            "happy": {"pitch": 1.1, "speed": 1.1, "volume": 0.9},
            "angry": {"pitch": 1.0, "speed": 0.9, "volume": 0.8},
            "confused": {"pitch": 1.0, "speed": 0.9, "volume": 0.8},
            "anxious": {"pitch": 1.0, "speed": 0.9, "volume": 0.8},
            "tired": {"pitch": 0.9, "speed": 0.8, "volume": 0.7},
            "empathetic": {"pitch": 1.0, "speed": 0.9, "volume": 0.8},
            "neutral": {"pitch": 1.0, "speed": 1.0, "volume": 0.8}
        }
        return modulation_params.get(emotion, modulation_params["neutral"])
        
    def _get_common_transitions(self, changes: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Analyze common emotion transitions."""
        transitions = {}
        for prev, curr in changes:
            transitions.setdefault(prev, []).append(curr)
            
        common_transitions = {
            emotion: max(set(transitions.get(emotion, [])), key=transitions.get(emotion, []).count)
            for emotion in set(emotion for emotion, _ in changes)
        }
        
        return common_transitions
        
    def _calculate_emotion_progression(self) -> Dict[str, Any]:
        """Analyze emotion changes over time."""
        if len(self.history) < 2:
            return {}
            
        changes = []
        for i in range(1, len(self.history)):
            prev = self.history[i-1][1]["emotion_context"]["primary"]
            curr = self.history[i][1]["emotion_context"]["primary"]
            if prev != curr:
                changes.append((prev, curr))
                
        return {
            "total_changes": len(changes),
            "common_transitions": self._get_common_transitions(changes)
        }
        
    def _analyze_interaction_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in user interactions."""
        if not self.history:
            return {}
            
        # Analyze timing patterns
        times = [
            datetime.fromisoformat(profile["timestamp"])
            for _, profile in self.history
        ]
        
        intervals = [
            (times[i] - times[i-1]).total_seconds()
            for i in range(1, len(times))
        ]
        
        return {
            "average_interval": sum(intervals) / len(intervals) if intervals else 0,
            "interaction_frequency": len(self.history) / (
                (times[-1] - times[0]).total_seconds() / 3600
            ) if len(times) > 1 else 0
        } 