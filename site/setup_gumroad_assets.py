"""
Setup Gumroad assets for AI Business Starter Pack deployment
"""
import os
import shutil
import logging
from pathlib import Path
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GumroadAssetManager:
    def __init__(self, base_dir="site/gumroad"):
        """Initialize the Gumroad asset manager."""
        self.base_dir = base_dir
        self.assets_dir = os.path.join(base_dir, "assets")
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.assets_dir, exist_ok=True)
        
    def copy_mockup_image(self, source_path: str, destination_name: str = "cover_mockup.jpg") -> str:
        """Copy and optimize mockup image for Gumroad."""
        try:
            # Set destination path
            destination_path = os.path.join(self.assets_dir, destination_name)
            
            # Copy the file
            logger.info(f"Copying mockup image from {source_path} to {destination_path}")
            shutil.copy2(source_path, destination_path)
            
            # Optimize image for web
            self.optimize_image(destination_path)
            
            logger.info(f"Mockup image copied and optimized successfully")
            return destination_path
            
        except Exception as e:
            logger.error(f"Failed to copy mockup image: {e}")
            raise
            
    def optimize_image(self, image_path: str):
        """Optimize image for web delivery."""
        try:
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                    
                # Resize if too large (max 2000px on longest side)
                max_size = 2000
                if max(img.size) > max_size:
                    ratio = max_size / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                # Save optimized image
                img.save(
                    image_path,
                    'JPEG',
                    quality=85,
                    optimize=True
                )
                
            logger.info(f"Image optimized: {image_path}")
            
        except Exception as e:
            logger.error(f"Failed to optimize image: {e}")
            raise
            
    def setup_product_assets(self):
        """Setup all product assets for Gumroad."""
        try:
            # Create product directory
            product_dir = os.path.join(self.assets_dir, "ai_starter_pack")
            os.makedirs(product_dir, exist_ok=True)
            
            # Copy voice-over
            voice_over_path = "site/voice_scripts/ai_starter_pack_pitch.mp3"
            if os.path.exists(voice_over_path):
                shutil.copy2(
                    voice_over_path,
                    os.path.join(product_dir, "product_intro.mp3")
                )
                
            # Copy product files
            product_files = [
                "NjanjaStorefront_Package.zip",
                "README.md",
                "LICENSE"
            ]
            
            for file in product_files:
                if os.path.exists(file):
                    shutil.copy2(
                        file,
                        os.path.join(product_dir, file)
                    )
                    
            logger.info("Product assets setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup product assets: {e}")
            raise

def main():
    """Setup Gumroad assets for deployment."""
    try:
        # Initialize asset manager
        manager = GumroadAssetManager()
        
        # Copy mockup image
        source_mockup = "site/assets/cover_mockup.png"  # Updated path
        if os.path.exists(source_mockup):
            mockup_path = manager.copy_mockup_image(source_mockup)
            print(f"\nMockup image copied to: {mockup_path}")
        else:
            logger.warning(f"Source mockup not found: {source_mockup}")
            print("\nPlease place your mockup image at: site/assets/cover_mockup.png")
            
        # Setup product assets
        manager.setup_product_assets()
        
        print("\nGumroad assets setup completed!")
        print("\nNext steps:")
        print("1. Review the assets in site/gumroad/assets")
        print("2. Update product.json if needed")
        print("3. Upload to Gumroad")
        
    except Exception as e:
        logger.error(f"Failed to setup Gumroad assets: {e}")
        raise

if __name__ == '__main__':
    main() 