"""
Testing & Quality Assurance module for SecondBrain application.
Ensures system reliability, performance, and correctness through comprehensive testing.
"""

from .unit_tests.test_manager import TestManager, TestConfig
from .integration_tests.integration_tester import IntegrationTester, IntegrationConfig
from .performance_tests.performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceConfig,
)
from .test_reports.report_generator import ReportGenerator, ReportConfig

__all__ = [
    "TestManager",
    "TestConfig",
    "IntegrationTester",
    "IntegrationConfig",
    "PerformanceAnalyzer",
    "PerformanceConfig",
    "ReportGenerator",
    "ReportConfig",
]
