"""
Brain Controller implementation for SecondBrain
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from src.secondbrain.core.strategic_planner import StrategicPlanner
from src.secondbrain.persona.adaptive_learning import PersonaLearningModule
from src.secondbrain.memory.diagnostic_memory_core import DiagnosticMemoryCore
from src.secondbrain.web_scout.global_scanner import GlobalScanner
from src.secondbrain.timeline.timeline_engine import TimelineEngine
from src.secondbrain.persona.samantha_voice_system import SamanthaVoiceSystem
from src.secondbrain.intel.global_web_scout import GlobalWebScout

logger = logging.getLogger(__name__)


class BrainController:
    """Central controller for SecondBrain's cognitive functions."""

    def __init__(
        self,
        memory_core: DiagnosticMemoryCore,
        learning_module: PersonaLearningModule,
        strategic_planner: StrategicPlanner,
    ):
        """Initialize the Brain Controller."""
        self.memory_core = memory_core
        self.learning_module = learning_module
        self.strategic_planner = strategic_planner
        self.running = False
        self.emotional_state = "neutral"
        self.last_analysis = None

        # Initialize global scanner and timeline engine
        self.scanner = GlobalScanner(
            sources=["GoogleNews", "Twitter", "GitHub", "Arxiv"]
        )
        self.timeline = TimelineEngine()
        self.samantha = SamanthaVoiceSystem()
        self.web_scout = GlobalWebScout()

    async def initialize(self):
        """Initialize the brain controller."""
        logger.info("Initializing Brain Controller...")
        self.running = True

        try:
            # Schedule initial analysis tasks
            self._schedule_initial_tasks()

            # Start background loops
            asyncio.create_task(self._analysis_loop())
            asyncio.create_task(self._planning_loop())
            asyncio.create_task(self.monitor_world())
            asyncio.create_task(self._timeline_check_loop())
            asyncio.create_task(self.web_scout.monitor())

            # Initialize timeline
            self.timeline.expand_future_nodes()
            self.timeline.alert_user_if("AI evolution, world shift")

            logger.info("Brain controller initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize brain controller: {str(e)}")
            raise

    def _schedule_initial_tasks(self):
        """Schedule initial system tasks."""
        now = datetime.now()

        # Schedule emotional analysis
        self.strategic_planner.schedule_task(
            "Review emotional response trends",
            (now + timedelta(days=1)).isoformat(),
            category="analysis",
            priority=3,
            recurring="daily",
            context={"type": "emotional_analysis"},
        )

        # Schedule learning assessment
        self.strategic_planner.schedule_task(
            "Assess learning progress",
            (now + timedelta(days=7)).isoformat(),
            category="learning",
            priority=2,
            recurring="weekly",
            context={"type": "learning_assessment"},
        )

        # Schedule system adaptation review
        self.strategic_planner.schedule_task(
            "Review system adaptations",
            (now + timedelta(days=30)).isoformat(),
            category="adaptation",
            priority=2,
            recurring="monthly",
            context={"type": "adaptation_review"},
        )

    async def monitor_world(self):
        """Start monitoring the world state."""
        logger.info("Starting world monitoring...")

        try:
            trends = await self.scanner.collect_context()
            # Link trends to persona or strategy modules
            self.update_persona_context(trends)
            self.predictive_core.ingest(trends)
        except Exception as e:
            logger.error(f"Error in world monitoring: {str(e)}")

    def update_persona_context(self, trends: Dict[str, Any]):
        """Update persona with new global context."""
        if trends and self.learning_module:
            self.learning_module.learn_from_interaction(
                "global_trends", str(trends), "analytical", {"type": "world_update"}
            )

    async def process_voice_input(
        self, text: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process voice input with context.

        Args:
            text: Voice input text
            context: Additional context information

        Returns:
            Dict containing response and metadata
        """
        try:
            # Record the input
            self.memory_core.record_event(
                f"Processing voice input: {text[:50]}...", "info"
            )

            # Let the learning module analyze the interaction
            self.learning_module.learn_from_interaction(
                "voice_input", text, "neutral", context
            )

            # Get strategic response
            response = await self.strategic_planner.plan_response(text, context)

            return response

        except Exception as e:
            error_msg = f"Error processing voice input: {str(e)}"
            logger.error(error_msg)
            self.memory_core.record_event(error_msg, "error")
            return {
                "text": "I encountered an error processing your input.",
                "emotion": "concerned",
                "error": str(e),
            }

    async def speak(self, text: str):
        """
        Speak the given text.

        Args:
            text: Text to speak
        """
        logger.info(f"Speaking: {text}")
        # TODO: Implement text-to-speech
        pass

    async def _analysis_loop(self):
        """Background loop for continuous system analysis."""
        while True:
            try:
                # Analyze learning progress
                behavior = self.learning_module.summarize_behavior()

                # Check emotional stability
                emotions = self.learning_module.analyze_emotional_trends()

                # Record analysis
                self.last_analysis = {
                    "timestamp": datetime.now().isoformat(),
                    "behavior": behavior,
                    "emotions": emotions,
                }

                # Suggest improvements
                if emotions.get("stability", 1.0) < 0.7:
                    self.strategic_planner.schedule_task(
                        "Emotional stability optimization",
                        (datetime.now() + timedelta(hours=1)).isoformat(),
                        category="optimization",
                        priority=4,
                        context={"trigger": "emotional_instability"},
                    )

                await asyncio.sleep(3600)  # Analyze every hour

            except Exception as e:
                logger.error(f"Error in analysis loop: {str(e)}")
                await asyncio.sleep(300)

    async def _planning_loop(self):
        """Background loop for strategic planning."""
        while True:
            try:
                # Get task suggestions
                suggestions = self.strategic_planner.get_task_suggestions(
                    self.memory_core, self.learning_module
                )

                # Schedule suggested tasks
                for suggestion in suggestions:
                    self.strategic_planner.schedule_task(
                        description=suggestion["description"],
                        due_date=(datetime.now() + timedelta(hours=24)).isoformat(),
                        category=suggestion["type"],
                        priority=suggestion["priority"],
                        context=suggestion["context"],
                    )

                # Analyze load and adjust if needed
                load = self.strategic_planner.predict_future_load()
                if load["total_upcoming"] > 20:
                    self.memory_core.record_event(
                        "High task load detected, adjusting priorities", "warning"
                    )

                await asyncio.sleep(1800)  # Plan every 30 minutes

            except Exception as e:
                logger.error(f"Error in planning loop: {str(e)}")
                await asyncio.sleep(300)

    async def _timeline_check_loop(self):
        """Background loop for checking timeline predictions."""
        while True:
            try:
                # Check for future events
                future_event = self.timeline.forecast()
                if future_event:
                    # Adapt to the future event
                    self.samantha.adapt_to_future(future_event)

                    # Announce the event through voice
                    self.samantha.announce_future_event(future_event)

                    # Register the forecast and log
                    self.timeline.register_forecast(future_event)
                    logger.info(f"[Timeline Engine] Future Event: {future_event}")

                    # Record in memory core
                    self.memory_core.record_event(
                        f"Future event detected: {future_event['event']}",
                        "info",
                        {"event_data": future_event},
                    )

                # Check for new web trends
                trends = self.web_scout.get_latest_trends(limit=5)
                for trend in trends:
                    if self._is_significant_trend(trend):
                        await self._announce_trend(trend)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error in timeline check loop: {str(e)}")
                await asyncio.sleep(300)

    def _is_significant_trend(self, trend: Dict[str, Any]) -> bool:
        """Check if a trend is significant enough to announce."""
        keywords = trend.get("keywords", [])
        high_priority = ["AI", "quantum", "security"]
        return any(k in keywords for k in high_priority)

    async def _announce_trend(self, trend: Dict[str, Any]) -> None:
        """Announce a significant trend through Samantha."""
        try:
            # Format trend for announcement
            keywords = ", ".join(trend.get("keywords", []))
            source = trend.get("source", "unknown source")
            preview = trend.get("preview", "").split(".")[0]  # First sentence

            announcement = {
                "event": f"New trend detected: {preview}",
                "type": "web_trend",
                "confidence": trend.get("confidence", 0.7),
                "source": source,
                "keywords": keywords,
            }

            # Announce through Samantha
            self.samantha.announce_future_event(announcement)

            # Record in memory
            self.memory_core.record_event(
                f"Web trend announced: {keywords}", "info", {"trend_data": trend}
            )

        except Exception as e:
            logger.error(f"Error announcing trend: {e}")
