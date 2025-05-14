"""
Example script for generating daily income summaries with robust error handling
"""

from datetime import datetime
import logging
from decimal import Decimal
from src.secondbrain.finance import (
    generate_income_report,
    ReportType,
    ReportGenerationError,
    DataValidationError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_sample_data() -> list:
    """
    Generate sample daily income data with categories and notes.

    Returns:
        List of dictionaries containing income data
    """
    return [
        {
            "Source": "Gumroad Store",
            "Item": "3 eBooks + templates",
            "Revenue": "1,250.00",
            "Category": "Digital Products",
            "Notes": "Includes new template sales",
        },
        {
            "Source": "Affiliate Page",
            "Item": "Amazon + tools",
            "Revenue": "740.50",
            "Category": "Affiliate Marketing",
            "Notes": "Tool recommendations performing well",
        },
        {
            "Source": "Dropshipping",
            "Item": "Shopify store",
            "Revenue": "2,030.75",
            "Category": "E-commerce",
            "Notes": "New product line launched",
        },
        {
            "Source": "YouTube + Podcast",
            "Item": "Ads + sponsors",
            "Revenue": "580.25",
            "Category": "Content Creation",
            "Notes": "Sponsorship deal started",
        },
        {
            "Source": "Content Services",
            "Item": "5 clients/month",
            "Revenue": "2,300.00",
            "Category": "Services",
            "Notes": "New client onboarded",
        },
        {
            "Source": "Amazon KDP",
            "Item": "2 eBooks",
            "Revenue": "320.50",
            "Category": "Digital Products",
            "Notes": "New book published",
        },
        {
            "Source": "Email Funnel",
            "Item": "Digital + Affiliate sales",
            "Revenue": "950.00",
            "Category": "Marketing",
            "Notes": "New funnel sequence",
        },
    ]


def generate_simple_report(data: list) -> str:
    """
    Generate a simple income summary report.

    Args:
        data: List of income data dictionaries

    Returns:
        Path to generated PDF file
    """
    try:
        output_path = generate_income_report(
            data=data,
            title="SecondBrainApp Daily Income Summary",
            is_daily_summary=True,
            report_type=ReportType.DAILY,
            use_simple_format=True,
        )

        logger.info(f"Simple income summary generated: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to generate simple report: {e}")
        raise


def generate_advanced_report(data: list) -> str:
    """
    Generate an advanced income summary report with analysis.

    Args:
        data: List of income data dictionaries

    Returns:
        Path to generated PDF file
    """
    try:
        output_path = generate_income_report(
            data=data,
            title="SecondBrain Daily Income Analysis",
            is_daily_summary=True,
            report_type=ReportType.DAILY,
            use_simple_format=False,
        )

        logger.info(f"Advanced income summary generated: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to generate advanced report: {e}")
        raise


def main():
    try:
        # Generate sample data
        daily_income_data = generate_sample_data()

        # Generate both report formats
        simple_report_path = generate_simple_report(daily_income_data)
        advanced_report_path = generate_advanced_report(daily_income_data)

        print("\nGenerated Reports:")
        print(f"1. Simple Report: {simple_report_path}")
        print("   Features:")
        print("   - Clean, modern layout")
        print("   - Basic income table")
        print("   - Total revenue calculation")
        print("   - Automatic date stamping")

        print(f"\n2. Advanced Report: {advanced_report_path}")
        print("   Features:")
        print("   - Comprehensive analysis")
        print("   - Category breakdown")
        print("   - Visualizations")
        print("   - Trend analysis")
        print("   - Risk assessment")

        print("\nData Management:")
        print("   - Automatic data validation")
        print("   - Data persistence in JSON format")
        print("   - Report archiving")
        print("   - Unique report identification")

        print("\nError Handling:")
        print("   - Input validation")
        print("   - Data format checking")
        print("   - Directory validation")
        print("   - Chart generation error handling")

    except DataValidationError as e:
        logger.error(f"Data validation error: {e}")
        print(f"\nError: Invalid data format - {e}")
    except ReportGenerationError as e:
        logger.error(f"Report generation error: {e}")
        print(f"\nError: Failed to generate report - {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: An unexpected error occurred - {e}")


if __name__ == "__main__":
    main()
