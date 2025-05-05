"""
AI Agent with enhanced security and blockchain capabilities.
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from .voice import VoiceProcessor
from .memory import MemoryStore
from .core.phantom_mcp import PhantomMCP
from .blockchain import BlockchainAgent
from .security.security_agent import SecurityAgent
from .blockchain.wallet_manager import WalletManager
from .phantom.phantom_core import PhantomCore
from .ai.recommendation_engine import RecommendationEngine
from .voice.voice_enhancement import VoiceEnhancer
from .context.context_manager import ContextManager
from .core.startup_manager import StartupManager

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        """Initialize AI Agent with enhanced capabilities."""
        self.running = False
        self.startup_manager = StartupManager()
        
        # Initialize components
        self.memory = MemoryStore()
        self.voice_processor = VoiceProcessor()
        self.phantom_mcp = PhantomMCP()
        self.phantom = PhantomCore()
        self.security = SecurityAgent()
        self.wallet = WalletManager()
        self.blockchain = BlockchainAgent(self.memory, self.voice_processor)
        self.recommendation_engine = RecommendationEngine()
        self.voice_enhancer = VoiceEnhancer()
        self.context_manager = ContextManager()
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the AI Agent with managed startup."""
        try:
            logger.info("Starting AI Agent...")
            self.running = True
            
            # Register components with dependencies
            await self.startup_manager.register_component("memory", self.memory)
            await self.startup_manager.register_component("phantom_mcp", self.phantom_mcp)
            await self.startup_manager.register_component("phantom_core", self.phantom)
            await self.startup_manager.register_component("security", self.security, ["phantom_mcp"])
            await self.startup_manager.register_component("wallet", self.wallet)
            await self.startup_manager.register_component("blockchain", self.blockchain, ["wallet"])
            await self.startup_manager.register_component("voice_enhancer", self.voice_enhancer)
            await self.startup_manager.register_component("voice_processor", self.voice_processor, ["voice_enhancer"])
            await self.startup_manager.register_component("recommendation_engine", self.recommendation_engine, ["memory"])
            await self.startup_manager.register_component("context_manager", self.context_manager, ["memory"])
            
            # Initialize all components
            await self.startup_manager.initialize_system()
            
            # Log startup
            self.phantom.log_event("System Startup", "AI Agent initialization complete")
            
            # Start continuous tasks
            self._task = asyncio.create_task(self._run())
            
            logger.info("AI Agent started successfully")
            
        except Exception as e:
            error_msg = f"Failed to start AI Agent: {str(e)}"
            self.phantom.log_event("Startup Error", error_msg, "ERROR")
            logger.error(error_msg)
            await self.stop()
            raise
            
    async def _run(self):
        """Main agent loop with enhanced processing."""
        try:
            while self.running:
                # Process voice commands with enhancement
                audio_data = await self.voice_processor.get_audio()
                if audio_data is not None:
                    # Enhance audio
                    enhanced_audio, metrics = await self.voice_enhancer.enhance_audio(audio_data)
                    
                    # Process enhanced audio
                    command = await self.voice_processor.process_audio(enhanced_audio)
                    if command:
                        # Update context
                        self.context_manager.push_context("voice_command", {
                            "command": command,
                            "audio_metrics": metrics
                        })
                        
                        # Get recommendation
                        context = self.context_manager.get_current_context()
                        recommendation = await self.recommendation_engine.get_recommendation(context.data)
                        
                        # Process command with recommendation
                        await self.process_command_with_recommendation(command, recommendation)
                
                # Monitor system security
                await self.security.monitor_system()
                
                # Scan environment
                scan_result = self.phantom.scan_environment()
                if scan_result["threat_level"] > 0:
                    await self.handle_security_threat(scan_result)
                
                # Save logs periodically
                self.phantom.save_log()
                
                # Allow other tasks to run
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("AI Agent loop cancelled")
            self.phantom.log_event("System Loop", "Agent loop cancelled")
        except Exception as e:
            error_msg = f"Error in AI Agent loop: {str(e)}"
            self.phantom.log_event("System Error", error_msg, "ERROR")
            logger.error(error_msg)
            self.running = False
            
    async def process_command_with_recommendation(self, command: str, recommendation: Dict[str, Any]):
        """Process command with AI recommendations."""
        try:
            # Log command
            self.phantom.log_event("Voice Command", f"Processing: {command}")
            
            # Generate response using recommendation
            response = await self._generate_enhanced_response(command, recommendation)
            
            # Enhance voice output
            voice_params = recommendation.get("delivery", {})
            enhanced_audio = await self.voice_enhancer.enhance_voice_output(
                response,
                voice_params
            )
            
            # Play enhanced response
            await self.voice_processor.play_audio(enhanced_audio)
            
            # Update context with response
            self.context_manager.update_current_context({
                "response": response,
                "recommendation_used": recommendation
            })
            
        except Exception as e:
            await self.handle_error(e, "command_processing")
            
    async def _generate_enhanced_response(self, command: str, recommendation: Dict[str, Any]) -> str:
        """Generate enhanced response using AI recommendations."""
        try:
            content = recommendation.get("content", {})
            message = content.get("message", "")
            suggestions = content.get("suggestions", [])
            
            # Combine message and suggestions
            response = message
            if suggestions:
                response += "\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            return f"I understood: {command}"
            
    async def stop(self):
        """Stop the AI Agent with managed shutdown."""
        try:
            logger.info("Stopping AI Agent...")
            self.running = False
            
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            
            # Save final context
            await self.context_manager.save_context_snapshot("shutdown")
            
            # Stop all components
            await self.startup_manager.shutdown_system()
            
            logger.info("AI Agent stopped successfully")
            
        except Exception as e:
            error_msg = f"Error stopping AI Agent: {str(e)}"
            logger.error(error_msg)
            self.phantom.log_event("Shutdown Error", error_msg, "ERROR")
            
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status with enhanced metrics."""
        try:
            phantom_status = self.phantom.get_status()
            context_analysis = await self.context_manager.analyze_context()
            voice_metrics = self.voice_enhancer.get_voice_quality_metrics()
            system_status = self.startup_manager.get_system_status()
            health_status = await self.startup_manager.health_check()
            
            return {
                "running": self.running,
                "system_health": self.phantom_mcp.state.system_health,
                "security_status": self.security.get_security_status(),
                "wallet_info": self.wallet.get_wallet_info(),
                "memory_entries": len(self.memory.log),
                "phantom_status": phantom_status,
                "context_status": context_analysis,
                "voice_metrics": voice_metrics,
                "system_status": system_status,
                "component_health": health_status
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {"error": str(e)}
            
    async def restart_component(self, component_name: str):
        """Restart a specific component."""
        try:
            await self.startup_manager.restart_component(component_name)
            logger.info(f"Component {component_name} restarted successfully")
        except Exception as e:
            logger.error(f"Error restarting component {component_name}: {e}")
            raise
            
    async def handle_error(self, error: Exception, context: str = "general"):
        """Handle errors with enhanced recovery."""
        try:
            error_msg = f"Error in {context}: {str(error)}"
            logger.error(error_msg)
            
            # Save error context
            self.context_manager.push_context("error", {
                "error": str(error),
                "context": context,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check component health
            health_status = await self.startup_manager.health_check()
            
            # Attempt recovery for failed components
            for component, status in health_status.items():
                if status["status"] == "error":
                    try:
                        await self.restart_component(component)
                    except Exception as e:
                        logger.error(f"Recovery failed for {component}: {e}")
            
            # Get recommendation for error
            error_recommendation = await self.recommendation_engine.get_recommendation({
                "type": "error_handling",
                "error": str(error),
                "context": context,
                "health_status": health_status
            })
            
            # Generate error response
            response = error_recommendation.get("content", {}).get(
                "message",
                f"An error occurred: {str(error)}"
            )
            
            # Enhance and play error response
            voice_params = error_recommendation.get("delivery", {})
            enhanced_audio = await self.voice_enhancer.enhance_voice_output(
                response,
                voice_params
            )
            await self.voice_processor.play_audio(enhanced_audio)
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            # Fallback to basic error handling
            await self.voice_processor.respond_with_voice(f"An error occurred: {str(error)}")
            
    def get_memory_analysis(self) -> Dict[str, Any]:
        """Get analysis of agent's memory and performance."""
        return self.memory.analyze_performance()
        
    def get_evolution_history(self) -> list:
        """Get the history of evolutionary improvements."""
        return self.phantom_mcp.evolution_history

    def set_context(self, context_type: str, data: dict):
        """Set the current context for the AI Agent."""
        self.context_manager.push_context(context_type, data)
        
    def get_context(self) -> dict:
        """Get the current context."""
        return self.context_manager.get_current_context()
        
    def get_recent_memories(self, memory_type: Optional[str] = None, limit: int = 10):
        """Retrieve recent memories of the specified type."""
        return self.memory_store.retrieve(memory_type=memory_type, limit=limit)

    async def handle_security_threat(self, scan_result: Dict[str, Any]):
        """Handle detected security threats."""
        try:
            threat_level = scan_result["threat_level"]
            self.phantom.log_event(
                "Security Threat",
                f"Detected threat level {threat_level}",
                "WARNING"
            )
            
            # Create security checkpoint
            await self.phantom_mcp.create_backup("security_threat")
            
            # Trigger system optimization
            await self.phantom_mcp.improve_system("threat_mitigation")
            
            # Notify through voice
            await self.voice_processor.respond_with_voice(
                f"Security threat detected. Threat level {threat_level}"
            )
            
        except Exception as e:
            error_msg = f"Error handling security threat: {str(e)}"
            self.phantom.log_event("Security Error", error_msg, "ERROR")
            logger.error(error_msg) 