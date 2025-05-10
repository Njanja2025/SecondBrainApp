"""
Voice generation module for creating voice-overs and audio content
"""
import os
import logging
from pathlib import Path
from pydub.generators import Sine
from pydub import AudioSegment
import subprocess
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceGenerator:
    def __init__(self, config_path: str = "site/marketing/voice_config.json"):
        """Initialize the voice generator."""
        self.config_path = config_path
        self.config = self.load_config()
        self.output_dir = "site/marketing/assets/audio"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_config(self) -> dict:
        """Load voice configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load voice config: {e}")
            return {
                "voice": "Samantha",
                "rate": 175,
                "pitch": 50,
                "volume": 1.0
            }
            
    def generate_placeholder(self, duration: int = 60, frequency: int = 440) -> str:
        """Generate a placeholder audio track."""
        try:
            # Generate soft background tone
            background_music = Sine(frequency).to_audio_segment(duration=duration * 1000)
            background_music = background_music.apply_gain(-30)
            
            # Define output path
            output_path = os.path.join(self.output_dir, "placeholder.mp3")
            
            # Export audio
            background_music.export(output_path, format="mp3")
            
            logger.info(f"Generated placeholder audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate placeholder: {e}")
            raise
            
    def generate_voice_over(self, text: str, output_name: str) -> str:
        """Generate voice-over using macOS say command."""
        try:
            # Define output path
            output_path = os.path.join(self.output_dir, f"{output_name}.mp3")
            
            # Prepare say command
            cmd = [
                "say",
                "-v", self.config.get("voice", "Samantha"),
                "-r", str(self.config.get("rate", 175)),
                "-o", output_path,
                text
            ]
            
            # Execute command
            subprocess.run(cmd, check=True)
            
            logger.info(f"Generated voice-over: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate voice-over: {e}")
            raise
            
    def mix_audio(self, voice_path: str, background_path: str, output_name: str) -> str:
        """Mix voice-over with background music."""
        try:
            # Load audio files
            voice = AudioSegment.from_mp3(voice_path)
            background = AudioSegment.from_mp3(background_path)
            
            # Adjust background volume
            background = background.apply_gain(-20)
            
            # Mix audio
            mixed = voice.overlay(background)
            
            # Define output path
            output_path = os.path.join(self.output_dir, f"{output_name}_mixed.mp3")
            
            # Export mixed audio
            mixed.export(output_path, format="mp3")
            
            logger.info(f"Generated mixed audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to mix audio: {e}")
            raise
            
    def generate_social_media_audio(self, platform: str, content: str) -> str:
        """Generate audio content for social media platforms."""
        try:
            # Generate voice-over
            voice_path = self.generate_voice_over(
                content,
                f"{platform}_voice"
            )
            
            # Generate background
            background_path = self.generate_placeholder(
                duration=30,
                frequency=440
            )
            
            # Mix audio
            mixed_path = self.mix_audio(
                voice_path,
                background_path,
                f"{platform}_content"
            )
            
            return mixed_path
            
        except Exception as e:
            logger.error(f"Failed to generate social media audio: {e}")
            raise

def main():
    """Generate sample voice-overs."""
    try:
        # Initialize generator
        generator = VoiceGenerator()
        
        # Generate sample content
        sample_text = "Welcome to our AI Business Starter Pack. Transform your business with our comprehensive toolkit."
        
        # Generate for each platform
        platforms = ["linkedin", "twitter", "tiktok"]
        for platform in platforms:
            audio_path = generator.generate_social_media_audio(
                platform,
                sample_text
            )
            print(f"Generated {platform} audio: {audio_path}")
            
    except Exception as e:
        logger.error(f"Failed to generate sample audio: {e}")
        raise

if __name__ == '__main__':
    main() 