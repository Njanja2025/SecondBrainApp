"""
Setup initial Gumroad directory structure
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

def setup_directory_structure():
    """Setup initial directory structure for Gumroad deployment."""
    try:
        # Create base directories
        directories = [
            "site/gumroad",
            "site/gumroad/assets",
            "site/gumroad/assets/ai_starter_pack",
            "site/gumroad/package"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
            
        # Create placeholder files
        placeholder_files = [
            "site/gumroad/assets/cover_mockup.jpg",
            "site/gumroad/assets/ai_starter_pack/product_intro.mp3",
            "site/gumroad/assets/ai_starter_pack/NjanjaStorefront_Package.zip",
            "site/gumroad/assets/ai_starter_pack/README.md",
            "site/gumroad/assets/ai_starter_pack/LICENSE"
        ]
        
        for file in placeholder_files:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    f.write("# Placeholder file\n")
                logger.info(f"Created placeholder file: {file}")
                
        print("\nDirectory structure setup completed!")
        print("\nNext steps:")
        print("1. Replace placeholder files with actual content")
        print("2. Run package_gumroad.py to create the deployment package")
        
    except Exception as e:
        logger.error(f"Failed to setup directory structure: {e}")
        raise

if __name__ == '__main__':
    setup_directory_structure() 