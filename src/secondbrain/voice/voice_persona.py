"""
Voice persona management system for SecondBrain.
Handles different voice personalities and their characteristics.
"""
import logging
import json
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from .voice_processor import VoiceEngine

logger = logging.getLogger(__name__)

class EmotionType(Enum):
    NEUTRAL = auto()
    HAPPY = auto()
    SAD = auto()
    EXCITED = auto()
    SERIOUS = auto()
    PLAYFUL = auto()
    CONCERNED = auto()
    CONFIDENT = auto()
    THOUGHTFUL = auto()

class VoiceStyle(Enum):
    NATURAL = "natural"
    ASSERTIVE = "assertive"
    CASUAL = "casual"
    FORMAL = "formal"
    EMPATHETIC = "empathetic"
    TECHNICAL = "technical"

@dataclass
class EmotionProfile:
    emotion: EmotionType
    pitch_modifier: float
    speed_modifier: float
    intensity: float = 1.0
    
    def __post_init__(self):
        """Validate emotion profile parameters."""
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Ensure emotion profile parameters are within valid ranges."""
        if not 0.5 <= self.pitch_modifier <= 2.0:
            raise ValueError(f"Pitch modifier {self.pitch_modifier} out of valid range [0.5, 2.0]")
        if not 0.5 <= self.speed_modifier <= 2.0:
            raise ValueError(f"Speed modifier {self.speed_modifier} out of valid range [0.5, 2.0]")
        if not 0.0 <= self.intensity <= 2.0:
            raise ValueError(f"Intensity {self.intensity} out of valid range [0.0, 2.0]")

@dataclass
class InteractionHistory:
    timestamp: datetime
    message: str
    emotion: EmotionType
    context: Optional[Dict[str, Any]] = None
    response_rating: Optional[float] = None

@dataclass
class VoicePersona:
    name: str
    style: VoiceStyle
    pitch: float
    speed: float
    description: str
    context_awareness: bool = True
    emotion_profiles: Dict[EmotionType, EmotionProfile] = field(default_factory=dict)
    catchphrases: List[str] = field(default_factory=list)
    interaction_history: List[InteractionHistory] = field(default_factory=list)
    adaptation_threshold: float = 0.1
    enable_memory_tracking: bool = False
    memory_engine: Any = None
    voice_engine: Optional[VoiceEngine] = None
    
    def __post_init__(self):
        """Initialize and validate persona attributes."""
        self._validate_parameters()
        if not self.emotion_profiles:
            self._init_default_emotions()
    
    def _validate_parameters(self):
        """Validate persona parameters."""
        if not 0.5 <= self.pitch <= 2.0:
            raise ValueError(f"Base pitch {self.pitch} out of valid range [0.5, 2.0]")
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError(f"Base speed {self.speed} out of valid range [0.5, 2.0]")
        if not isinstance(self.style, VoiceStyle):
            self.style = VoiceStyle(self.style)
    
    def _init_default_emotions(self):
        """Set up default emotion profiles for the persona."""
        self.emotion_profiles = {
            EmotionType.NEUTRAL: EmotionProfile(EmotionType.NEUTRAL, 1.0, 1.0),
            EmotionType.HAPPY: EmotionProfile(EmotionType.HAPPY, 1.1, 1.15),
            EmotionType.SAD: EmotionProfile(EmotionType.SAD, 0.9, 0.85),
            EmotionType.EXCITED: EmotionProfile(EmotionType.EXCITED, 1.2, 1.25),
            EmotionType.SERIOUS: EmotionProfile(EmotionType.SERIOUS, 0.95, 0.9),
            EmotionType.PLAYFUL: EmotionProfile(EmotionType.PLAYFUL, 1.15, 1.1),
            EmotionType.CONCERNED: EmotionProfile(EmotionType.CONCERNED, 0.85, 0.9),
            EmotionType.CONFIDENT: EmotionProfile(EmotionType.CONFIDENT, 1.1, 1.05),
            EmotionType.THOUGHTFUL: EmotionProfile(EmotionType.THOUGHTFUL, 0.95, 0.85)
        }
    
    def record_interaction(self, message: str, emotion: EmotionType, context: Optional[Dict] = None) -> None:
        """Record an interaction for learning and adaptation."""
        history_entry = InteractionHistory(
            timestamp=datetime.now(),
            message=message,
            emotion=emotion,
            context=context
        )
        self.interaction_history.append(history_entry)
        
        # Keep history manageable by limiting size
        if len(self.interaction_history) > 1000:
            self.interaction_history = self.interaction_history[-1000:]
    
    def rate_response(self, message: str, rating: float) -> None:
        """Rate a previous response for adaptation."""
        if not self.interaction_history:
            return
        
        # Find and rate the most recent matching interaction
        for entry in reversed(self.interaction_history):
            if entry.message == message:
                entry.response_rating = max(0.0, min(1.0, rating))
                self._adapt_to_feedback(entry)
                
                # Store in memory engine if enabled
                if self.enable_memory_tracking and self.memory_engine:
                    self.memory_engine.store(
                        context={
                            "time_of_day": entry.context.get("time_of_day") if entry.context else None,
                            "user_emotion": entry.context.get("user_emotion") if entry.context else None,
                            "conversation_topic": entry.context.get("conversation_topic") if entry.context else None
                        },
                        feedback={
                            "message": message,
                            "rating": rating,
                            "effectiveness": entry.response_rating,
                            "emotion": entry.emotion.name if entry.emotion else None
                        }
                    )
                break
    
    def _adapt_to_feedback(self, interaction: InteractionHistory) -> None:
        """Adapt persona parameters based on feedback."""
        if interaction.response_rating is None or interaction.response_rating >= 0.8:
            return
            
        # Adjust emotion profile based on poor ratings
        if interaction.emotion in self.emotion_profiles:
            profile = self.emotion_profiles[interaction.emotion]
            
            # Subtle adjustments based on rating
            adjustment = self.adaptation_threshold * (1 - interaction.response_rating)
            
            # Adjust parameters while keeping them within bounds
            profile.pitch_modifier = max(0.5, min(2.0, profile.pitch_modifier * (1 - adjustment)))
            profile.speed_modifier = max(0.5, min(2.0, profile.speed_modifier * (1 - adjustment)))
            profile.intensity = max(0.0, min(2.0, profile.intensity * (1 - adjustment)))
            
            logger.info(f"Adapted {self.name}'s {interaction.emotion.name} profile based on feedback")

    def get_context_modifier(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Get context-based modifications to voice parameters."""
        modifiers = {"pitch": 1.0, "speed": 1.0, "intensity": 1.0}
        
        if not self.context_awareness or not context:
            return modifiers
            
        # Check memory for similar contexts if memory tracking is enabled
        if self.enable_memory_tracking and self.memory_engine:
            similar_contexts = self.memory_engine.retrieve({
                "context.time_of_day": context.get("time_of_day"),
                "context.user_emotion": context.get("user_emotion")
            })
            
            if similar_contexts:
                # Analyze successful responses in similar contexts
                successful_mods = []
                for entry in similar_contexts:
                    if entry["feedback"].get("effectiveness", 0) >= 0.8:
                        successful_mods.append(entry["feedback"].get("modifiers", {}))
                
                if successful_mods:
                    # Average the successful modifiers
                    for mod in successful_mods:
                        for key in modifiers:
                            if key in mod:
                                modifiers[key] *= mod[key]
                    
                    # Normalize the averaged modifiers
                    mod_count = len(successful_mods)
                    for key in modifiers:
                        modifiers[key] = (modifiers[key] ** (1/mod_count))
        
        # Apply standard context modifications
        time_of_day = context.get("time_of_day", "").lower()
        if time_of_day == "morning":
            modifiers["energy"] = 1.1
        elif time_of_day == "night":
            modifiers["energy"] = 0.9
            
        # Topic-based modifications
        topic = context.get("conversation_topic", "").lower()
        if "emergency" in topic:
            modifiers["speed"] = 1.15
            modifiers["intensity"] = 1.2
        elif "technical" in topic:
            modifiers["speed"] = 0.95
            
        # User emotion response
        user_emotion = context.get("user_emotion", "").lower()
        if user_emotion in ["angry", "frustrated"]:
            modifiers["pitch"] *= 0.9  # Lower pitch for calming
            modifiers["speed"] *= 0.9  # Slower speed for clarity
            
        return modifiers

    def bind_enhanced_traits(self, tone: str, emotion_range: List[str],
                           memory_persistence: bool = True,
                           command_mode: bool = True) -> None:
        """
        Bind enhanced personality traits to the persona.
        
        Args:
            tone: Base tone for the voice
            emotion_range: List of supported emotional states
            memory_persistence: Whether to maintain conversation memory
            command_mode: Whether to support command-style interactions
        """
        from .config import CONFIG
        
        profile = CONFIG["voice_profiles"].get(self.name.lower())
        if not profile:
            logger.warning(f"No profile configuration found for {self.name}")
            return
            
        # Apply tone modulation
        if tone in profile["tone_modulation"]:
            mods = profile["tone_modulation"][tone]
            self.pitch *= mods["pitch"]
            self.speed *= mods["speed"]
            
        # Update emotion profiles based on range
        for emotion in emotion_range:
            if emotion not in self.emotion_profiles:
                # Create new emotion profile with default values
                self.emotion_profiles[EmotionType[emotion.upper()]] = EmotionProfile(
                    emotion=EmotionType[emotion.upper()],
                    pitch_modifier=1.0,
                    speed_modifier=1.0,
                    intensity=1.0
                )
        
        # Configure adaptation settings
        if memory_persistence and "adaptation_settings" in profile:
            self.adaptation_threshold = profile["adaptation_settings"]["learning_rate"]
            
        # Set up context weights if available
        if "context_weights" in profile:
            self._context_weights = profile["context_weights"]
            
        logger.info(f"Enhanced traits bound to {self.name}: tone={tone}, "
                   f"emotions={len(emotion_range)}, memory={memory_persistence}")

    def enable_voice(self, voice_name: Optional[str] = None):
        """Enable voice output for this persona."""
        try:
            self.voice_engine = VoiceEngine(voice_name or self.name)
            logger.info(f"Voice output enabled for {self.name}")
        except Exception as e:
            logger.error(f"Failed to enable voice for {self.name}: {str(e)}")
            
    def speak(self, message: str, emotion: Optional[EmotionType] = None, 
             context: Optional[Dict[str, Any]] = None):
        """
        Speak a message with appropriate emotional modulation.
        
        Args:
            message: Text to speak
            emotion: Optional emotion to apply
            context: Optional context for modulation
        """
        if not self.voice_engine:
            logger.warning(f"Voice not enabled for {self.name}. Call enable_voice() first.")
            return
            
        try:
            # Get emotion and context modifiers
            modifiers = self.get_context_modifier(context or {})
            if emotion and emotion in self.emotion_profiles:
                emotion_profile = self.emotion_profiles[emotion]
                modifiers["pitch"] *= emotion_profile.pitch_modifier
                modifiers["speed"] *= emotion_profile.speed_modifier
                modifiers["volume"] = emotion_profile.intensity
                
            # Speak with modulation
            self.voice_engine.speak(message, modifiers)
            
            # Record the interaction
            self.record_interaction(message, emotion or EmotionType.NEUTRAL, context)
            
        except Exception as e:
            logger.error(f"Failed to speak message: {str(e)}")

class VoicePersonaManager:
    def __init__(self):
        self.personas: Dict[str, VoicePersona] = {}
        self.default_persona: Optional[str] = None
        self.last_used_persona: Optional[str] = None
        self.interaction_count: Dict[str, int] = {}
        self._initialize_default_personas()

    def _initialize_default_personas(self):
        """Initialize the default set of voice personas with enhanced characteristics."""
        # Samantha - Natural and adaptable
        self.add_persona(VoicePersona(
            name="Samantha",
            style=VoiceStyle.NATURAL,
            pitch=1.0,
            speed=1.0,
            description="Default, natural tone",
            catchphrases=[
                "I'd be happy to help with that.",
                "Let me assist you.",
                "How can I make this easier for you?"
            ]
        ))

        # Commander - Authoritative and precise
        commander = VoicePersona(
            name="Commander",
            style=VoiceStyle.ASSERTIVE,
            pitch=0.9,
            speed=1.1,
            description="Assertive, mission-oriented",
            catchphrases=[
                "Status report received.",
                "Mission parameters acknowledged.",
                "Proceeding with operation."
            ]
        )
        commander.emotion_profiles[EmotionType.SERIOUS].intensity = 1.5
        commander.emotion_profiles[EmotionType.EXCITED].speed_modifier = 1.15
        self.add_persona(commander)

        # HumorBot - Dynamic and entertaining
        humorbot = VoicePersona(
            name="HumorBot",
            style=VoiceStyle.CASUAL,
            pitch=1.1,
            speed=1.05,
            description="Casual, lighthearted",
            catchphrases=[
                "Here's a fun fact!",
                "Time for some AI humor!",
                "Let's keep it light and fun!"
            ]
        )
        humorbot.emotion_profiles[EmotionType.PLAYFUL].intensity = 1.4
        humorbot.emotion_profiles[EmotionType.HAPPY].pitch_modifier = 1.2
        self.add_persona(humorbot)

    def add_persona(self, persona: VoicePersona) -> None:
        """Add a new voice persona to the manager."""
        try:
            # Validate persona before adding
            if not isinstance(persona, VoicePersona):
                raise TypeError("Must provide a VoicePersona instance")
                
            self.personas[persona.name] = persona
            self.interaction_count[persona.name] = 0
            logger.info(f"Added voice persona: {persona.name} ({persona.description})")
            
        except Exception as e:
            logger.error(f"Failed to add persona {persona.name}: {str(e)}")
            raise

    def get_persona(self, name: str) -> Optional[VoicePersona]:
        """
        Get a voice persona by name.
        
        Args:
            name: Name of the persona to retrieve
            
        Returns:
            VoicePersona if found, None otherwise
        """
        return self.personas.get(name)

    def set_default(self, name: str) -> bool:
        """
        Set the default voice persona.
        
        Args:
            name: Name of the persona to set as default
            
        Returns:
            True if successful, False if persona not found
        """
        if name in self.personas:
            self.default_persona = name
            logger.info(f"Set default voice persona to: {name}")
            return True
        logger.warning(f"Could not set default persona - {name} not found")
        return False

    def get_default_persona(self) -> Optional[VoicePersona]:
        """
        Get the current default persona.
        
        Returns:
            Default VoicePersona if set, None otherwise
        """
        if self.default_persona:
            return self.personas.get(self.default_persona)
        return None

    def bind_all_personas(self) -> None:
        """
        Bind all personas to the voice system.
        This ensures all personas are properly initialized and ready for use.
        """
        for name, persona in self.personas.items():
            logger.info(f"Binding voice persona: {name}")
            # Here you could add additional initialization logic
            # such as loading voice models, etc.

    def bind_voice_persona(self, name: str, tone: str, emotion_range: List[str],
                          memory_persistence: bool = True,
                          command_mode: bool = True) -> None:
        """
        Bind enhanced capabilities to a voice persona.
        
        Args:
            name: Name of the persona to enhance
            tone: Base tone for the voice
            emotion_range: List of supported emotional states
            memory_persistence: Whether to maintain conversation memory
            command_mode: Whether to support command-style interactions
        """
        persona = self.get_persona(name)
        if not persona:
            logger.error(f"Cannot bind traits - persona {name} not found")
            return
            
        persona.bind_enhanced_traits(
            tone=tone,
            emotion_range=emotion_range,
            memory_persistence=memory_persistence,
            command_mode=command_mode
        )
        
        # Update interaction tracking
        self.interaction_count[name] = 0
        logger.info(f"Enhanced capabilities bound to {name}")

    def get_profile(self, name: Optional[str] = None, emotion: Optional[EmotionType] = None,
                   context: Optional[Dict] = None) -> Dict:
        """Get the voice profile with emotion and context modifications."""
        persona = self.get_persona(name) if name else self.get_default_persona()
        if not persona:
            return {"pitch": 1.0, "speed": 1.0, "style": VoiceStyle.NATURAL.value}
        
        # Track usage
        self.last_used_persona = persona.name
        self.interaction_count[persona.name] = self.interaction_count.get(persona.name, 0) + 1
        
        # Get base profile
        base_profile = {
            "pitch": persona.pitch,
            "speed": persona.speed,
            "style": persona.style.value
        }
        
        # Apply emotion modifications
        if emotion and emotion in persona.emotion_profiles:
            emotion_profile = persona.emotion_profiles[emotion]
            base_profile["pitch"] *= emotion_profile.pitch_modifier
            base_profile["speed"] *= emotion_profile.speed_modifier
            base_profile["emotion_intensity"] = emotion_profile.intensity
        
        # Apply context modifications
        if context:
            context_modifiers = persona.get_context_modifier(context)
            base_profile["pitch"] *= context_modifiers["pitch"]
            base_profile["speed"] *= context_modifiers["speed"]
            
        # Record the interaction
        if emotion:
            persona.record_interaction(
                message=f"Profile request: {emotion.name}",
                emotion=emotion,
                context=context
            )
            
        return base_profile

    def save_state(self, filepath: str) -> None:
        """Save the current state of all personas."""
        try:
            state = {
                "default_persona": self.default_persona,
                "last_used_persona": self.last_used_persona,
                "interaction_counts": self.interaction_count,
                "personas": {
                    name: {
                        "style": persona.style.value,
                        "pitch": persona.pitch,
                        "speed": persona.speed,
                        "description": persona.description,
                        "context_awareness": persona.context_awareness,
                        "adaptation_threshold": persona.adaptation_threshold,
                        "catchphrases": persona.catchphrases
                    }
                    for name, persona in self.personas.items()
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Saved persona manager state to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")
            raise

    def load_state(self, filepath: str) -> None:
        """Load a previously saved state."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.default_persona = state["default_persona"]
            self.last_used_persona = state["last_used_persona"]
            self.interaction_count = state["interaction_counts"]
            
            # Recreate personas with saved state
            for name, data in state["personas"].items():
                persona = VoicePersona(
                    name=name,
                    style=VoiceStyle(data["style"]),
                    pitch=data["pitch"],
                    speed=data["speed"],
                    description=data["description"],
                    context_awareness=data["context_awareness"],
                    adaptation_threshold=data["adaptation_threshold"],
                    catchphrases=data["catchphrases"]
                )
                self.personas[name] = persona
                
            logger.info(f"Loaded persona manager state from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load state: {str(e)}")
            raise 