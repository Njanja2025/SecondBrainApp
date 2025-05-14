"""
User Interface module for SecondBrain application.
Handles visual experience, interaction flow, and UI components.
"""

from .dashboard.dashboard_manager import DashboardManager, DashboardConfig
from .input_output.io_manager import IOManager, IOConfig
from .themes_styles.theme_manager import ThemeManager, ThemeConfig
from .navigation.nav_manager import NavigationManager, NavConfig

__all__ = [
    "DashboardManager",
    "DashboardConfig",
    "IOManager",
    "IOConfig",
    "ThemeManager",
    "ThemeConfig",
    "NavigationManager",
    "NavConfig",
]
