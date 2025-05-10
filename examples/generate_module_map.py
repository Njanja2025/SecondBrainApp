"""
Example script for generating the SecondBrainApp module map with enhanced features
"""
import logging
from pathlib import Path
from src.secondbrain.visualization.module_map import (
    generate_module_map,
    ModuleType,
    ModuleConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Generate the module map
        output_path = generate_module_map()
        
        print("\nModule Map Generated:")
        print(f"Path: {output_path}")
        
        print("\nModule Types:")
        print("1. Core Components:")
        print("   - SecondBrainApp 2025 (Main application framework)")
        print("   - Evolver Engine (Core evolution engine)")
        print("   - Phantom AI Core (AI processing engine)")
        
        print("\n2. Major MCP Modules:")
        print("   - Wealth MCP (Wealth management system)")
        print("   - Companion MCP (AI companion system)")
        print("   - Engineering MCP (Engineering tools)")
        print("   - Security Core (Security framework)")
        
        print("\n3. Wealth MCP Features:")
        print("   - Digital Product Store")
        print("   - Affiliate Mall")
        print("   - Dropshipping Hub")
        print("   - Faceless Content")
        print("   - AI Content Services")
        print("   - Book Publishing")
        print("   - Email Funnel System")
        print("   - Ad Agent System")
        
        print("\n4. Companion MCP Features:")
        print("   - Voice Journaling")
        print("   - Samantha Voice Sync")
        print("   - Academic & Sermon Writer")
        print("   - Emotional Intelligence Layer")
        
        print("\n5. Engineering MCP Features:")
        print("   - Game Generation System")
        print("   - Music Drafting + Video Integration")
        print("   - AI Blueprint & Terminal Studio")
        
        print("\nVisualization Features:")
        print("1. Enhanced Styling:")
        print("   - Color-coded modules by type")
        print("   - Consistent font styling")
        print("   - Professional layout")
        print("   - Clear module relationships")
        
        print("\n2. Interactive Elements:")
        print("   - Module tooltips with descriptions")
        print("   - Hierarchical organization")
        print("   - Visual grouping by type")
        
        print("\n3. Technical Details:")
        print("   - High-resolution output (300 DPI)")
        print("   - Vector-based rendering")
        print("   - Automatic layout optimization")
        print("   - Clean file management")
        
        print("\n4. Module Relationships:")
        print("   - Core dependencies")
        print("   - Feature hierarchies")
        print("   - System integration points")
        print("   - Security boundaries")
        
        print("\n5. Quality Features:")
        print("   - Type-safe configuration")
        print("   - Robust error handling")
        print("   - Automatic directory creation")
        print("   - Clean temporary files")
        
    except Exception as e:
        logger.error(f"Failed to generate module map: {e}")
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 