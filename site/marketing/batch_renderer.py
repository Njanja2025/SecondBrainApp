"""
Enhanced batch video rendering system for multiple versions
"""

import os
import json
import logging
from pathlib import Path
from render_njanja_intro import VideoRenderer
from thumbnail_generator import ThumbnailGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BatchRenderer:
    def __init__(self):
        """Initialize the batch renderer."""
        self.assets_dir = "site/marketing/assets"
        self.exports_dir = "site/marketing/exports"
        self.config_path = os.path.join(self.assets_dir, "render_config.json")
        self.video_renderer = VideoRenderer()
        self.thumbnail_generator = ThumbnailGenerator()

    def load_config(self):
        """Load rendering configuration."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {
                "versions": [
                    {
                        "name": "standard",
                        "title": "Welcome to Njanja AI Empire",
                        "subtitle": "AI-Powered Business Solutions",
                        "features": [
                            "AI-Powered Business Solutions",
                            "Automated Content Generation",
                            "Smart Analytics & Insights",
                            "24/7 Customer Support",
                        ],
                        "style": {
                            "text_color": "#ffffff",
                            "highlight_color": "#00ff00",
                            "background_color": [0, 0, 0],
                            "font": "Arial-Bold",
                        },
                        "effects": {
                            "text_animation": {
                                "zoom": True,
                                "slide": True,
                                "fade": True,
                                "rotate": False,
                            },
                            "background": {"gradient": True, "color_shift": False},
                            "banner": {"zoom": True, "rotate": False},
                            "feature_animation": {"slide": True, "bounce": False},
                            "global": {"fade": True, "color_shift": False},
                        },
                        "thumbnail": {
                            "enhance": True,
                            "gradient": True,
                            "gradient_colors": [(0, 0, 0, 128), (0, 0, 0, 64)],
                            "gradient_direction": "vertical",
                            "blur": True,
                            "blur_radius": 2,
                            "title_effects": {
                                "shadow": True,
                                "shadow_offset": 3,
                                "glow": True,
                                "glow_radius": 2,
                            },
                            "subtitle_effects": {"shadow": True, "shadow_offset": 2},
                            "logo_glow": True,
                            "border": True,
                            "border_width": 5,
                            "border_color": (255, 255, 255),
                        },
                    }
                ],
                "rendering": {
                    "fps": 24,
                    "resolution": [1920, 1080],
                    "bitrate": "8000k",
                    "preset": "medium",
                    "threads": 4,
                },
            }

    def render_version(self, version_config):
        """Render a single version of the video."""
        try:
            logger.info(f"Rendering version: {version_config['name']}")

            # Update video renderer configuration
            self.video_renderer.output_path = os.path.join(
                self.exports_dir, f"Njanja_Intro_{version_config['name']}.mp4"
            )

            # Render video with effects
            video_config = {
                "title": version_config["title"],
                "features": [
                    (f, i * 5) for i, f in enumerate(version_config["features"])
                ],
                "background_color": version_config["style"]["background_color"],
                "effects": version_config["effects"],
                "rendering": version_config.get("rendering", {}),
            }

            video_path = self.video_renderer.render_video(config=video_config)

            # Generate thumbnail with effects
            thumbnail_path = self.thumbnail_generator.create_thumbnail(
                title=version_config["title"],
                subtitle=version_config["subtitle"],
                style_config=version_config["thumbnail"],
            )

            return {
                "name": version_config["name"],
                "video_path": video_path,
                "thumbnail_path": thumbnail_path,
            }

        except Exception as e:
            logger.error(f"Error rendering version {version_config['name']}: {e}")
            raise

    def render_all_versions(self):
        """Render all configured versions."""
        try:
            config = self.load_config()
            results = []

            for version in config["versions"]:
                result = self.render_version(version)
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error in batch rendering: {e}")
            raise

    def generate_report(self, results):
        """Generate a detailed rendering report."""
        report_path = os.path.join(self.exports_dir, "render_report.txt")

        with open(report_path, "w") as f:
            f.write("Video Rendering Report\n")
            f.write("=====================\n\n")

            for result in results:
                f.write(f"Version: {result['name']}\n")
                f.write(f"Video: {result['video_path']}\n")
                f.write(f"Thumbnail: {result['thumbnail_path']}\n")
                f.write("\nEffects Applied:\n")
                f.write("----------------\n")

                # Load version config
                version_config = next(
                    (
                        v
                        for v in self.load_config()["versions"]
                        if v["name"] == result["name"]
                    ),
                    None,
                )

                if version_config:
                    f.write("\nVideo Effects:\n")
                    for effect_type, effects in version_config["effects"].items():
                        f.write(f"\n{effect_type}:\n")
                        for effect, enabled in effects.items():
                            f.write(
                                f"  - {effect}: {'Enabled' if enabled else 'Disabled'}\n"
                            )

                    f.write("\nThumbnail Effects:\n")
                    for effect_type, effects in version_config["thumbnail"].items():
                        if isinstance(effects, dict):
                            f.write(f"\n{effect_type}:\n")
                            for effect, value in effects.items():
                                f.write(f"  - {effect}: {value}\n")
                        else:
                            f.write(f"  - {effect_type}: {effects}\n")

                f.write("\n" + "=" * 50 + "\n\n")

        return report_path


def main():
    """Main function to run batch rendering."""
    try:
        renderer = BatchRenderer()
        results = renderer.render_all_versions()
        report_path = renderer.generate_report(results)

        print("\nBatch rendering completed successfully!")
        print(f"Report generated: {report_path}")
        print("\nGenerated files:")
        for result in results:
            print(f"\nVersion: {result['name']}")
            print(f"Video: {result['video_path']}")
            print(f"Thumbnail: {result['thumbnail_path']}")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
