"""
Voice enhancement module for SecondBrain.
"""
import logging
import os
from typing import Dict, Optional, Any
from pathlib import Path

from ..phantom.phantom_core import PhantomCore
from .voice_modulator import VoiceModulator
from .voice_persona import VoicePersonaManager, EmotionType

logger = logging.getLogger(__name__)

class VoiceEnhancer:
    def __init__(self, state_dir: Optional[str] = None):
        self.phantom = PhantomCore()
        self.modulator = VoiceModulator()
        self.persona_manager = VoicePersonaManager()
        self.state_dir = state_dir or os.path.join(os.path.dirname(__file__), "state")
        self.state_file = os.path.join(self.state_dir, "voice_personas.json")

    async def initialize(self):
        """
        Initialize the voice enhancer and load previous state if available.
        """
        logger.info("Initializing voice enhancer...")
        
        # Create state directory if it doesn't exist
        os.makedirs(self.state_dir, exist_ok=True)
        
        # Try to load previous state
        try:
            if os.path.exists(self.state_file):
                self.persona_manager.load_state(self.state_file)
            else:
                self.persona_manager.set_default("Samantha")
        except Exception as e:
            logger.warning(f"Could not load previous state: {str(e)}")
            self.persona_manager.set_default("Samantha")
        
        await self.modulator.initialize()
        self.persona_manager.bind_all_personas()
        return True

    def enhance_voice(
        self,
        text: str,
        persona_name: Optional[str] = None,
        emotion: Optional[EmotionType] = None,
        context: Optional[Dict[str, Any]] = None,
        save_state: bool = True
    ) -> Dict[str, str]:
        """
        Enhance the given text using phantom logic and voice modulation.
        
        Args:
            text: Text to enhance
            persona_name: Optional name of persona to use, uses default if None
            emotion: Optional emotion to apply to the voice
            context: Optional context information for more natural responses
            save_state: Whether to save the persona state after enhancement
            
        Returns:
            Dict containing original and enhanced text
        """
        try:
            logger.info(f"Enhancing voice for text: {text}")
            
            # Get voice profile from persona manager with emotion and context
            profile = self.persona_manager.get_profile(
                name=persona_name,
                emotion=emotion,
                context=context
            )
            
            # Apply modulation effects
            modulated_text = self.modulator.modulate(text, profile)
            
            # Save state if requested
            if save_state:
                try:
                    self.persona_manager.save_state(self.state_file)
                except Exception as e:
                    logger.warning(f"Failed to save persona state: {str(e)}")
            
            return {
                "original": text,
                "enhanced": modulated_text,
                "profile_used": profile
            }
            
        except Exception as e:
            logger.error(f"Voice enhancement failed: {str(e)}")
            return {
                "original": text,
                "enhanced": text,  # Return original text on failure
                "error": str(e)
            }

    def rate_response(self, text: str, rating: float, persona_name: Optional[str] = None) -> None:
        """
        Rate a previous response to help personas adapt.
        
        Args:
            text: The text that was enhanced
            rating: Rating between 0.0 and 1.0
            persona_name: Optional name of persona to rate, uses last used if None
        """
        try:
            if not persona_name:
                persona_name = self.persona_manager.last_used_persona
            
            if persona_name:
                persona = self.persona_manager.get_persona(persona_name)
                if persona:
                    persona.rate_response(text, rating)
                    # Save state after rating
                    self.persona_manager.save_state(self.state_file)
                    
        except Exception as e:
            logger.error(f"Failed to rate response: {str(e)}")

    def get_persona_stats(self) -> Dict[str, Any]:
        """
        Get statistics about persona usage and performance.
        
        Returns:
            Dict containing persona statistics
        """
        stats = {
            "total_interactions": sum(self.persona_manager.interaction_count.values()),
            "default_persona": self.persona_manager.default_persona,
            "last_used": self.persona_manager.last_used_persona,
            "personas": {}
        }
        
        for name, persona in self.persona_manager.personas.items():
            interactions = self.persona_manager.interaction_count.get(name, 0)
            rated_interactions = sum(1 for h in persona.interaction_history if h.response_rating is not None)
            avg_rating = 0.0
            if rated_interactions > 0:
                ratings = [h.response_rating for h in persona.interaction_history if h.response_rating is not None]
                avg_rating = sum(ratings) / len(ratings)
            
            stats["personas"][name] = {
                "total_interactions": interactions,
                "rated_interactions": rated_interactions,
                "average_rating": round(avg_rating, 2),
                "style": persona.style.value
            }
        
        return stats 