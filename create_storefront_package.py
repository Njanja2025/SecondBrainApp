"""
Script to create the complete Njanja Storefront package
"""
import os
import zipfile
import shutil
from pathlib import Path
import logging
import subprocess
import platform
from datetime import datetime
import json
from PIL import Image, ImageDraw, ImageFont
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory_structure(base_dir: str) -> None:
    """Create the required directory structure."""
    directories = [
        "voice_scripts",
        "products/ai_business_starter_pack/assets",
        "upload_ready",
        "docs"
    ]
    
    for directory in directories:
        path = os.path.join(base_dir, directory)
        os.makedirs(path, exist_ok=True)
        logger.info(f"Created directory: {path}")

def create_voice_script(base_dir: str) -> None:
    """Create the voice script file."""
    script_path = os.path.join(base_dir, "voice_scripts/homepage_intro.txt")
    content = """Welcome to Thekgano — your gateway to the future of digital innovation.
We build and deliver AI-powered solutions, from automation tools to eBooks, templates, and marketing assets.
Let's get started on your transformation journey."""
    
    with open(script_path, "w") as f:
        f.write(content)
    logger.info(f"Created voice script: {script_path}")

def create_product_files(base_dir: str) -> None:
    """Create product description and price files."""
    product_dir = os.path.join(base_dir, "products/ai_business_starter_pack")
    
    # Create description.md
    description_path = os.path.join(product_dir, "description.md")
    description_content = """## AI Business Starter Pack

Everything you need to launch your digital business:
- AI automation tool
- Editable eBook
- Marketing templates

Delivered instantly after checkout."""
    
    with open(description_path, "w") as f:
        f.write(description_content)
    logger.info(f"Created description: {description_path}")
    
    # Create price.txt
    price_path = os.path.join(product_dir, "price.txt")
    with open(price_path, "w") as f:
        f.write("ZAR 499.00")
    logger.info(f"Created price file: {price_path}")

def create_checkout_file(base_dir: str) -> None:
    """Create the Paystack test checkout HTML file."""
    checkout_path = os.path.join(base_dir, "paystack_test_checkout.html")
    checkout_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Test Paystack Checkout</title>
  <script src="https://js.paystack.co/v1/inline.js"></script>
</head>
<body>
  <h2>Pay with Paystack (Test Mode)</h2>
  <button onclick="payWithPaystack()">Pay Now</button>
  <script>
    function payWithPaystack() {
      var handler = PaystackPop.setup({
        key: 'pk_test_702e2471b3b9dd34fb6c',
        email: 'testuser@njanja.net',
        amount: 500000,
        currency: 'ZAR',
        callback: function(response) {
          alert('Payment successful. Ref: ' + response.reference);
        },
        onClose: function() {
          alert('Payment cancelled');
        }
      });
      handler.openIframe();
    }
  </script>
</body>
</html>"""
    
    with open(checkout_path, "w") as f:
        f.write(checkout_content)
    logger.info(f"Created checkout file: {checkout_path}")

def create_cover_mockup(base_dir: str) -> bool:
    """Create a product cover mockup image."""
    try:
        # Create a new image with a gradient background
        width, height = 1200, 800
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Draw gradient background
        for y in range(height):
            r = int(255 * (1 - y/height))
            g = int(200 * (1 - y/height))
            b = int(255 * (1 - y/height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add text
        try:
            font = ImageFont.truetype("Arial", 60)
            small_font = ImageFont.truetype("Arial", 30)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw title
        title = "AI Business Starter Pack"
        title_bbox = draw.textbbox((0, 0), title, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, 200), title, fill='white', font=font)
        
        # Draw subtitle
        subtitle = "Your Gateway to Digital Success"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=small_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (width - subtitle_width) // 2
        draw.text((subtitle_x, 300), subtitle, fill='white', font=small_font)
        
        # Save the image
        cover_path = os.path.join(base_dir, "products/ai_business_starter_pack/assets/cover_mockup.jpg")
        image.save(cover_path, quality=95)
        logger.info(f"Created cover mockup: {cover_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create cover mockup: {e}")
        return False

def create_readme(base_dir: str) -> None:
    """Create a README file with setup instructions."""
    readme_path = os.path.join(base_dir, "README.md")
    readme_content = """# Njanja Storefront Package

## Overview
This package contains everything you need to set up your digital storefront, including:
- AI Business Starter Pack product files
- Voice-over scripts and audio
- Paystack test checkout integration

## Directory Structure
```
storefront/
├── docs/                    # Documentation
├── products/               # Product files
│   └── ai_business_starter_pack/
│       ├── assets/        # Product assets
│       ├── description.md # Product description
│       └── price.txt     # Product pricing
├── voice_scripts/         # Voice-over scripts
└── paystack_test_checkout.html
```

## Setup Instructions

### 1. Voice-over Generation
The package includes a script to generate voice-overs using macOS's built-in `say` command:
```bash
python generate_voiceover.py
```

### 2. Product Setup
1. Review and customize the product description in `products/ai_business_starter_pack/description.md`
2. Update pricing in `products/ai_business_starter_pack/price.txt`
3. Customize the cover mockup in `products/ai_business_starter_pack/assets/cover_mockup.jpg`

### 3. Payment Integration
1. Update the Paystack test key in `paystack_test_checkout.html`
2. Test the checkout process using the test mode
3. Replace with production key when ready

## Requirements
- macOS for voice-over generation
- ffmpeg (optional) for MP3 conversion
- Python 3.6+

## Support
For support, contact support@njanja.net
"""
    
    with open(readme_path, "w") as f:
        f.write(readme_content)
    logger.info(f"Created README: {readme_path}")

def generate_voiceover(base_dir: str) -> bool:
    """Generate voice-over using macOS say command."""
    try:
        if platform.system() != 'Darwin':
            logger.error("Voice generation requires macOS")
            return False
            
        text_file = os.path.join(base_dir, "voice_scripts/homepage_intro.txt")
        output_file = os.path.join(base_dir, "voice_scripts/homepage_intro.mp3")
        
        # Generate temporary AIFF file
        temp_aiff = output_file.replace('.mp3', '.aiff')
        
        # Generate voice using say command
        say_cmd = ['say', '-v', 'Samantha', '-o', temp_aiff, '-f', text_file]
        subprocess.run(say_cmd, check=True)
        
        # Convert to MP3 if ffmpeg is available
        try:
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', temp_aiff,
                '-codec:a', 'libmp3lame', '-qscale:a', '2',
                output_file
            ]
            subprocess.run(ffmpeg_cmd, check=True)
            os.remove(temp_aiff)
        except (subprocess.SubprocessError, FileNotFoundError):
            # If ffmpeg is not available, just rename the AIFF file
            os.rename(temp_aiff, output_file)
            logger.warning("ffmpeg not found. Using AIFF format instead of MP3.")
        
        logger.info(f"Generated voice-over: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate voice-over: {e}")
        return False

def create_package_zip(base_dir: str, output_zip: str) -> bool:
    """Create the final package zip file."""
    try:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for foldername, _, filenames in os.walk(base_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, base_dir)
                    zipf.write(file_path, arcname)
                    logger.info(f"Added to zip: {arcname}")
        
        logger.info(f"Created package: {output_zip}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create package: {e}")
        return False

def main():
    """Main function to create the complete package."""
    # Define base directory
    base_dir = os.path.abspath("storefront")
    output_zip = "NjanjaStorefront_Package.zip"
    
    try:
        # Create directory structure
        create_directory_structure(base_dir)
        
        # Create content files
        create_voice_script(base_dir)
        create_product_files(base_dir)
        create_checkout_file(base_dir)
        create_readme(base_dir)
        
        # Create cover mockup
        if create_cover_mockup(base_dir):
            print("\nCover mockup created successfully")
        else:
            print("\nFailed to create cover mockup")
        
        # Generate voice-over
        if generate_voiceover(base_dir):
            print("\nVoice-over generated successfully")
        else:
            print("\nFailed to generate voice-over")
        
        # Create package zip
        if create_package_zip(base_dir, output_zip):
            print(f"\nPackage created successfully: {output_zip}")
            print("\nPackage contents:")
            with zipfile.ZipFile(output_zip, 'r') as zipf:
                for file in zipf.namelist():
                    print(f"- {file}")
                    
            # Print next steps
            print("\nNext steps:")
            print("1. Review the files in the 'storefront' directory")
            print("2. Customize the product description and pricing")
            print("3. Test the Paystack checkout integration")
            print("4. Upload the package to your hosting platform")
        else:
            print("\nFailed to create package")
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("\nFailed to create package. Check the logs for details.")

if __name__ == "__main__":
    main() 