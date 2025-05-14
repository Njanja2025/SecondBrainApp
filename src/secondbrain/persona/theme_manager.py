"""
Theme Manager for synchronizing GUI appearance with emotional state.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional
import json
from datetime import datetime
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manages GUI theme synchronization with emotional state."""

    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root
        self.current_theme = "neutral"
        self.transition_duration = 0.5  # seconds

        # Theme color mappings
        self.theme_colors = {
            "calm": {
                "bg": "#AEE1F9",  # Sky blue
                "fg": "#2C3E50",  # Dark blue-gray
                "accent": "#85C1E9",  # Light blue
            },
            "excited": {
                "bg": "#FFF176",  # Vibrant yellow
                "fg": "#E67E22",  # Dark orange
                "accent": "#FFE082",  # Light yellow
            },
            "attentive": {
                "bg": "#C8E6C9",  # Soft green
                "fg": "#2E7D32",  # Dark green
                "accent": "#A5D6A7",  # Light green
            },
            "thoughtful": {
                "bg": "#E1BEE7",  # Soft purple
                "fg": "#6A1B9A",  # Dark purple
                "accent": "#CE93D8",  # Light purple
            },
            "neutral": {
                "bg": "#E0E0E0",  # Light gray
                "fg": "#424242",  # Dark gray
                "accent": "#BDBDBD",  # Medium gray
            },
        }

        # Theme history
        self.theme_history = []

        # Load custom themes if available
        self._load_custom_themes()

    def _load_custom_themes(self):
        """Load custom theme configurations."""
        try:
            theme_file = Path("config/themes.json")
            if theme_file.exists():
                with open(theme_file) as f:
                    custom_themes = json.load(f)
                self.theme_colors.update(custom_themes)
        except Exception as e:
            logger.error(f"Failed to load custom themes: {e}")

    async def sync_theme(self, tone: str):
        """
        Synchronize GUI theme with emotional tone.

        Args:
            tone: Emotional tone to match
        """
        try:
            if not self.root:
                return

            # Get theme colors
            theme = self.theme_colors.get(tone, self.theme_colors["neutral"])

            # Log theme change
            self.theme_history.append(
                {"tone": tone, "theme": theme, "timestamp": datetime.now().isoformat()}
            )

            # Animate transition
            await self._animate_transition(theme)

            self.current_theme = tone

        except Exception as e:
            logger.error(f"Failed to sync theme: {e}")

    async def _animate_transition(self, target_theme: Dict):
        """
        Smoothly animate theme transition.

        Args:
            target_theme: Target theme colors
        """
        try:
            # Get current colors
            current_bg = self.root.cget("bg")
            frames = 20  # Number of transition frames

            # Calculate color steps
            bg_steps = self._calculate_color_steps(
                current_bg, target_theme["bg"], frames
            )

            # Animate transition
            for i in range(frames):
                # Update background
                self.root.configure(bg=bg_steps[i])

                # Update widgets
                for widget in self.root.winfo_children():
                    if isinstance(widget, (ttk.Frame, tk.Frame)):
                        widget.configure(bg=bg_steps[i])
                    elif isinstance(widget, (ttk.Label, tk.Label)):
                        widget.configure(bg=bg_steps[i], fg=target_theme["fg"])

                # Small delay for smooth transition
                await asyncio.sleep(self.transition_duration / frames)

        except Exception as e:
            logger.error(f"Failed to animate theme transition: {e}")

    def _calculate_color_steps(
        self, start_color: str, end_color: str, steps: int
    ) -> list:
        """
        Calculate intermediate colors for smooth transition.

        Args:
            start_color: Starting color hex
            end_color: Target color hex
            steps: Number of transition steps

        Returns:
            List of intermediate color hex values
        """
        try:
            # Convert hex to RGB
            start_rgb = self._hex_to_rgb(start_color)
            end_rgb = self._hex_to_rgb(end_color)

            # Calculate steps
            r_step = (end_rgb[0] - start_rgb[0]) / steps
            g_step = (end_rgb[1] - start_rgb[1]) / steps
            b_step = (end_rgb[2] - start_rgb[2]) / steps

            # Generate color sequence
            colors = []
            for i in range(steps):
                r = int(start_rgb[0] + (r_step * i))
                g = int(start_rgb[1] + (g_step * i))
                b = int(start_rgb[2] + (b_step * i))
                colors.append(f"#{r:02x}{g:02x}{b:02x}")

            return colors

        except Exception as e:
            logger.error(f"Failed to calculate color steps: {e}")
            return [start_color] * steps

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def get_theme_analytics(self) -> Dict:
        """Get analytics about theme usage patterns."""
        try:
            if not self.theme_history:
                return {}

            # Analyze recent history
            recent = self.theme_history[-100:]  # Last 100 entries

            # Count theme frequencies
            theme_counts = {}
            for entry in recent:
                tone = entry["tone"]
                theme_counts[tone] = theme_counts.get(tone, 0) + 1

            return {
                "current_theme": self.current_theme,
                "theme_distribution": theme_counts,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get theme analytics: {e}")
            return {}
