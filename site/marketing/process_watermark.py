"""
Process and optimize watermark image for marketing materials
"""
import os
import logging
from PIL import Image
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_watermark(input_path: str, output_path: str, size: tuple = (150, 150)) -> str:
    """
    Process watermark image with proper error handling and optimization.
    
    Args:
        input_path: Path to input image
        output_path: Path to save processed image
        size: Target size as (width, height)
        
    Returns:
        str: Path to processed image
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Open and process image
        with Image.open(input_path) as img:
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            # Resize image
            img_resized = img.resize(size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img_resized.save(
                output_path,
                format='PNG',
                optimize=True,
                quality=95
            )
            
        logger.info(f"Successfully processed watermark: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to process watermark: {e}")
        raise

def main():
    """Process watermark image for marketing materials."""
    try:
        # Define paths
        base_dir = Path("site/marketing/assets")
        input_path = base_dir / "A_YouTube_channel_watermark_image_features_a_logo_.png"
        output_path = base_dir / "Njanja_Watermark_150x150.png"
        
        # Process watermark
        processed_path = process_watermark(
            str(input_path),
            str(output_path),
            size=(150, 150)
        )
        
        print(f"\nWatermark processed successfully: {processed_path}")
        print("\nNext steps:")
        print("1. Verify the watermark in marketing materials")
        print("2. Update video templates with new watermark")
        print("3. Test watermark visibility on different backgrounds")
        
    except Exception as e:
        logger.error(f"Failed to process watermark: {e}")
        raise

if __name__ == '__main__':
    main() 