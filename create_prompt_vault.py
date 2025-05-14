"""
Script to create the AI Prompt Vault zip package
"""

import os
import sys
import zipfile
import logging
import random
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PromptCategory(Enum):
    """Enum for prompt categories."""

    CONTENT = "Content Creation"
    BUSINESS = "Business"
    FREELANCING = "Freelancing"
    EDUCATION = "Education"
    CREATIVE = "Creative"


@dataclass
class PromptTemplate:
    """Data class for prompt templates."""

    template: str
    difficulty: str
    estimated_time: str
    monetization_potential: str
    target_audience: List[str]
    required_skills: List[str]


class PromptGenerator:
    """Class for generating and managing prompts."""

    def __init__(self):
        """Initialize prompt generator with templates."""
        self.templates = {
            PromptCategory.CONTENT: [
                PromptTemplate(
                    "Create a viral social media post about {topic}",
                    "Easy",
                    "15-30 minutes",
                    "High",
                    ["Social Media Managers", "Content Creators", "Marketers"],
                    ["Social Media", "Content Writing", "Marketing"],
                ),
                PromptTemplate(
                    "Write a blog post outline for {topic}",
                    "Medium",
                    "30-60 minutes",
                    "Medium",
                    ["Bloggers", "Content Writers", "SEO Specialists"],
                    ["Content Writing", "SEO", "Research"],
                ),
                PromptTemplate(
                    "Generate a YouTube video script about {topic}",
                    "Hard",
                    "1-2 hours",
                    "High",
                    ["YouTubers", "Video Creators", "Content Producers"],
                    ["Script Writing", "Video Production", "Storytelling"],
                ),
            ],
            PromptCategory.BUSINESS: [
                PromptTemplate(
                    "Write a business plan for {business_type}",
                    "Hard",
                    "2-4 hours",
                    "Very High",
                    ["Entrepreneurs", "Business Consultants", "Startup Founders"],
                    ["Business Planning", "Market Analysis", "Financial Planning"],
                ),
                PromptTemplate(
                    "Create a marketing strategy for {product}",
                    "Medium",
                    "1-2 hours",
                    "High",
                    ["Marketing Managers", "Business Owners", "Consultants"],
                    ["Marketing", "Strategy", "Market Research"],
                ),
            ],
            PromptCategory.FREELANCING: [
                PromptTemplate(
                    "Create a proposal for {project_type}",
                    "Medium",
                    "1-2 hours",
                    "High",
                    ["Freelancers", "Consultants", "Agency Owners"],
                    ["Proposal Writing", "Project Management", "Client Communication"],
                ),
                PromptTemplate(
                    "Write a cover letter for {job_type}",
                    "Easy",
                    "30-60 minutes",
                    "Medium",
                    ["Job Seekers", "Career Coaches", "HR Professionals"],
                    ["Resume Writing", "Professional Communication"],
                ),
            ],
            PromptCategory.EDUCATION: [
                PromptTemplate(
                    "Create a lesson plan for {subject}",
                    "Medium",
                    "1-2 hours",
                    "Medium",
                    ["Teachers", "Educators", "Tutors"],
                    ["Curriculum Design", "Teaching", "Subject Matter Expertise"],
                ),
                PromptTemplate(
                    "Write a quiz about {topic}",
                    "Easy",
                    "30-60 minutes",
                    "Low",
                    ["Teachers", "Content Creators", "Quiz Makers"],
                    ["Assessment Design", "Subject Matter Expertise"],
                ),
            ],
            PromptCategory.CREATIVE: [
                PromptTemplate(
                    "Write a story about {theme}",
                    "Hard",
                    "2-4 hours",
                    "High",
                    ["Writers", "Authors", "Content Creators"],
                    ["Creative Writing", "Storytelling", "Character Development"],
                ),
                PromptTemplate(
                    "Create a character profile for {genre}",
                    "Medium",
                    "1-2 hours",
                    "Medium",
                    ["Writers", "Game Designers", "Content Creators"],
                    ["Character Development", "Creative Writing"],
                ),
            ],
        }

    def generate_prompts(self, count: int = 365) -> List[Dict[str, str]]:
        """
        Generate specified number of prompts.

        Args:
            count: Number of prompts to generate

        Returns:
            List[Dict[str, str]]: List of prompt dictionaries
        """
        prompts = []
        for i in range(count):
            # Select random category and template
            category = random.choice(list(PromptCategory))
            template = random.choice(self.templates[category])

            # Create prompt dictionary
            prompt = {
                "id": i + 1,
                "category": category.value,
                "template": template.template,
                "difficulty": template.difficulty,
                "estimated_time": template.estimated_time,
                "monetization_potential": template.monetization_potential,
                "target_audience": template.target_audience,
                "required_skills": template.required_skills,
            }
            prompts.append(prompt)

        return prompts


def create_vault_files(temp_dir: Path) -> Dict[str, str]:
    """
    Create files for the prompt vault.

    Args:
        temp_dir: Directory to create files in

    Returns:
        Dict[str, str]: Mapping of filenames to their content
    """
    try:
        # Generate prompts
        generator = PromptGenerator()
        prompts = generator.generate_prompts()

        # Create JSON file with all prompt data
        json_content = json.dumps(prompts, indent=2)

        # Create formatted text file
        prompt_text = []
        for prompt in prompts:
            prompt_text.append(f"Prompt #{prompt['id']}: {prompt['template']}")
            prompt_text.append(f"Category: {prompt['category']}")
            prompt_text.append(f"Difficulty: {prompt['difficulty']}")
            prompt_text.append(f"Estimated Time: {prompt['estimated_time']}")
            prompt_text.append(
                f"Monetization Potential: {prompt['monetization_potential']}"
            )
            prompt_text.append(
                f"Target Audience: {', '.join(prompt['target_audience'])}"
            )
            prompt_text.append(
                f"Required Skills: {', '.join(prompt['required_skills'])}"
            )
            prompt_text.append("")  # Empty line for readability

        # Create readme content
        readme_text = f"""Welcome to the AI Prompt Vault!

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This vault contains 365 monetizable AI prompts that you can use for:
- Content Creation
- Business Development
- Freelancing Services
- Educational Materials
- Creative Projects

How to Use:
1. Choose a prompt that fits your needs
2. Replace the placeholders (in curly braces) with your specific details
3. Use the prompt with your preferred AI tool
4. Monetize the results through your chosen platform

Categories Included:
- Content Creation (Social Media, Blog Posts, Videos, etc.)
- Business (Plans, Marketing, Sales, etc.)
- Freelancing (Proposals, Portfolios, Services, etc.)
- Education (Lesson Plans, Quizzes, Study Materials, etc.)
- Creative (Stories, Characters, Plots, etc.)

Each prompt includes:
- Difficulty Level
- Estimated Completion Time
- Monetization Potential
- Target Audience
- Required Skills

For support or questions, please contact: support@example.com

Enjoy creating amazing content with AI!
"""

        files_to_create = {
            "365_Monetizable_Prompts.txt": "\n".join(prompt_text),
            "prompts.json": json_content,
            "ReadMe.txt": readme_text,
        }

        # Create files
        for filename, content in files_to_create.items():
            file_path = temp_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created file: {filename}")

        return files_to_create

    except Exception as e:
        logger.error(f"Failed to create vault files: {e}")
        raise


def create_vault_zip(output_path: str) -> bool:
    """
    Create the AI Prompt Vault zip package.

    Args:
        output_path: Path where the zip file should be created

    Returns:
        bool: True if successful
    """
    try:
        # Create temporary directory
        temp_dir = Path("temp_vault")
        temp_dir.mkdir(exist_ok=True)

        # Create vault files
        files_to_create = create_vault_files(temp_dir)

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

        logger.info(f"Successfully created vault zip at: {zip_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create vault zip: {e}")
        return False


def main():
    """Main function to create the prompt vault."""
    try:
        # Define output path
        output_path = "AI_Prompt_Vault.zip"

        # Create vault
        if create_vault_zip(output_path):
            print(f"\nPrompt Vault created successfully at: {output_path}")
            print("\nContents:")
            with zipfile.ZipFile(output_path, "r") as zipf:
                for file in zipf.namelist():
                    print(f"- {file}")

            # Print statistics
            with zipfile.ZipFile(output_path, "r") as zipf:
                total_size = sum(info.file_size for info in zipf.filelist)
                print(f"\nTotal size: {total_size / 1024:.1f} KB")
                print(f"Number of files: {len(zipf.filelist)}")
        else:
            print("\nFailed to create prompt vault. Check the logs for details.")

    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
