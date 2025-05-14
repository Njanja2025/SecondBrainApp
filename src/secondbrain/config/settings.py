"""
settings.py - Configuration loader for SecondBrainApp
"""

def load_config():
    """Return a default config dictionary for the Baddy agent."""
    return {
        "agent_name": "Baddy",
        "challenge_difficulty": "medium",
        "logging": {
            "level": "INFO"
        }
    } 