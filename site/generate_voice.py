"""
Generate voice-over for AI Business Starter Pack using macOS say command
"""
import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceGenerator:
    def __init__(self, voice="Samantha", output_dir="site/voice_scripts"):
        """Initialize the voice generator."""
        self.voice = voice
        self.output_dir = output_dir
        self.ensure_output_directory()
        
    def ensure_output_directory(self):
        """Ensure output directory exists."""
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_voice(self, script_file: str, output_file: str = None) -> str:
        """Generate voice-over from script file."""
        try:
            # Read script
            with open(script_file, 'r') as f:
                script = f.read()
                
            # Set output file
            if not output_file:
                output_file = os.path.join(
                    self.output_dir,
                    f"{Path(script_file).stem}.aiff"
                )
                
            # Generate voice-over
            cmd = [
                'say',
                '-v', self.voice,
                '-o', output_file,
                script
            ]
            
            logger.info(f"Generating voice-over with voice: {self.voice}")
            subprocess.run(cmd, check=True)
            
            # Convert to MP3 if ffmpeg is available
            mp3_file = self.convert_to_mp3(output_file)
            
            logger.info(f"Voice-over generated successfully: {mp3_file}")
            return mp3_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate voice-over: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
            
    def convert_to_mp3(self, aiff_file: str) -> str:
        """Convert AIFF to MP3 using ffmpeg."""
        try:
            # Check if ffmpeg is installed
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("ffmpeg not found. Skipping MP3 conversion.")
                return aiff_file
                
            # Convert to MP3
            mp3_file = aiff_file.replace('.aiff', '.mp3')
            cmd = [
                'ffmpeg',
                '-i', aiff_file,
                '-codec:a', 'libmp3lame',
                '-qscale:a', '2',
                mp3_file
            ]
            
            logger.info("Converting to MP3...")
            subprocess.run(cmd, check=True)
            
            # Remove original AIFF file
            os.remove(aiff_file)
            
            return mp3_file
            
        except Exception as e:
            logger.error(f"Failed to convert to MP3: {e}")
            return aiff_file

def main():
    """Generate voice-over for AI Business Starter Pack."""
    try:
        # Initialize voice generator
        generator = VoiceGenerator()
        
        # Generate voice-over
        script_file = "site/voice_scripts/ai_starter_pack_pitch.txt"
        output_file = generator.generate_voice(script_file)
        
        print(f"\nVoice-over generated successfully!")
        print(f"Output file: {output_file}")
        print("\nNext steps:")
        print("1. Review the voice-over")
        print("2. Update the product listing if needed")
        print("3. Upload to Gumroad")
        
    except Exception as e:
        logger.error(f"Failed to generate voice-over: {e}")
        raise

if __name__ == '__main__':
    main() 