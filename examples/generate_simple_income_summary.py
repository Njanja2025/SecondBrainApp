"""
Example script for generating income summaries with enhanced features
"""

from datetime import datetime
import logging
from decimal import Decimal
from pathlib import Path
from src.secondbrain.finance.document_generator import (
    generate_income_report,
    DocumentConfig,
    DocumentStyle,
    ReportType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_sample_data() -> list:
    """
    Generate sample daily income data.

    Returns:
        List of dictionaries containing income data
    """
    return [
        {
            "Source": "Gumroad Store",
            "Item": "3 eBooks + templates",
            "Revenue": "1,250.00",
            "Notes": "Includes new template sales",
        },
        {
            "Source": "Affiliate Links",
            "Item": "Amazon, tools, Canva",
            "Revenue": "430.00",
            "Notes": "Tool recommendations performing well",
        },
        {
            "Source": "Dropshipping",
            "Item": "Shopify - AI Gadgets",
            "Revenue": "1,720.00",
            "Notes": "New product line launched",
        },
        {
            "Source": "YouTube + Podcast",
            "Item": "AdSense + Sponsorships",
            "Revenue": "540.00",
            "Notes": "Sponsorship deal started",
        },
        {
            "Source": "Content Services",
            "Item": "4 Clients via Fiverr",
            "Revenue": "2,100.00",
            "Notes": "New client onboarded",
        },
        {
            "Source": "Amazon KDP",
            "Item": "2 Books Royalties",
            "Revenue": "240.00",
            "Notes": "New book published",
        },
        {
            "Source": "Email Funnel",
            "Item": "Product + Affiliate Offers",
            "Revenue": "890.00",
            "Notes": "New funnel sequence",
        },
    ]


def main():
    try:
        # Generate sample data
        daily_income_data = generate_sample_data()

        # Create document configurations
        modern_config = DocumentConfig(
            title="SecondBrainApp Daily Income Summary",
            style=DocumentStyle.MODERN,
            include_charts=True,
            include_summary=True,
            include_notes=True,
            watermark="CONFIDENTIAL",
        )

        corporate_config = DocumentConfig(
            title="SecondBrainApp Corporate Income Report",
            style=DocumentStyle.CORPORATE,
            include_charts=True,
            include_summary=True,
            include_notes=True,
            watermark="INTERNAL USE ONLY",
        )

        # Generate reports in different formats and styles
        pdf_path = generate_income_report(
            data=daily_income_data, config=modern_config, format="pdf"
        )

        docx_path = generate_income_report(
            data=daily_income_data, config=corporate_config, format="docx"
        )

        logger.info(f"PDF report generated: {pdf_path}")
        logger.info(f"Word report generated: {docx_path}")

        print("\nGenerated Reports:")
        print(f"1. Modern PDF Report: {pdf_path}")
        print("   Features:")
        print("   - Modern blue color scheme")
        print("   - Professional header with date")
        print("   - Consistent font styling")
        print("   - Phantom AI branding")
        print("   - Basic income table")
        print("   - Total revenue calculation")
        print("   - Revenue distribution chart")
        print("   - Summary statistics")
        print("   - Notes for each entry")
        print("   - Confidential watermark")

        print(f"\n2. Corporate Word Report: {docx_path}")
        print("   Features:")
        print("   - Corporate green color scheme")
        print("   - Professional document format")
        print("   - Formatted table with grid")
        print("   - Proper spacing and alignment")
        print("   - Easy to edit and modify")
        print("   - Compatible with Microsoft Office")
        print("   - Revenue distribution chart")
        print("   - Summary statistics")
        print("   - Notes for each entry")
        print("   - Internal use watermark")

        print("\nData Management:")
        print("   - Automatic data validation")
        print("   - Revenue formatting")
        print("   - Total calculation")
        print("   - Unique file naming")
        print("   - Organized storage")
        print("   - Template support")
        print("   - Style customization")

        print("\nError Handling:")
        print("   - Input validation")
        print("   - Format checking")
        print("   - Directory validation")
        print("   - Chart generation error handling")
        print("   - Template loading error handling")
        print("   - Watermark error handling")

    except Exception as e:
        logger.error(f"Failed to generate reports: {e}")
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
