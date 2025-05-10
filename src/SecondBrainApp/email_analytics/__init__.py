"""
Email Analytics module for SecondBrain application.
Manages email metrics, monitoring, and reporting.
"""

from .email_metrics import (
    EmailMetricsManager,
    EmailMetricConfig,
    MetricType,
    MetricCategory
)
from .inbox_monitor import (
    InboxMonitor,
    MonitorConfig,
    AlertConfig,
    FilterConfig
)
from .reporting import (
    EmailReportManager,
    ReportFormat,
    ReportTemplate
)
from .visualization import (
    EmailVisualizer,
    ChartType,
    ChartConfig
)

__all__ = [
    'EmailMetricsManager',
    'EmailMetricConfig',
    'MetricType',
    'MetricCategory',
    'InboxMonitor',
    'MonitorConfig',
    'AlertConfig',
    'FilterConfig',
    'EmailReportManager',
    'ReportFormat',
    'ReportTemplate',
    'EmailVisualizer',
    'ChartType',
    'ChartConfig'
] 