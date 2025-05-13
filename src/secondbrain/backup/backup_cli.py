"""
SecondBrain Backup CLI with voice integration.
"""
import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
import pyttsx3
from companion_journaling_backup import CompanionJournalingBackup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/secondbrain_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VoiceController:
    def __init__(self):
        self.voice_config = self._load_config('voice_config.json')
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', self.voice_config['voice_name'])
    
    def _load_config(self, config_file):
        config_path = Path(__file__).parent / config_file
        with open(config_path) as f:
            return json.load(f)
    
    def play_intro(self):
        """Play intro audio and announce start."""
        if self.voice_config['intro_enabled']:
            try:
                # Play intro audio
                audio_path = Path(self.voice_config['audio_file'])
                if audio_path.exists():
                    subprocess.run(["afplay", str(audio_path)])
                
                # Announce start
                self.engine.say(self.voice_config['intro_message'])
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"Error playing intro: {e}")
    
    def announce_success(self):
        """Announce successful backup."""
        if self.voice_config['voice_enabled']:
            try:
                self.engine.say(self.voice_config['confirmation_message'])
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"Error announcing success: {e}")
    
    def announce_error(self):
        """Announce backup error."""
        if self.voice_config['voice_enabled']:
            try:
                self.engine.say(self.voice_config['error_message'])
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"Error announcing error: {e}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='SecondBrain Backup CLI')
    parser.add_argument('--auto', action='store_true', help='Run backup automatically')
    parser.add_argument('--verify', action='store_true', help='Verify backup after completion')
    return parser.parse_args()

def main():
    """Run the backup process with voice integration."""
    args = parse_args()
    voice = VoiceController()
    
    try:
        # Play intro
        voice.play_intro()
        
        # Run backup
        backup = CompanionJournalingBackup()
        result = backup.create_backup()
        
        if result['status'] == 'success':
            voice.announce_success()
            logger.info("Backup completed successfully")
            
            if args.verify:
                # Run verification
                from vault_verifier import verify_latest_backup
                verify_latest_backup()
        else:
            voice.announce_error()
            logger.error(f"Backup failed: {result['message']}")
            return 1
            
    except Exception as e:
        voice.announce_error()
        logger.error(f"Error during backup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 