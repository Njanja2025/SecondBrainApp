"""
Theme manager for handling UI themes and styles.
Manages color schemes, icons, and visual assets.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ThemeConfig:
    """Configuration for UI theme and styles."""

    name: str
    colors: Dict[str, str]
    fonts: Dict[str, str]
    icons: Dict[str, str]
    spacing: Dict[str, int]
    animations: Dict[str, Any]
    is_dark: bool = False
    is_custom: bool = False


class ThemeManager:
    """Manages UI themes and styles."""

    def __init__(self, config_dir: str = "config/themes"):
        """Initialize the theme manager.

        Args:
            config_dir: Directory to store theme configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_themes()

    def _setup_logging(self):
        """Set up logging for the theme manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_themes(self):
        """Load theme configurations."""
        try:
            config_file = self.config_dir / "themes.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    self.themes = {
                        name: ThemeConfig(**config)
                        for name, config in json.load(f).items()
                    }
            else:
                self.themes = {}
                self._save_themes()

            logger.info("Theme configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load theme configurations: {str(e)}")
            raise

    def _save_themes(self):
        """Save theme configurations."""
        try:
            config_file = self.config_dir / "themes.json"

            with open(config_file, "w") as f:
                json.dump(
                    {name: vars(config) for name, config in self.themes.items()},
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save theme configurations: {str(e)}")

    def create_theme(self, config: ThemeConfig) -> bool:
        """Create a new theme.

        Args:
            config: Theme configuration

        Returns:
            bool: True if theme was created successfully
        """
        try:
            if config.name in self.themes:
                logger.error(f"Theme {config.name} already exists")
                return False

            self.themes[config.name] = config
            self._save_themes()

            logger.info(f"Created theme {config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create theme {config.name}: {str(e)}")
            return False

    def update_theme(self, name: str, config: ThemeConfig) -> bool:
        """Update an existing theme.

        Args:
            name: Theme name
            config: New theme configuration

        Returns:
            bool: True if theme was updated successfully
        """
        try:
            if name not in self.themes:
                logger.error(f"Theme {name} not found")
                return False

            self.themes[name] = config
            self._save_themes()

            logger.info(f"Updated theme {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update theme {name}: {str(e)}")
            return False

    def delete_theme(self, name: str) -> bool:
        """Delete a theme.

        Args:
            name: Theme name

        Returns:
            bool: True if theme was deleted successfully
        """
        try:
            if name not in self.themes:
                logger.error(f"Theme {name} not found")
                return False

            del self.themes[name]
            self._save_themes()

            logger.info(f"Deleted theme {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete theme {name}: {str(e)}")
            return False

    def get_theme(self, name: str) -> Optional[ThemeConfig]:
        """Get theme configuration.

        Args:
            name: Theme name

        Returns:
            Theme configuration if found
        """
        return self.themes.get(name)

    def list_themes(self) -> List[str]:
        """List all themes.

        Returns:
            List of theme names
        """
        return list(self.themes.keys())

    def get_color(self, theme_name: str, color_name: str) -> Optional[str]:
        """Get a color from a theme.

        Args:
            theme_name: Theme name
            color_name: Color name

        Returns:
            Color value if found
        """
        try:
            theme = self.get_theme(theme_name)
            if not theme:
                logger.error(f"Theme {theme_name} not found")
                return None

            return theme.colors.get(color_name)

        except Exception as e:
            logger.error(
                f"Failed to get color {color_name} from theme {theme_name}: {str(e)}"
            )
            return None

    def get_font(self, theme_name: str, font_name: str) -> Optional[str]:
        """Get a font from a theme.

        Args:
            theme_name: Theme name
            font_name: Font name

        Returns:
            Font value if found
        """
        try:
            theme = self.get_theme(theme_name)
            if not theme:
                logger.error(f"Theme {theme_name} not found")
                return None

            return theme.fonts.get(font_name)

        except Exception as e:
            logger.error(
                f"Failed to get font {font_name} from theme {theme_name}: {str(e)}"
            )
            return None

    def get_icon(self, theme_name: str, icon_name: str) -> Optional[str]:
        """Get an icon from a theme.

        Args:
            theme_name: Theme name
            icon_name: Icon name

        Returns:
            Icon value if found
        """
        try:
            theme = self.get_theme(theme_name)
            if not theme:
                logger.error(f"Theme {theme_name} not found")
                return None

            return theme.icons.get(icon_name)

        except Exception as e:
            logger.error(
                f"Failed to get icon {icon_name} from theme {theme_name}: {str(e)}"
            )
            return None

    def get_spacing(self, theme_name: str, spacing_name: str) -> Optional[int]:
        """Get a spacing value from a theme.

        Args:
            theme_name: Theme name
            spacing_name: Spacing name

        Returns:
            Spacing value if found
        """
        try:
            theme = self.get_theme(theme_name)
            if not theme:
                logger.error(f"Theme {theme_name} not found")
                return None

            return theme.spacing.get(spacing_name)

        except Exception as e:
            logger.error(
                f"Failed to get spacing {spacing_name} from theme {theme_name}: {str(e)}"
            )
            return None

    def get_animation(
        self, theme_name: str, animation_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get an animation from a theme.

        Args:
            theme_name: Theme name
            animation_name: Animation name

        Returns:
            Animation configuration if found
        """
        try:
            theme = self.get_theme(theme_name)
            if not theme:
                logger.error(f"Theme {theme_name} not found")
                return None

            return theme.animations.get(animation_name)

        except Exception as e:
            logger.error(
                f"Failed to get animation {animation_name} from theme {theme_name}: {str(e)}"
            )
            return None


# Example usage
if __name__ == "__main__":
    manager = ThemeManager()

    # Create a theme
    config = ThemeConfig(
        name="default",
        colors={
            "primary": "#007bff",
            "secondary": "#6c757d",
            "background": "#ffffff",
            "text": "#212529",
        },
        fonts={"heading": "Arial", "body": "Helvetica", "mono": "Courier"},
        icons={"home": "home.svg", "settings": "settings.svg", "user": "user.svg"},
        spacing={"small": 8, "medium": 16, "large": 24},
        animations={"fade": {"duration": 0.3, "easing": "ease-in-out"}},
    )
    manager.create_theme(config)

    # Get theme values
    primary_color = manager.get_color("default", "primary")
    heading_font = manager.get_font("default", "heading")
    home_icon = manager.get_icon("default", "home")
    medium_spacing = manager.get_spacing("default", "medium")
    fade_animation = manager.get_animation("default", "fade")
