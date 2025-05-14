"""
Enhanced thumbnail generator for YouTube videos with advanced effects
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    def __init__(self):
        """Initialize the thumbnail generator."""
        self.assets_dir = "site/marketing/assets"
        self.exports_dir = "site/marketing/exports"
        self.banner_path = os.path.join(
            self.assets_dir, "branding", "Njanja_YouTube_Banner.png"
        )
        self.output_path = os.path.join(self.exports_dir, "thumbnail.png")

        # Ensure directories exist
        os.makedirs(self.exports_dir, exist_ok=True)

    def create_particle_overlay(self, size, num_particles=100):
        """Create a particle effect overlay."""
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for _ in range(num_particles):
            x = np.random.randint(0, size[0])
            y = np.random.randint(0, size[1])
            radius = np.random.randint(1, 3)
            alpha = np.random.randint(100, 200)
            color = (255, 255, 255, alpha)
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)

        return overlay

    def create_3d_text(self, text, font, color, style_config=None):
        """Create 3D text effect."""
        if style_config is None:
            style_config = {}

        # Create base text
        text_img = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)

        # Calculate text size and position
        text_width = draw.textlength(text, font=font)
        text_height = font.size
        position = ((1280 - text_width) // 2, (720 - text_height) // 2)

        # Draw 3D effect
        depth = style_config.get("depth", 5)
        for i in range(depth):
            offset = i
            shadow_color = tuple(max(0, c - 50) for c in color[:3]) + (color[3],)
            draw.text(
                (position[0] + offset, position[1] + offset),
                text,
                font=font,
                fill=shadow_color,
            )

        # Draw main text
        draw.text(position, text, font=font, fill=color)

        return text_img

    def create_gradient_overlay(
        self, size, colors, direction="vertical", style_config=None
    ):
        """Create an enhanced gradient overlay."""
        if style_config is None:
            style_config = {}

        gradient = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        # Add noise to gradient
        noise = np.random.normal(0, 10, size + (4,))
        noise = np.clip(noise, -20, 20)

        if direction == "vertical":
            for y in range(size[1]):
                r = int(np.interp(y, [0, size[1]], [colors[0][0], colors[1][0]]))
                g = int(np.interp(y, [0, size[1]], [colors[0][1], colors[1][1]]))
                b = int(np.interp(y, [0, size[1]], [colors[0][2], colors[1][2]]))
                a = int(np.interp(y, [0, size[1]], [colors[0][3], colors[1][3]]))

                # Add noise
                r = np.clip(r + noise[y, 0, 0], 0, 255)
                g = np.clip(g + noise[y, 0, 1], 0, 255)
                b = np.clip(b + noise[y, 0, 2], 0, 255)
                a = np.clip(a + noise[y, 0, 3], 0, 255)

                draw.line([(0, y), (size[0], y)], fill=(int(r), int(g), int(b), int(a)))
        else:  # horizontal
            for x in range(size[0]):
                r = int(np.interp(x, [0, size[0]], [colors[0][0], colors[1][0]]))
                g = int(np.interp(x, [0, size[0]], [colors[0][1], colors[1][1]]))
                b = int(np.interp(x, [0, size[0]], [colors[0][2], colors[1][2]]))
                a = int(np.interp(x, [0, size[0]], [colors[0][3], colors[1][3]]))

                # Add noise
                r = np.clip(r + noise[0, x, 0], 0, 255)
                g = np.clip(g + noise[0, x, 1], 0, 255)
                b = np.clip(b + noise[0, x, 2], 0, 255)
                a = np.clip(a + noise[0, x, 3], 0, 255)

                draw.line([(x, 0), (x, size[1])], fill=(int(r), int(g), int(b), int(a)))

        return gradient

    def apply_text_effects(self, text, font, position, color, style_config=None):
        """Apply enhanced text effects."""
        if style_config is None:
            style_config = {}

        # Use 3D text if enabled
        if style_config.get("3d", False):
            return self.create_3d_text(text, font, color, style_config)

        # Create text image
        text_img = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)

        # Draw shadow
        if style_config.get("shadow", True):
            shadow_offset = style_config.get("shadow_offset", 3)
            shadow_color = style_config.get("shadow_color", (0, 0, 0, 180))
            draw.text(
                (position[0] + shadow_offset, position[1] + shadow_offset),
                text,
                font=font,
                fill=shadow_color,
            )

        # Draw main text
        draw.text(position, text, font=font, fill=color)

        # Apply glow effect
        if style_config.get("glow", False):
            glow_radius = style_config.get("glow_radius", 2)
            glow_color = style_config.get("glow_color", color)
            text_img = text_img.filter(ImageFilter.GaussianBlur(glow_radius))
            draw = ImageDraw.Draw(text_img)
            draw.text(position, text, font=font, fill=glow_color)

        return text_img

    def create_thumbnail(
        self,
        title="Welcome to Njanja AI Empire",
        subtitle="AI-Powered Business Solutions",
        style_config=None,
    ):
        """Create a YouTube thumbnail with enhanced effects."""
        try:
            if style_config is None:
                style_config = {}

            logger.info("Loading banner image...")
            # Load and resize banner
            img = Image.open(self.banner_path)
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)

            # Apply image effects
            if style_config.get("enhance", True):
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)

            # Add gradient overlay
            if style_config.get("gradient", True):
                gradient_colors = style_config.get(
                    "gradient_colors", [(0, 0, 0, 128), (0, 0, 0, 64)]
                )
                gradient = self.create_gradient_overlay(
                    img.size,
                    gradient_colors,
                    direction=style_config.get("gradient_direction", "vertical"),
                    style_config=style_config,
                )
                img = Image.alpha_composite(img.convert("RGBA"), gradient)

            # Add particle effect
            if style_config.get("particles", False):
                particles = self.create_particle_overlay(
                    img.size, num_particles=style_config.get("num_particles", 100)
                )
                img = Image.alpha_composite(img, particles)

            # Add blur effect
            if style_config.get("blur", True):
                blur_radius = style_config.get("blur_radius", 2)
                img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            # Create drawing context
            draw = ImageDraw.Draw(img)

            # Load fonts
            title_font = ImageFont.truetype(
                style_config.get("title_font", "Arial Bold"),
                style_config.get("title_size", 80),
            )
            subtitle_font = ImageFont.truetype(
                style_config.get("subtitle_font", "Arial"),
                style_config.get("subtitle_size", 50),
            )

            # Calculate text positions
            title_width = draw.textlength(title, font=title_font)
            subtitle_width = draw.textlength(subtitle, font=subtitle_font)

            title_position = ((1280 - title_width) // 2, 200)
            subtitle_position = ((1280 - subtitle_width) // 2, 320)

            # Apply text effects
            title_img = self.apply_text_effects(
                title,
                title_font,
                title_position,
                style_config.get("title_color", (255, 255, 255)),
                style_config.get("title_effects", {}),
            )

            subtitle_img = self.apply_text_effects(
                subtitle,
                subtitle_font,
                subtitle_position,
                style_config.get("subtitle_color", (255, 255, 255)),
                style_config.get("subtitle_effects", {}),
            )

            # Composite text onto image
            img = Image.alpha_composite(img, title_img)
            img = Image.alpha_composite(img, subtitle_img)

            # Add logo or icon if available
            logo_path = os.path.join(self.assets_dir, "branding", "logo.png")
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo = logo.resize((100, 100), Image.Resampling.LANCZOS)

                # Apply logo effects
                if style_config.get("logo_glow", False):
                    logo = logo.filter(ImageFilter.GaussianBlur(2))

                img.paste(logo, (50, 50), logo if logo.mode == "RGBA" else None)

            # Add border if specified
            if style_config.get("border", False):
                border_width = style_config.get("border_width", 5)
                border_color = style_config.get("border_color", (255, 255, 255))
                img = ImageOps.expand(img, border=border_width, fill=border_color)

            # Save thumbnail
            img.save(self.output_path, "PNG")
            logger.info(f"Thumbnail generated: {self.output_path}")
            return self.output_path

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            raise


def main():
    """Generate sample thumbnail."""
    try:
        generator = ThumbnailGenerator()

        # Example style configuration
        style_config = {
            "enhance": True,
            "gradient": True,
            "gradient_colors": [(0, 0, 0, 128), (0, 0, 0, 64)],
            "gradient_direction": "vertical",
            "particles": True,
            "num_particles": 100,
            "blur": True,
            "blur_radius": 2,
            "title_font": "Arial Bold",
            "title_size": 80,
            "title_color": (255, 255, 255),
            "title_effects": {
                "3d": True,
                "depth": 5,
                "shadow": True,
                "shadow_offset": 3,
                "glow": True,
                "glow_radius": 2,
            },
            "subtitle_font": "Arial",
            "subtitle_size": 50,
            "subtitle_color": (255, 255, 255),
            "subtitle_effects": {"shadow": True, "shadow_offset": 2},
            "logo_glow": True,
            "border": True,
            "border_width": 5,
            "border_color": (255, 255, 255),
        }

        output_path = generator.create_thumbnail(style_config=style_config)
        print(f"\nThumbnail generated successfully: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
