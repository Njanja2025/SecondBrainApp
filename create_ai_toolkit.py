"""
Script to create the AI Toolkit zip package
"""

import os
import zipfile
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_placeholder_files(temp_dir: Path) -> dict:
    """
    Create placeholder files for the toolkit.

    Args:
        temp_dir: Directory to create files in

    Returns:
        dict: Mapping of filenames to their content
    """
    files_to_create = {
        "AI_Toolkit_ReadMe.txt": f"""Welcome to The AI Toolkit!

This toolkit contains prompts, strategies, and setup guides for digital product creation using AI.

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Contents:
1. Bonus Prompts PDF - Collection of advanced AI prompts
2. Product Cover - Professional cover image for your digital products

For support or questions, please contact: support@example.com

Enjoy creating amazing digital products with AI!
""",
        "Bonus_Prompts.pdf": """This is a placeholder for bonus prompts PDF.
Replace with the final version when ready.

The final PDF will contain:
- Advanced prompt engineering techniques
- Industry-specific prompt templates
- Best practices for AI product creation
- Case studies and examples
""",
        "Product_Cover.png": """This is a placeholder for the product cover image.
Replace with your final graphic.

The final image should be:
- High resolution (at least 2000x2000 pixels)
- Professional design
- Branded with your logo
- Suitable for digital product marketplaces
""",
    }

    # Create files
    for filename, content in files_to_create.items():
        file_path = temp_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Created placeholder file: {filename}")

    return files_to_create


def create_toolkit_zip(output_path: str) -> bool:
    """
    Create the AI Toolkit zip package.

    Args:
        output_path: Path where the zip file should be created

    Returns:
        bool: True if successful
    """
    try:
        # Create temporary directory
        temp_dir = Path("temp_toolkit")
        temp_dir.mkdir(exist_ok=True)

        # Create placeholder files
        files_to_create = create_placeholder_files(temp_dir)

        # Create zip file
        zip_path = Path(output_path)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename in files_to_create.keys():
                file_path = temp_dir / filename
                zipf.write(file_path, arcname=filename)
                logger.info(f"Added {filename} to zip")

        # Clean up temporary directory
        for file in temp_dir.glob("*"):
            file.unlink()
        temp_dir.rmdir()

        logger.info(f"Successfully created toolkit zip at: {zip_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create toolkit zip: {e}")
        return False


def main():
    """Main function to create the toolkit."""
    # Define output path
    output_path = "AI_Toolkit_Complete_Pack.zip"

    # Create toolkit
    if create_toolkit_zip(output_path):
        print(f"\nToolkit created successfully at: {output_path}")
        print("\nContents:")
        with zipfile.ZipFile(output_path, "r") as zipf:
            for file in zipf.namelist():
                print(f"- {file}")
    else:
        print("\nFailed to create toolkit. Check the logs for details.")


if __name__ == "__main__":
    main()
