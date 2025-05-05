#!/usr/bin/env python3
"""
SecondBrain AI Agent with Phantom MCP and Voice Control
"""
import asyncio
import logging
import os
import signal
import sys
from dotenv import load_dotenv
from src.secondbrain.ai_agent import AIAgent
from src.secondbrain.gui import GUI
from src.secondbrain.phantom.ventilation import ventilate

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/.secondbrain/logs/agent.log"))
    ]
)

logger = logging.getLogger(__name__)

class SecondBrain:
    def __init__(self):
        self.agent = AIAgent()
        self.gui = GUI() if os.getenv("ENABLE_GUI", "true").lower() == "true" else None
        self.running = False
        
    async def start(self):
        """Start the SecondBrain system."""
        try:
            logger.info("Starting SecondBrain...")
            self.running = True
            
            # Register signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)
            
            # Start AI Agent
            await self.agent.start()
            
            # Start GUI if enabled
            if self.gui:
                self.gui.start()
            
            # Keep the main loop running
            while self.running:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error starting SecondBrain: {str(e)}")
            await self.stop()
            sys.exit(1)
            
    async def stop(self):
        """Stop the SecondBrain system gracefully."""
        try:
            logger.info("Stopping SecondBrain...")
            self.running = False
            
            # Stop AI Agent
            await self.agent.stop()
            
            # Stop GUI
            if self.gui:
                self.gui.stop()
            
            # Run ventilation protocol
            ventilate()
                
            logger.info("SecondBrain stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping SecondBrain: {str(e)}")
            sys.exit(1)
            
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.stop())

def main():
    """Main entry point."""
    try:
        # Check for required environment variables
        required_vars = ["OPENAI_API_KEY", "INFURA_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please set them in the .env file")
            sys.exit(1)
        
        # Create and start SecondBrain
        brain = SecondBrain()
        asyncio.run(brain.start())
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()