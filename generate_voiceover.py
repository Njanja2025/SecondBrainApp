"""
Script to generate Samantha's voice-over for the homepage intro using macOS's built-in say command
"""

import os
import subprocess
from pathlib import Path
import logging
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def generate_voiceover(text_file: str, output_file: str) -> bool:
    """
    Generate voice-over from text file using macOS's say command.

    Args:
        text_file: Path to text file
        output_file: Path to output MP3 file

    Returns:
        bool: True if successful
    """
    try:
        # Check if running on macOS
        if platform.system() != "Darwin":
            logger.error("This script requires macOS for the 'say' command")
            return False

        # Read text file
        with open(text_file, "r", encoding="utf-8") as f:
            text = f.read()

        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate temporary AIFF file
        temp_aiff = output_path.with_suffix(".aiff")

        # Generate voice using say command
        say_cmd = ["say", "-v", "Samantha", "-o", str(temp_aiff), text]
        subprocess.run(say_cmd, check=True)

        # Convert AIFF to MP3 using ffmpeg if available
        if check_ffmpeg():
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(temp_aiff),
                "-codec:a",
                "libmp3lame",
                "-qscale:a",
                "2",
                str(output_file),
            ]
            subprocess.run(ffmpeg_cmd, check=True)

            # Remove temporary AIFF file
            temp_aiff.unlink()
        else:
            # If ffmpeg is not available, just rename the AIFF file
            temp_aiff.rename(output_file)
            logger.warning("ffmpeg not found. Using AIFF format instead of MP3.")

        logger.info(f"Generated voice-over: {output_file}")
        return True

    except subprocess.SubprocessError as e:
        logger.error(f"Failed to generate voice-over: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to generate voice-over: {e}")
        return False


def main():
    """Main function to generate voice-over."""
    # Define paths
    text_file = "voice_scripts/homepage_intro.txt"
    output_file = "voice_scripts/homepage_intro.mp3"

    # Generate voice-over
    if generate_voiceover(text_file, output_file):
        print(f"\nVoice-over generated successfully at: {output_file}")
        print("\nFile details:")
        print(f"- Size: {Path(output_file).stat().st_size / 1024:.1f} KB")
        print(f"- Duration: ~{len(open(text_file).read().split()) * 0.3:.1f} seconds")

        if not check_ffmpeg():
            print("\nNote: ffmpeg not found. Install it for MP3 conversion:")
            print("brew install ffmpeg")
    else:
        print("\nFailed to generate voice-over. Check the logs for details.")


if __name__ == "__main__":
    main()
