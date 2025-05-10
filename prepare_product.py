"""
Script to prepare the AI Business Starter Pack for Gumroad/Payhip upload
"""
import os
import shutil
import zipfile
from pathlib import Path
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_product_zip(product_dir: str, output_file: str) -> bool:
    """
    Create a zip file of the product for upload.
    
    Args:
        product_dir: Path to product directory
        output_file: Path to output zip file
        
    Returns:
        bool: True if successful
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create zip file
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from product directory
            for root, _, files in os.walk(product_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, product_dir)
                    zipf.write(file_path, arcname)
                    logger.info(f"Added {arcname} to zip")
                    
        logger.info(f"Created product zip: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create product zip: {e}")
        return False

def create_upload_ready_files(product_dir: str) -> bool:
    """
    Create upload-ready files for Gumroad/Payhip.
    
    Args:
        product_dir: Path to product directory
        
    Returns:
        bool: True if successful
    """
    try:
        # Create upload directory
        upload_dir = Path("upload_ready")
        upload_dir.mkdir(exist_ok=True)
        
        # Copy and rename files
        files_to_copy = {
            "description.md": "product_description.md",
            "price.txt": "price.txt",
            "assets/cover_mockup.jpg": "cover.jpg",
            "assets/templates.zip": "templates.zip",
            "voice_scripts/homepage_intro.mp3": "assets/homepage_intro.mp3"
        }
        
        # Track successful copies
        successful_copies = []
        
        for src, dst in files_to_copy.items():
            src_path = Path(product_dir) / src
            dst_path = upload_dir / dst
            
            # Create parent directories if they don't exist
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                logger.info(f"Copied {src} to {dst}")
                successful_copies.append(dst)
            else:
                logger.warning(f"Source file not found: {src}")
                
        # Create metadata file
        metadata = {
            "product_name": "AI Business Starter Pack",
            "price": "ZAR 499.00",
            "created_at": datetime.now().isoformat(),
            "files": successful_copies,
            "version": "1.0.0",
            "platform": "macOS",
            "requirements": {
                "ffmpeg": "Optional - for MP3 conversion",
                "say": "Built-in macOS command"
            }
        }
        
        # Save metadata as pretty-printed JSON
        with open(upload_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info("Created upload-ready files")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create upload-ready files: {e}")
        return False

def verify_files(product_dir: str) -> bool:
    """
    Verify that all required files exist.
    
    Args:
        product_dir: Path to product directory
        
    Returns:
        bool: True if all required files exist
    """
    required_files = [
        "description.md",
        "price.txt",
        "assets/cover_mockup.jpg",
        "assets/templates.zip",
        "voice_scripts/homepage_intro.mp3"
    ]
    
    missing_files = []
    for file in required_files:
        if not (Path(product_dir) / file).exists():
            missing_files.append(file)
            
    if missing_files:
        logger.error("Missing required files:")
        for file in missing_files:
            logger.error(f"- {file}")
        return False
        
    return True

def main():
    """Main function to prepare product for upload."""
    # Define paths
    product_dir = "products/ai_business_starter_pack"
    zip_file = "upload_ready/ai_business_starter_pack.zip"
    
    # Verify required files
    if not verify_files(product_dir):
        print("\nMissing required files. Please ensure all files are present before proceeding.")
        return
    
    # Create upload-ready files
    if create_upload_ready_files(product_dir):
        print("\nCreated upload-ready files in 'upload_ready' directory")
        
        # Create product zip
        if create_product_zip(product_dir, zip_file):
            print(f"\nCreated product zip: {zip_file}")
            print("\nUpload-ready files:")
            for file in Path("upload_ready").glob("*"):
                print(f"- {file.name}")
                
            # Print next steps
            print("\nNext steps:")
            print("1. Review the files in the 'upload_ready' directory")
            print("2. Upload the files to Gumroad/Payhip")
            print("3. Test the product download and installation")
        else:
            print("\nFailed to create product zip. Check the logs for details.")
    else:
        print("\nFailed to create upload-ready files. Check the logs for details.")

if __name__ == "__main__":
    main() 