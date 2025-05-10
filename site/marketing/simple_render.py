"""
Enhanced simple video rendering script for Njanja AI Empire intro
"""
import os
from moviepy.editor import (
    AudioFileClip, ImageClip, TextClip, CompositeVideoClip,
    ColorClip, concatenate_videoclips, VideoFileClip
)
from moviepy.video.fx import fadein, fadeout, resize, mirror_x, rotate
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_gradient_background(duration, colors=None):
    """Create a gradient background with enhanced effects."""
    if colors is None:
        colors = [(0, 0, 0), (50, 50, 100)]
        
    def make_frame(t):
        progress = t / duration
        r = int(colors[0][0] * (1 - progress) + colors[1][0] * progress)
        g = int(colors[0][1] * (1 - progress) + colors[1][1] * progress)
        b = int(colors[0][2] * (1 - progress) + colors[1][2] * progress)
        frame = np.full((1080, 1920, 3), (r, g, b), dtype=np.uint8)
        
        # Add noise effect
        noise = np.random.normal(0, 10, frame.shape).astype(np.uint8)
        frame = np.clip(frame + noise, 0, 255).astype(np.uint8)
        
        return frame
        
    return VideoFileClip(make_frame, duration=duration)

def create_animated_text(text, duration, position, style=None):
    """Create animated text with enhanced effects."""
    if style is None:
        style = {}
        
    # Create base text
    text_clip = TextClip(
        text,
        fontsize=style.get('fontsize', 70),
        color=style.get('color', 'white'),
        font=style.get('font', 'Arial-Bold'),
        stroke_color=style.get('stroke_color', 'black'),
        stroke_width=style.get('stroke_width', 2),
        method='caption',
        align='center'
    ).set_duration(duration).set_position(position)
    
    # Add fade effects
    if style.get('fade', True):
        text_clip = text_clip.fadein(0.5).fadeout(0.5)
        
    # Add zoom effect
    if style.get('zoom', True):
        def zoom_effect(t):
            if t < 0.5:
                return 1 + 0.2 * t
            elif t > duration - 0.5:
                return 1 + 0.2 * (duration - t)
            return 1.2
        text_clip = text_clip.resize(lambda t: zoom_effect(t))
        
    # Add rotation effect
    if style.get('rotate', False):
        def rotation_effect(t):
            if t < 0.5:
                return 5 * (1 - t/0.5)
            return 0
        text_clip = text_clip.rotate(lambda t: rotation_effect(t))
        
    # Add wave effect
    if style.get('wave', False):
        def wave_effect(t):
            return 1 + 0.1 * np.sin(t * 10)
        text_clip = text_clip.resize(lambda t: wave_effect(t))
        
    return text_clip

def render_simple_video(config=None):
    """Render a simple version of the intro video with enhanced features."""
    if config is None:
        config = {}
        
    # Define paths
    base_dir = os.path.expanduser("~/Documents/SecondBrainApp")
    assets_dir = os.path.join(base_dir, "assets")
    exports_dir = os.path.join(base_dir, "exports")
    audio_path = os.path.join(assets_dir, "audio", "NjanjaIntro.mp3")
    banner_path = os.path.join(assets_dir, "branding", "Njanja_YouTube_Banner.png")
    output_path = os.path.join(exports_dir, "Njanja_Intro_60s.mp4")
    
    # Ensure directories exist
    os.makedirs(exports_dir, exist_ok=True)
    
    try:
        # Load assets
        logger.info("Loading audio file...")
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        # Create background
        logger.info("Creating background...")
        background = create_gradient_background(
            duration,
            colors=config.get('background_colors', [(0, 0, 0), (50, 50, 100)])
        )
        
        # Load and process banner
        logger.info("Loading banner image...")
        banner = ImageClip(banner_path).set_duration(duration)
        banner = banner.resize(width=1920).set_position("center")
        
        # Add banner effects
        if config.get('banner_zoom', True):
            def banner_zoom(t):
                if t < 2:
                    return 1 + 0.1 * t/2
                return 1.1
            banner = banner.resize(lambda t: banner_zoom(t))
            
        # Add banner rotation
        if config.get('banner_rotate', False):
            def banner_rotation(t):
                if t < 1:
                    return 2 * (1 - t)
                return 0
            banner = banner.rotate(lambda t: banner_rotation(t))
            
        # Create text overlays
        logger.info("Creating text overlays...")
        welcome_text = create_animated_text(
            config.get('title', "Welcome to Njanja AI Empire"),
            duration=5,
            position=("center", 100),
            style=config.get('title_style', {})
        )
        
        # Add features if specified
        feature_clips = []
        features = config.get('features', [])
        for i, (feature, start_time) in enumerate(features):
            clip = create_animated_text(
                feature,
                duration=4,
                position=("center", 300 + i * 100),
                style=config.get('feature_style', {})
            ).set_start(start_time)
            feature_clips.append(clip)
        
        # Combine everything
        logger.info("Combining video elements...")
        video = CompositeVideoClip([
            background,
            banner,
            welcome_text,
            *feature_clips
        ], size=(1920, 1080)).set_audio(audio)
        
        # Add global effects
        if config.get('global_fade', True):
            video = video.fadein(1).fadeout(1)
            
        if config.get('global_mirror', False):
            video = video.fx(mirror_x)
            
        if config.get('global_rotate', False):
            video = video.rotate(2)
        
        # Write video file
        logger.info("Writing video file...")
        video.write_videofile(
            output_path,
            fps=config.get('fps', 24),
            codec='libx264',
            audio_codec='aac',
            threads=config.get('threads', 4),
            preset=config.get('preset', 'medium'),
            bitrate=config.get('bitrate', '8000k')
        )
        
        logger.info(f"Video rendered successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error rendering video: {e}")
        raise

def main():
    """Main function to render the video."""
    try:
        # Example configuration
        config = {
            'title': "Welcome to Njanja AI Empire",
            'background_colors': [(0, 0, 0), (50, 50, 100)],
            'title_style': {
                'fontsize': 80,
                'color': 'white',
                'stroke_color': 'black',
                'stroke_width': 2,
                'fade': True,
                'zoom': True,
                'rotate': True,
                'wave': True
            },
            'features': [
                ("AI-Powered Business Solutions", 5),
                ("Automated Content Generation", 10),
                ("Smart Analytics & Insights", 15),
                ("24/7 Customer Support", 20)
            ],
            'feature_style': {
                'fontsize': 50,
                'color': '#00ff00',
                'fade': True,
                'zoom': True,
                'wave': True
            },
            'banner_zoom': True,
            'banner_rotate': True,
            'global_fade': True,
            'global_mirror': False,
            'global_rotate': False,
            'fps': 30,
            'threads': 4,
            'preset': 'medium',
            'bitrate': '8000k'
        }
        
        output_path = render_simple_video(config)
        print(f"\nVideo rendered successfully: {output_path}")
        print("\nNext steps:")
        print("1. Review the video in the exports directory")
        print("2. Upload to YouTube")
        print("3. Add thumbnail, description, and hashtags")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == '__main__':
    main() 