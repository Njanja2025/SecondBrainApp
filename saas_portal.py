"""
SecondBrainApp SaaS Portal
"""

import os
import logging
from pathlib import Path
from src.secondbrain.saas.portal import Portal
from src.secondbrain.utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run the SaaS portal."""
    try:
        # Load configuration
        config = Config()

        # Initialize portal
        portal = Portal(config)

        # Get server settings
        host = os.getenv("PORTAL_HOST", "0.0.0.0")
        port = int(os.getenv("PORTAL_PORT", 5000))
        debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

        logger.info(f"Starting SecondBrainApp SaaS Portal on {host}:{port}")
        portal.run(host=host, port=port, debug=debug)

    except Exception as e:
        logger.error(f"Failed to start portal: {e}")
        raise


if __name__ == "__main__":
    main()
