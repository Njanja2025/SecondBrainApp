"""
Base Character class for SecondBrainApp characters
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Character:
    """Base class for all characters in SecondBrainApp."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize base character."""
        self.config = config
        self.name = "Base"
        self.description = "Base character class"
        self.personality = {
            "traits": [],
            "mood": "neutral",
            "energy": 100
        }
        
    def interact(self, action: str, **kwargs) -> Dict[str, Any]:
        """Base interaction method to be overridden by subclasses."""
        logger.warning("Base interact method called - should be overridden by subclass")
        return {"status": "not_implemented"} 