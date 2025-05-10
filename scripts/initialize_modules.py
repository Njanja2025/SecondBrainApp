#!/usr/bin/env python3
"""
Module initialization script for SecondBrain application.
Creates and configures all system modules.
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.append(str(src_dir))

from secondbrain.config.system_map import SystemMap
from secondbrain.core.module_manager import ModuleManager

logger = logging.getLogger(__name__)

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def initialize_modules():
    """Initialize all system modules."""
    try:
        # Create system map and module manager
        system_map = SystemMap()
        manager = ModuleManager(system_map)
        
        # Initialize each module
        for module_id in system_map.modules:
            logger.info(f"Initializing module: {module_id}")
            
            if manager.initialize_module(module_id):
                # Validate module
                issues = manager.validate_module(module_id)
                if issues:
                    logger.warning(f"Module {module_id} has validation issues:")
                    for issue in issues:
                        logger.warning(f"  - {issue}")
                else:
                    logger.info(f"Module {module_id} initialized successfully")
            else:
                logger.error(f"Failed to initialize module {module_id}")
        
        logger.info("Module initialization complete")
        
    except Exception as e:
        logger.error(f"Module initialization failed: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point."""
    setup_logging()
    logger.info("Starting module initialization")
    initialize_modules()

if __name__ == "__main__":
    main() 