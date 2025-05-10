"""
Script to check for the launch guide PDF file
"""
import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_launch_guide():
    try:
        # Get the expected path of the launch guide
        home_dir = Path.home()
        pdf_path = home_dir / '.secondbrain' / 'docs' / 'launch_guide.pdf'
        
        # Check if file exists
        file_available = pdf_path.exists()
        
        if file_available:
            # Get file size and last modified time
            file_size = pdf_path.stat().st_size
            last_modified = pdf_path.stat().st_mtime
            
            print(f"\nLaunch Guide Status:")
            print(f"Path: {pdf_path}")
            print(f"Available: Yes")
            print(f"Size: {file_size:,} bytes")
            print(f"Last Modified: {last_modified}")
            
            # Verify file is readable
            try:
                with open(pdf_path, 'rb') as f:
                    # Read first few bytes to verify it's a PDF
                    header = f.read(5)
                    is_pdf = header.startswith(b'%PDF-')
                    print(f"Valid PDF: {'Yes' if is_pdf else 'No'}")
            except Exception as e:
                print(f"Error reading file: {e}")
                
        else:
            print(f"\nLaunch Guide not found at: {pdf_path}")
            print("Please run examples/generate_launch_guide.py to create the guide")
            
        return file_available
        
    except Exception as e:
        logger.error(f"Error checking launch guide: {e}")
        print(f"\nError: {e}")
        return False

if __name__ == "__main__":
    check_launch_guide() 