"""
Combined video rendering script for Njanja AI Empire intro
Supports both simple and enhanced rendering modes with presets
"""
import os
import json
import argparse
from simple_render import render_simple_video
from render_njanja_intro import VideoRenderer

def load_preset(preset_name):
    """Load a rendering preset from the presets file."""
    presets_path = os.path.join("site", "marketing", "assets", "render_presets.json")
    try:
        with open(presets_path, 'r') as f:
            presets = json.load(f)
            if preset_name in presets['presets']:
                return presets['presets'][preset_name]
            else:
                print(f"Warning: Preset '{preset_name}' not found. Using standard preset.")
                return presets['presets']['standard']
    except Exception as e:
        print(f"Warning: Could not load presets file: {e}")
        return None

def render_video(mode='simple', config=None, preset=None):
    """
    Render video in specified mode.
    
    Args:
        mode (str): 'simple' or 'enhanced'
        config (dict): Custom configuration
        preset (str): Name of preset to use
    """
    # Load preset if specified
    if preset:
        preset_config = load_preset(preset)
        if preset_config:
            # Merge preset with custom config
            if config:
                preset_config.update(config)
            config = preset_config
    
    if mode == 'simple':
        return render_simple_video(config)
    else:
        renderer = VideoRenderer()
        return renderer.render_video(config)

def main():
    """Main function to handle video rendering."""
    parser = argparse.ArgumentParser(description='Render Njanja AI Empire intro video')
    parser.add_argument('--mode', choices=['simple', 'enhanced'], default='simple',
                      help='Rendering mode: simple or enhanced')
    parser.add_argument('--config', type=str,
                      help='Path to custom config file')
    parser.add_argument('--preset', choices=['minimal', 'standard', 'premium', 'startup'],
                      default='standard', help='Rendering preset to use')
    
    args = parser.parse_args()
    
    try:
        # Load custom config if specified
        config = None
        if args.config:
            with open(args.config, 'r') as f:
                config = json.load(f)
        
        output_path = render_video(args.mode, config, args.preset)
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