"""
Main entry point for SecondBrain application.
"""
import logging
import sys
from pathlib import Path
from .gui.system_tray import SystemTrayApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path("logs/secondbrain.log"))
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    try:
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Start system tray application
        app = SystemTrayApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main() 