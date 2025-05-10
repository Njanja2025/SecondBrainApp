"""
Process and copy YouTube banner to Dropbox
"""
import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_banner(source_path: str, dest_dir: str, filename: str) -> str:
    """
    Process and copy banner image to destination directory.
    
    Args:
        source_path: Path to source banner image
        dest_dir: Destination directory path
        filename: Target filename
        
    Returns:
        str: Path to copied banner
    """
    try:
        # Ensure destination directory exists
        os.makedirs(dest_dir, exist_ok=True)
        
        # Define destination path
        dest_path = os.path.join(dest_dir, filename)
        
        # Copy banner
        shutil.copy(source_path, dest_path)
        
        logger.info(f"Successfully copied banner to: {dest_path}")
        return dest_path
        
    except Exception as e:
        logger.error(f"Failed to process banner: {e}")
        raise

def main():
    """Process and copy YouTube banner."""
    try:
        # Define paths
        source_banner = "site/marketing/assets/A_YouTube_banner_for_Njanja_AI_Empire_features_a.png"
        dropbox_dir = "site/marketing/dropbox/NjanjaBranding"
        dest_filename = "Njanja_YouTube_Banner.png"
        
        # Process banner
        banner_path = process_banner(
            source_banner,
            dropbox_dir,
            dest_filename
        )
        
        print(f"\nBanner processed successfully: {banner_path}")
        print("\nNext steps:")
        print("1. Verify the banner in Dropbox")
        print("2. Update YouTube channel with new banner")
        print("3. Test banner visibility on different devices")
        
    except Exception as e:
        logger.error(f"Failed to process banner: {e}")
        raise

if __name__ == '__main__':
    main() 