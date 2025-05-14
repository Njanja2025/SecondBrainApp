"""
Example script for generating income reports
"""

from datetime import datetime, timedelta
import numpy as np
from src.secondbrain.finance import generate_income_report


def generate_historical_data(days: int = 30) -> list:
    """
    Generate sample historical data with realistic variations.

    Args:
        days: Number of days of historical data to generate

    Returns:
        List of daily income data dictionaries
    """
    base_data = {
        "Gumroad Store": 1250.00,
        "Affiliate Page": 675.50,
        "Dropshipping": 2120.75,
        "YouTube + Podcast": 920.25,
        "Content Services": 1800.00,
        "Amazon KDP": 360.50,
        "Email Funnel": 740.00,
    }

    historical_data = []
    for i in range(days):
        # Add realistic variations to each source
        day_data = {}
        for source, amount in base_data.items():
            # Add trend
            trend = 1 + (i * 0.02)  # 2% daily growth

            # Add random variation
            variation = np.random.normal(1, 0.1)  # 10% standard deviation

            # Add weekly seasonality
            seasonality = 1 + 0.1 * np.sin(i * 2 * np.pi / 7)  # Weekly cycle

            # Calculate final amount
            final_amount = amount * trend * variation * seasonality
            day_data[source] = max(0, final_amount)  # Ensure non-negative

        historical_data.append(day_data)

    return historical_data


def main():
    # Current income data
    income_data = {
        "Gumroad Store": 1250.00,
        "Affiliate Page": 675.50,
        "Dropshipping": 2120.75,
        "YouTube + Podcast": 920.25,
        "Content Services": 1800.00,
        "Amazon KDP": 360.50,
        "Email Funnel": 740.00,
    }

    # Generate historical data with realistic variations
    historical_data = generate_historical_data(days=30)

    # Generate comprehensive report
    output_path = generate_income_report(
        data=income_data,
        title="SecondBrain Monthly Income Report",
        historical_data=historical_data,
        include_charts=True,
        forecast_days=30,
    )

    print(f"Income report generated: {output_path}")
    print("\nReport includes:")
    print("1. Visualizations:")
    print("   - Income distribution pie chart")
    print("   - Income by source bar chart")
    print("   - Income source radar chart")
    print("   - Income correlation heatmap")
    print("   - Growth rate comparison chart")
    print("   - Risk matrix visualization")
    print("   - 30-day forecast with confidence intervals")

    print("\n2. Analysis:")
    print("   - Detailed income table with percentages")
    print("   - Summary statistics")
    print("   - Trend analysis with growth rates")
    print("   - Comparative analysis by source")
    print("   - Risk assessment for each income source")
    print("   - 30-day income forecast")

    print("\n3. Business Intelligence:")
    print("   - Growth opportunity identification")
    print("   - Risk level assessment")
    print("   - Trend direction analysis")
    print("   - Performance recommendations")
    print("   - Volatility analysis")

    print("\n4. Data Management:")
    print("   - Historical data tracking")
    print("   - Data persistence in JSON format")
    print("   - Automatic report archiving")
    print("   - Unique report identification")


if __name__ == "__main__":
    main()
