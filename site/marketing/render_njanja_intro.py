"""
Video rendering script for Njanja AI Empire intro with advanced effects
"""

import os
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
    VideoFileClip,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.fx import fadein, fadeout, resize, mirror_x, rotate, colorx
from moviepy.video.compositing.transitions import crossfadein, crossfadeout
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VideoRenderer:
    def __init__(self):
        """Initialize the video renderer."""
        self.assets_dir = "site/marketing/assets"
        self.exports_dir = "site/marketing/exports"
        self.audio_path = os.path.join(self.assets_dir, "audio", "NjanjaIntro.mp3")
        self.banner_path = os.path.join(
            self.assets_dir, "branding", "Njanja_YouTube_Banner.png"
        )
        self.output_path = os.path.join(self.exports_dir, "Njanja_Intro_60s.mp4")

        # Ensure directories exist
        os.makedirs(self.exports_dir, exist_ok=True)

    def create_particle_effect(self, duration, size=(1920, 1080), num_particles=100):
        """Create a particle effect background."""

        def make_frame(t):
            frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
            for i in range(num_particles):
                x = int(size[0] * (0.5 + 0.5 * np.sin(t * 2 + i)))
                y = int(size[1] * (0.5 + 0.5 * np.cos(t * 3 + i)))
                color = (255, 255, 255)
                frame[y - 2 : y + 2, x - 2 : x + 2] = color
            return frame

        return VideoFileClip(make_frame, duration=duration)

    def create_3d_text(
        self, text, duration, position, fontsize=70, color="white", style_config=None
    ):
        """Create 3D text effect."""
        if style_config is None:
            style_config = {}

        # Create base text
        clip = TextClip(
            text,
            fontsize=fontsize,
            color=color,
            font=style_config.get("font", "Arial-Bold"),
            stroke_color=style_config.get("stroke_color", "black"),
            stroke_width=style_config.get("stroke_width", 2),
            method="caption",
            align="center",
        )

        # Add 3D rotation
        def rotation_3d(t):
            if t < 0.5:
                return 30 * (1 - t / 0.5)
            return 0

        clip = clip.rotate(lambda t: rotation_3d(t))

        # Add perspective transform
        def perspective_transform(t):
            if t < 0.5:
                scale = 1 + 0.2 * t / 0.5
                return scale
            return 1.2

        clip = clip.resize(lambda t: perspective_transform(t))

        return clip.set_position(position).set_duration(duration)

    def create_text_overlay(
        self, text, duration, position, fontsize=70, color="white", style_config=None
    ):
        """Create a text overlay with enhanced effects."""
        if style_config is None:
            style_config = {}

        # Use 3D text if enabled
        if style_config.get("3d", False):
            return self.create_3d_text(
                text, duration, position, fontsize, color, style_config
            )

        clip = TextClip(
            text,
            fontsize=fontsize,
            color=color,
            font=style_config.get("font", "Arial-Bold"),
            stroke_color=style_config.get("stroke_color", "black"),
            stroke_width=style_config.get("stroke_width", 2),
            method="caption",
            align="center",
        )

        # Add animations
        clip = clip.set_position(position).set_duration(duration)

        # Enhanced transitions
        if style_config.get("fade", True):
            clip = clip.crossfadein(0.5).crossfadeout(0.5)

        # Add zoom effect
        if style_config.get("zoom", True):

            def zoom_effect(t):
                if t < 0.5:
                    return 1 + 0.2 * t
                elif t > duration - 0.5:
                    return 1 + 0.2 * (duration - t)
                return 1.2

            clip = clip.resize(lambda t: zoom_effect(t))

        # Add rotation effect
        if style_config.get("rotate", False):

            def rotation_effect(t):
                if t < 0.5:
                    return 5 * (1 - t / 0.5)
                return 0

            clip = clip.rotate(lambda t: rotation_effect(t))

        # Add wave effect
        if style_config.get("wave", False):

            def wave_effect(t):
                return 1 + 0.1 * np.sin(t * 10)

            clip = clip.resize(lambda t: wave_effect(t))

        return clip

    def create_background(self, duration, color=(0, 0, 0), style_config=None):
        """Create an animated background with enhanced effects."""
        if style_config is None:
            style_config = {}

        # Use particle effect if enabled
        if style_config.get("particles", False):
            return self.create_particle_effect(
                duration, num_particles=style_config.get("num_particles", 100)
            )

        bg = ColorClip(size=(1920, 1080), color=color).set_duration(duration)

        # Add gradient animation
        if style_config.get("gradient", True):

            def gradient_effect(t):
                r = int(50 * (1 + t / duration))
                g = int(30 * (1 + t / duration))
                b = int(70 * (1 + t / duration))
                return (r, g, b)

            bg = bg.set_color(lambda t: gradient_effect(t))

        # Add color shift effect
        if style_config.get("color_shift", False):
            bg = bg.fx(colorx, 1.2)

        # Add wave effect
        if style_config.get("wave", False):

            def wave_effect(t):
                return 1 + 0.1 * np.sin(t * 5)

            bg = bg.resize(lambda t: wave_effect(t))

        return bg

    def create_feature_highlight(
        self, text, start_time, duration, position, style_config=None
    ):
        """Create an animated feature highlight with enhanced effects."""
        if style_config is None:
            style_config = {}

        # Create text clip
        text_clip = self.create_text_overlay(
            text,
            duration=duration,
            position=position,
            fontsize=50,
            color=style_config.get("highlight_color", "#00ff00"),
            style_config=style_config,
        )

        # Add slide-in animation
        if style_config.get("slide", True):

            def slide_effect(t):
                if t < 0.5:
                    return ("center", position[1] + 100 * (1 - t / 0.5))
                return position

            text_clip = text_clip.set_position(lambda t: slide_effect(t))

        # Add bounce effect
        if style_config.get("bounce", False):

            def bounce_effect(t):
                if t < 0.5:
                    return 1 + 0.2 * np.sin(t * 10)
                return 1

            text_clip = text_clip.resize(lambda t: bounce_effect(t))

        # Add wave effect
        if style_config.get("wave", False):

            def wave_effect(t):
                return 1 + 0.1 * np.sin(t * 5)

            text_clip = text_clip.resize(lambda t: wave_effect(t))

        return text_clip.set_start(start_time)

    def render_video(self, config=None):
        """Render the final video with enhanced effects."""
        try:
            if config is None:
                config = {}

            logger.info("Loading audio file...")
            audio = AudioFileClip(self.audio_path)
            duration = audio.duration

            logger.info("Creating background...")
            background = self.create_background(
                duration,
                color=tuple(config.get("background_color", (0, 0, 0))),
                style_config=config.get("effects", {}).get("background", {}),
            )

            logger.info("Loading banner image...")
            banner = ImageClip(self.banner_path).set_duration(duration)
            banner = banner.resize(width=1920).set_position("center")

            # Add enhanced banner effects
            if config.get("effects", {}).get("banner", {}).get("zoom", True):

                def banner_zoom(t):
                    if t < 2:
                        return 1 + 0.1 * t / 2
                    return 1.1

                banner = banner.resize(lambda t: banner_zoom(t))

            if config.get("effects", {}).get("banner", {}).get("rotate", False):

                def banner_rotation(t):
                    if t < 1:
                        return 2 * (1 - t)
                    return 0

                banner = banner.rotate(lambda t: banner_rotation(t))

            if config.get("effects", {}).get("banner", {}).get("wave", False):

                def banner_wave(t):
                    return 1 + 0.05 * np.sin(t * 5)

                banner = banner.resize(lambda t: banner_wave(t))

            logger.info("Creating text overlays...")
            # Welcome text with enhanced animation
            welcome_text = self.create_text_overlay(
                config.get("title", "Welcome to Njanja AI Empire"),
                duration=5,
                position=("center", 100),
                fontsize=80,
                style_config=config.get("effects", {}).get("text_animation", {}),
            )

            # Features with animations
            features = config.get(
                "features",
                [
                    ("AI-Powered Business Solutions", 5),
                    ("Automated Content Generation", 10),
                    ("Smart Analytics & Insights", 15),
                    ("24/7 Customer Support", 20),
                ],
            )

            feature_clips = []
            for i, (feature, start_time) in enumerate(features):
                clip = self.create_feature_highlight(
                    feature,
                    start_time=start_time,
                    duration=4,
                    position=("center", 300 + i * 100),
                    style_config=config.get("effects", {}).get("feature_animation", {}),
                )
                feature_clips.append(clip)

            logger.info("Combining video elements...")
            # Combine all elements with enhanced transitions
            final = CompositeVideoClip(
                [background, banner, welcome_text, *feature_clips], size=(1920, 1080)
            ).set_audio(audio)

            # Add global effects
            if config.get("effects", {}).get("global", {}).get("fade", True):
                final = final.fadein(1).fadeout(1)

            if config.get("effects", {}).get("global", {}).get("color_shift", False):
                final = final.fx(colorx, 1.1)

            if config.get("effects", {}).get("global", {}).get("wave", False):

                def global_wave(t):
                    return 1 + 0.05 * np.sin(t * 3)

                final = final.resize(lambda t: global_wave(t))

            logger.info("Writing video file...")
            final.write_videofile(
                self.output_path,
                fps=config.get("rendering", {}).get("fps", 24),
                codec="libx264",
                audio_codec="aac",
                threads=config.get("rendering", {}).get("threads", 4),
                preset=config.get("rendering", {}).get("preset", "medium"),
                bitrate=config.get("rendering", {}).get("bitrate", "8000k"),
            )

            logger.info(f"Video rendered successfully: {self.output_path}")
            return self.output_path

        except Exception as e:
            logger.error(f"Error rendering video: {e}")
            raise


def main():
    """Main function to render the video."""
    try:
        renderer = VideoRenderer()
        output_path = renderer.render_video()
        print(f"\nVideo rendered successfully: {output_path}")
        print("\nNext steps:")
        print("1. Review the video in the exports directory")
        print("2. Upload to YouTube")
        print("3. Add thumbnail, description, and hashtags")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
