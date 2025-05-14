"""
Script to generate placeholder avatar images for testing.
"""

from PIL import Image, ImageDraw
from pathlib import Path


def create_placeholder_avatar(expression: str, color: tuple, size: tuple = (200, 200)):
    """Create a placeholder avatar image with the given expression."""
    # Create new image with white background
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)

    # Draw face circle
    circle_radius = min(size) // 3
    center = (size[0] // 2, size[1] // 2)
    draw.ellipse(
        [
            (center[0] - circle_radius, center[1] - circle_radius),
            (center[0] + circle_radius, center[1] + circle_radius),
        ],
        outline="black",
        fill=color,
        width=2,
    )

    # Draw expression-specific features
    if expression == "calm":
        # Calm expression - neutral mouth, relaxed eyes
        draw.line(
            [(center[0] - 20, center[1] + 20), (center[0] + 20, center[1] + 20)],
            fill="black",
            width=2,
        )
        # Eyes
        draw.ellipse(
            [(center[0] - 30, center[1] - 20), (center[0] - 10, center[1] - 10)],
            fill="black",
        )
        draw.ellipse(
            [(center[0] + 10, center[1] - 20), (center[0] + 30, center[1] - 10)],
            fill="black",
        )

    elif expression == "excited":
        # Excited expression - big smile, wide eyes
        draw.arc(
            [(center[0] - 30, center[1] - 10), (center[0] + 30, center[1] + 30)],
            0,
            180,
            fill="black",
            width=2,
        )
        # Eyes
        draw.ellipse(
            [(center[0] - 35, center[1] - 25), (center[0] - 10, center[1] - 10)],
            fill="black",
        )
        draw.ellipse(
            [(center[0] + 10, center[1] - 25), (center[0] + 35, center[1] - 10)],
            fill="black",
        )

    elif expression == "attentive":
        # Attentive expression - slight smile, focused eyes
        draw.arc(
            [(center[0] - 20, center[1]), (center[0] + 20, center[1] + 20)],
            0,
            180,
            fill="black",
            width=2,
        )
        # Eyes
        draw.ellipse(
            [(center[0] - 30, center[1] - 20), (center[0] - 15, center[1] - 10)],
            fill="black",
        )
        draw.ellipse(
            [(center[0] + 15, center[1] - 20), (center[0] + 30, center[1] - 10)],
            fill="black",
        )

    else:  # neutral
        # Neutral expression - straight mouth, normal eyes
        draw.line(
            [(center[0] - 20, center[1] + 10), (center[0] + 20, center[1] + 10)],
            fill="black",
            width=2,
        )
        # Eyes
        draw.ellipse(
            [(center[0] - 30, center[1] - 20), (center[0] - 15, center[1] - 10)],
            fill="black",
        )
        draw.ellipse(
            [(center[0] + 15, center[1] - 20), (center[0] + 30, center[1] - 10)],
            fill="black",
        )

    return img


def create_animation_frames(expression: str, color: tuple, size: tuple = (200, 200)):
    """Create animation frames for an expression."""
    frames = {}

    # Create base expression
    base_img = create_placeholder_avatar(expression, color, size)
    frames["base"] = base_img

    # Create blink frame
    blink_img = base_img.copy()
    draw = ImageDraw.Draw(blink_img)
    width, height = size
    center_x = width // 2
    center_y = height // 2

    # Draw closed eyes
    draw.line(
        [(center_x - 30, center_y - 20), (center_x - 10, center_y - 20)],
        fill="black",
        width=2,
    )
    draw.line(
        [(center_x + 10, center_y - 20), (center_x + 30, center_y - 20)],
        fill="black",
        width=2,
    )
    frames["blink"] = blink_img

    # Create speaking frame
    speak_img = base_img.copy()
    draw = ImageDraw.Draw(speak_img)

    # Draw open mouth
    if expression == "excited":
        # Wide open mouth for excited
        draw.ellipse(
            [(center_x - 25, center_y + 10), (center_x + 25, center_y + 30)],
            outline="black",
            width=2,
        )
    else:
        # Normal open mouth
        draw.ellipse(
            [(center_x - 20, center_y + 10), (center_x + 20, center_y + 25)],
            outline="black",
            width=2,
        )
    frames["speak"] = speak_img

    return frames


def main():
    """Generate all placeholder avatar images and animation frames."""
    # Create avatars directory if it doesn't exist
    avatar_dir = Path("assets/avatars")
    avatar_dir.mkdir(parents=True, exist_ok=True)

    # Expression configurations
    expressions = {
        "calm": (200, 255, 200),  # Light green
        "excited": (255, 200, 200),  # Light red
        "attentive": (200, 200, 255),  # Light blue
        "neutral": (240, 240, 240),  # Light gray
    }

    # Generate images and animation frames
    for expression, color in expressions.items():
        # Generate animation frames
        frames = create_animation_frames(expression, color)

        # Save base expression
        frames["base"].save(avatar_dir / f"avatar_{expression}.png")

        # Save animation frames
        frames["blink"].save(avatar_dir / f"avatar_{expression}_blink.png")
        frames["speak"].save(avatar_dir / f"avatar_{expression}_speak.png")

        print(f"Generated {expression} avatar and animation frames")


if __name__ == "__main__":
    main()
