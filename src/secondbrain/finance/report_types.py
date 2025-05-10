"""
Report type definitions for SecondBrainApp finance module
"""
from enum import Enum, auto

class ReportType(Enum):
    """Types of financial reports that can be generated."""
    
    INCOME_SUMMARY = auto()
    REVENUE_DISTRIBUTION = auto()
    ASSET_PERFORMANCE = auto()
    EXPENSE_ANALYSIS = auto()
    CASH_FLOW = auto()
    PROFIT_LOSS = auto()
    BALANCE_SHEET = auto()
    TAX_SUMMARY = auto()
    INCOME = "income"
    EXPENSE = "expense"
    BALANCE = "balance"
    TAX = "tax"
    CUSTOM = "custom"
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return self.name.replace('_', ' ').title()
        
    @classmethod
    def from_string(cls, value: str) -> 'ReportType':
        """
        Convert a string to a ReportType enum value.
        
        Args:
            value: String representation of the report type
            
        Returns:
            ReportType: The corresponding enum value
            
        Raises:
            ValueError: If the string doesn't match any report type
        """
        try:
            # Convert string to enum format (e.g., "Income Summary" -> "INCOME_SUMMARY")
            enum_value = value.upper().replace(' ', '_')
            return cls[enum_value]
        except KeyError:
            raise ValueError(f"Invalid report type: {value}")
            
    @property
    def description(self) -> str:
        """Get a detailed description of the report type."""
        descriptions = {
            ReportType.INCOME_SUMMARY: "Summary of all income sources and totals",
            ReportType.REVENUE_DISTRIBUTION: "Breakdown of revenue by source and category",
            ReportType.ASSET_PERFORMANCE: "Performance metrics for digital assets",
            ReportType.EXPENSE_ANALYSIS: "Detailed analysis of expenses and costs",
            ReportType.CASH_FLOW: "Cash flow statement and projections",
            ReportType.PROFIT_LOSS: "Profit and loss statement",
            ReportType.BALANCE_SHEET: "Financial position and balance sheet",
            ReportType.TAX_SUMMARY: "Tax-related information and summaries"
        }
        return descriptions.get(self, "No description available") 