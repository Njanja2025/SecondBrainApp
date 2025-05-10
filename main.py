#!/usr/bin/env python3
"""
SecondBrain AI Agent with Phantom MCP and Voice Control
"""
import asyncio
import logging
import os
import signal
import sys
from threading import Thread
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from src.secondbrain.ai_agent import AIAgent
from src.secondbrain.gui import GUI
from src.secondbrain.phantom.ventilation import ventilate
from src.secondbrain.memory.diagnostic_memory_core import DiagnosticMemoryCore
from src.secondbrain.persona.adaptive_learning import PersonaLearningModule
from src.secondbrain.core.strategic_planner import StrategicPlanner
from src.secondbrain.brain_controller import BrainController
from src.secondbrain.cloud.test_runner import BackupTestRunner
from src.secondbrain.cloud.log_reporter import BackupLogReport
from src.secondbrain.web.web_binding import WebBinding

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SecondBrain:
    def __init__(self):
        """Initialize the SecondBrain system."""
        # Initialize core components
        self.memory_core = DiagnosticMemoryCore()
        self.learning_module = PersonaLearningModule()
        self.strategic_planner = StrategicPlanner()
        
        # Initialize brain controller
        self.brain = BrainController(
            memory_core=self.memory_core,
            learning_module=self.learning_module,
            strategic_planner=self.strategic_planner
        )
        
        # Initialize other components
        self.agent = AIAgent()
        self.gui = GUI() if os.getenv("ENABLE_GUI", "true").lower() == "true" else None
        self.running = False
        
        # Initialize backup components
        self.backup_runner = BackupTestRunner()
        self.web_binding = WebBinding()
        
    async def trigger_backup_on_start(self):
        """Run startup backup and sync operations."""
        try:
            logger.info("Initiating startup backup + log flow...")
            
            # Run backup tests
            await self.backup_runner.run_memory_backup_test()
            await self.backup_runner.run_voice_log_backup_test()
            await self.backup_runner.run_dns_health_test()
            
            # Generate and email report
            log = BackupLogReport()
            log.log_event("backup", "Auto-triggered on app startup")
            report_path = log.generate_report()
            
            # Configure web binding
            if os.getenv("CONFIGURE_WEB_BINDING", "true").lower() == "true":
                self.web_binding.setup()
            
            self.memory_core.record_event("Startup backup and sync completed", "info")
            await self.brain.speak("Startup backup and sync completed.")
            
        except Exception as e:
            error_msg = f"Startup backup failed: {str(e)}"
            logger.error(error_msg)
            self.memory_core.record_event(error_msg, "error")
            await self.brain.speak("Startup backup failed.")
            
    async def start(self):
        """Start the SecondBrain system."""
        try:
            logger.info("Starting SecondBrain...")
            self.running = True
            
            # Register signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)
            
            # Initialize brain controller
            await self.brain.initialize()
            self.memory_core.record_event("Brain controller initialized", "info")
            
            # Run startup backup in background thread
            Thread(target=lambda: asyncio.run(self.trigger_backup_on_start())).start()
            
            # Start world monitoring
            await self.brain.monitor_world()
            self.memory_core.record_event("World monitoring initialized", "info")
            self.learning_module.learn_from_interaction(
                "world_monitor",
                "Global monitoring activated",
                "analytical",
                {"event": "monitor_startup"}
            )
            
            # Start AI Agent
            await self.agent.start()
            self.memory_core.record_event("AI Agent started successfully", "info")
            self.learning_module.learn_from_interaction(
                "system_start",
                "AI Agent initialized",
                "neutral",
                {"event": "system_startup"}
            )
            
            # Start GUI if enabled
            if self.gui:
                self.gui.start()
                self.memory_core.record_event("GUI interface initialized", "info")
                self.learning_module.learn_from_interaction(
                    "gui_start",
                    "GUI interface activated",
                    "neutral",
                    {"event": "gui_startup"}
                )
            
            # Keep the main loop running
            while self.running:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            error_msg = f"Error starting SecondBrain: {str(e)}"
            logger.error(error_msg)
            self.memory_core.record_event(error_msg, "error")
            self.learning_module.learn_from_interaction(
                "system_error",
                error_msg,
                "error",
                {"event": "system_error", "error": str(e)}
            )
            await self.stop()
            sys.exit(1)
            
    async def process_voice_command(self, text: str) -> Dict[str, Any]:
        """
        Process voice commands with emotional awareness.
        
        Args:
            text: Voice command text
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Process through brain controller
            response = await self.brain.process_voice_input(
                text,
                {"source": "voice_command"}
            )
            
            # Record successful processing
            self.memory_core.record_event(
                f"Processed voice command: {text[:50]}...",
                "info"
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing voice command: {str(e)}"
            self.memory_core.record_event(error_msg, "error")
            return {
                "text": "I encountered an error processing your command.",
                "emotion": "concerned",
                "error": str(e)
            }
            
    async def stop(self):
        """Stop the SecondBrain system gracefully."""
        try:
            logger.info("Stopping SecondBrain...")
            self.running = False
            
            # Stop AI Agent
            await self.agent.stop()
            self.memory_core.record_event("AI Agent stopped", "info")
            self.learning_module.learn_from_interaction(
                "system_stop",
                "AI Agent shutdown",
                "neutral",
                {"event": "system_shutdown"}
            )
            
            # Stop GUI
            if self.gui:
                self.gui.stop()
                self.memory_core.record_event("GUI interface terminated", "info")
                self.learning_module.learn_from_interaction(
                    "gui_stop",
                    "GUI interface terminated",
                    "neutral",
                    {"event": "gui_shutdown"}
                )
            
            # Export memory before ventilation
            try:
                self.memory_core.export_memory("system_memory.json")
                self.memory_core.record_event("Memory exported successfully", "info")
                
                # Save learning module memory
                self.learning_module.save_memory("long_term_persona.json")
                self.learning_module.learn_from_interaction(
                    "memory_save",
                    "Long-term memory saved",
                    "neutral",
                    {"event": "memory_export"}
                )
                
                # Save strategic planner state
                self.strategic_planner._auto_save()
                
            except Exception as e:
                error_msg = f"Failed to export memory: {str(e)}"
                self.memory_core.record_event(error_msg, "error")
                self.learning_module.learn_from_interaction(
                    "memory_error",
                    error_msg,
                    "error",
                    {"event": "memory_export_error", "error": str(e)}
                )
            
            # Run ventilation protocol
            ventilate()
            self.memory_core.record_event("Ventilation protocol completed", "info")
            self.learning_module.learn_from_interaction(
                "ventilation",
                "System ventilation complete",
                "neutral",
                {"event": "ventilation_complete"}
            )
                
            logger.info("SecondBrain stopped successfully")
            
        except Exception as e:
            error_msg = f"Error stopping SecondBrain: {str(e)}"
            logger.error(error_msg)
            self.memory_core.record_event(error_msg, "error")
            self.learning_module.learn_from_interaction(
                "shutdown_error",
                error_msg,
                "error",
                {"event": "shutdown_error", "error": str(e)}
            )
            sys.exit(1)
            
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received signal {signum}")
        self.memory_core.record_event(f"Received system signal: {signum}", "warning")
        self.learning_module.learn_from_interaction(
            "system_signal",
            f"Received signal {signum}",
            "warning",
            {"event": "system_signal", "signal": signum}
        )
        asyncio.create_task(self.stop())

def main():
    """Main entry point."""
    try:
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