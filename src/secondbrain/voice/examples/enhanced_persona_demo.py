"""
Enhanced demo script for SecondBrain voice persona system with advanced scenario simulation.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any
from ..voice_enhancement import VoiceEnhancer
from ..voice_persona import EmotionType, VoiceStyle
from ..config import CONFIG
from ...memory.persona_memory import MemoryEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bind_memory(persona):
    """Bind memory engine to a persona."""
    persona.memory_engine = MemoryEngine()
    persona.memory_engine.link_to(persona.name)
    persona.enable_memory_tracking = True
    logger.info(f"Memory tracking enabled for {persona.name}")


def enable_voice_output(persona):
    """Enable voice output for a persona."""
    persona.enable_voice()
    logger.info(f"Voice output enabled for {persona.name}")


class ScenarioSimulator:
    def __init__(self, enhancer: VoiceEnhancer):
        self.enhancer = enhancer
        self.interaction_results = []
        self.emotion_accuracy = {}
        self.trait_effectiveness = {}
        self.emotion_transitions = []

    async def run_morning_checkin_scenario(self):
        """Simulate a morning check-in scenario with focused user."""
        logger.info("\n=== Running Morning Check-in Scenario ===")

        context = {
            "time_of_day": "morning",
            "user_emotion": "focused",
            "conversation_topic": "project_progress",
            "user_intent": "status_review",
        }

        # Configure Samantha with confident traits
        self.enhancer.persona_manager.bind_voice_persona(
            name="Samantha",
            tone="confident",
            emotion_range=["focused", "calm", "encouraging", "professional"],
            memory_persistence=True,
            command_mode=True,
        )

        # Enable memory tracking for Samantha
        samantha = self.enhancer.persona_manager.get_persona("Samantha")
        if samantha:
            bind_memory(samantha)
            enable_voice_output(samantha)

        # Simulate the interaction flow
        interactions = [
            {
                "message": "Good morning Samantha, can you brief me on today's tasks?",
                "emotion": EmotionType.CALM,
                "expected_traits": ["confident", "focused"],
                "expected_tone": "professional",
            },
            {
                "message": "I see three priority items on your schedule.",
                "emotion": EmotionType.FOCUSED,
                "expected_traits": ["efficient", "clear"],
                "expected_tone": "informative",
            },
            {
                "message": "Would you like me to help you plan the optimal sequence?",
                "emotion": EmotionType.ENCOURAGING,
                "expected_traits": ["helpful", "proactive"],
                "expected_tone": "supportive",
            },
        ]

        for interaction in interactions:
            result = self.enhancer.enhance_voice(
                interaction["message"],
                persona_name="Samantha",
                emotion=interaction["emotion"],
                context=context,
            )

            # Speak the enhanced response
            if samantha:
                samantha.speak(
                    result["enhanced"], emotion=interaction["emotion"], context=context
                )

            # Validate emotion adaptation
            emotion_score = self._validate_emotion_adaptation(
                result["enhanced"], interaction["emotion"], interaction["expected_tone"]
            )

            # Validate personality traits
            trait_score = self._validate_personality_traits(
                result["enhanced"], interaction["expected_traits"]
            )

            # Record results
            self.interaction_results.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": interaction["message"],
                    "enhanced": result["enhanced"],
                    "emotion_score": emotion_score,
                    "trait_score": trait_score,
                    "context": context.copy(),
                }
            )

            # Rate the response based on combined score
            combined_score = (emotion_score + trait_score) / 2
            self.enhancer.rate_response(
                interaction["message"], combined_score, "Samantha"
            )

            logger.info(f"\nInteraction:")
            logger.info(f"Original: {interaction['message']}")
            logger.info(f"Enhanced: {result['enhanced']}")
            logger.info(f"Emotion Score: {emotion_score:.2f}")
            logger.info(f"Trait Score: {trait_score:.2f}")

    async def run_error_recovery_scenario(self):
        """Simulate an error recovery scenario with frustrated user."""
        logger.info("\n=== Running Error Recovery Scenario ===")

        # Initial context with user frustration
        context = {
            "time_of_day": "afternoon",
            "user_emotion": "frustrated",
            "conversation_topic": "system bug report",
            "user_intent": "seek resolution",
            "error_context": {
                "severity": "medium",
                "recurring": True,
                "impact": "workflow disruption",
            },
        }

        # Configure Samantha for empathetic error handling
        self.enhancer.persona_manager.bind_voice_persona(
            name="Samantha",
            tone="reassuring",
            emotion_range=["calm", "empathetic", "confident", "professional"],
            memory_persistence=True,
            command_mode=True,
        )

        # Check memory for similar past situations
        samantha = self.enhancer.persona_manager.get_persona("Samantha")
        if samantha and samantha.memory_engine:
            past_frustrations = samantha.memory_engine.retrieve(
                {"context.user_emotion": "frustrated"}
            )

            if past_frustrations:
                logger.info("\nAnalyzing past similar situations:")
                patterns = samantha.memory_engine.get_interaction_patterns()
                successful_responses = patterns["successful_responses"]

                if successful_responses:
                    logger.info("Found successful past responses to user frustration:")
                    for response in successful_responses[:3]:  # Show top 3
                        logger.info(f"- Context: {response['context']}")
                        logger.info(
                            f"  Effectiveness: {response['feedback']['effectiveness']:.2f}"
                        )

        # Simulate error recovery interaction flow
        interactions = [
            {
                "message": "Samantha, something's not working in the system again.",
                "emotion": EmotionType.CONCERNED,
                "expected_traits": ["empathetic", "attentive"],
                "expected_tone": "acknowledging",
                "user_emotional_state": "frustrated",
            },
            {
                "message": "I understand your frustration. Let me analyze the system status.",
                "emotion": EmotionType.CALM,
                "expected_traits": ["confident", "reassuring"],
                "expected_tone": "professional",
                "user_emotional_state": "anxious",
            },
            {
                "message": "I've identified the issue. Would you like me to guide you through the solution?",
                "emotion": EmotionType.ENCOURAGING,
                "expected_traits": ["helpful", "proactive"],
                "expected_tone": "supportive",
                "user_emotional_state": "receptive",
            },
        ]

        previous_emotional_state = "frustrated"

        for interaction in interactions:
            # Update context with current emotional state
            context["user_emotion"] = interaction["user_emotional_state"]

            result = self.enhancer.enhance_voice(
                interaction["message"],
                persona_name="Samantha",
                emotion=interaction["emotion"],
                context=context,
            )

            # Track emotional transition
            self.emotion_transitions.append(
                {
                    "from_state": previous_emotional_state,
                    "to_state": interaction["user_emotional_state"],
                    "persona_emotion": interaction["emotion"].name,
                    "effectiveness": 0.0,  # Will be updated after validation
                }
            )

            # Validate emotion adaptation
            emotion_score = self._validate_emotion_adaptation(
                result["enhanced"], interaction["emotion"], interaction["expected_tone"]
            )

            # Validate personality traits
            trait_score = self._validate_personality_traits(
                result["enhanced"], interaction["expected_traits"]
            )

            # Calculate emotional transition effectiveness
            transition_effectiveness = self._calculate_emotional_transition_score(
                previous_emotional_state,
                interaction["user_emotional_state"],
                emotion_score,
            )

            # Update the latest transition effectiveness
            self.emotion_transitions[-1]["effectiveness"] = transition_effectiveness

            # Record results with emotional transition data
            self.interaction_results.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": interaction["message"],
                    "enhanced": result["enhanced"],
                    "emotion_score": emotion_score,
                    "trait_score": trait_score,
                    "context": context.copy(),
                    "emotional_transition": {
                        "from": previous_emotional_state,
                        "to": interaction["user_emotional_state"],
                        "effectiveness": transition_effectiveness,
                    },
                }
            )

            # Speak the enhanced response with appropriate emotion
            if samantha:
                samantha.speak(
                    result["enhanced"], emotion=interaction["emotion"], context=context
                )

            # Rate the response based on combined scores
            combined_score = (
                emotion_score + trait_score + transition_effectiveness
            ) / 3
            self.enhancer.rate_response(
                interaction["message"], combined_score, "Samantha"
            )

            logger.info(f"\nInteraction:")
            logger.info(f"Original: {interaction['message']}")
            logger.info(f"Enhanced: {result['enhanced']}")
            logger.info(f"Emotion Score: {emotion_score:.2f}")
            logger.info(f"Trait Score: {trait_score:.2f}")
            logger.info(f"Emotional Transition Score: {transition_effectiveness:.2f}")
            logger.info(f"User Emotional State: {interaction['user_emotional_state']}")

            previous_emotional_state = interaction["user_emotional_state"]

    def _calculate_emotional_transition_score(
        self, from_state: str, to_state: str, emotion_score: float
    ) -> float:
        """
        Calculate how effective the emotional transition was based on the desired outcome.
        Returns a score between 0.0 and 1.0.
        """
        # Define emotional state progression (from negative to positive)
        emotional_progression = {
            "frustrated": 0,
            "anxious": 1,
            "receptive": 2,
            "calm": 3,
            "satisfied": 4,
        }

        # Get progression values for the states
        from_value = emotional_progression.get(from_state.lower(), 0)
        to_value = emotional_progression.get(to_state.lower(), 0)

        # Calculate base transition score
        if to_value > from_value:
            # Positive transition
            transition_score = 0.7 + (
                0.3 * ((to_value - from_value) / len(emotional_progression))
            )
        else:
            # Negative or neutral transition
            transition_score = 0.5

        # Combine with emotion score for final effectiveness
        return min(1.0, (transition_score * 0.7) + (emotion_score * 0.3))

    def _validate_emotion_adaptation(
        self, enhanced_text: str, expected_emotion: EmotionType, expected_tone: str
    ) -> float:
        """
        Validate how well the enhanced text matches expected emotion and tone.
        Returns a score between 0.0 and 1.0.
        """
        # This is a simplified validation - in production you'd want more sophisticated NLP
        emotion_name = expected_emotion.name.lower()
        score = 0.0

        # Check for emotional markers in text
        emotional_markers = {
            "calm": ["calmly", "steady", "balanced", "composed"],
            "focused": ["specifically", "precisely", "clearly", "exactly"],
            "encouraging": ["great", "excellent", "well done", "you can"],
        }

        markers = emotional_markers.get(emotion_name, [])
        if markers:
            score += sum(
                1 for marker in markers if marker in enhanced_text.lower()
            ) / len(markers)

        # Check tone alignment
        tone_markers = {
            "professional": ["would you like", "I recommend", "shall we"],
            "informative": ["I see", "there are", "you have"],
            "supportive": ["I can help", "let me assist", "we can"],
        }

        tone_score = 0.0
        if expected_tone in tone_markers:
            markers = tone_markers[expected_tone]
            tone_score = sum(
                1 for marker in markers if marker in enhanced_text.lower()
            ) / len(markers)

        # Combine scores with weights
        final_score = (score * 0.6) + (tone_score * 0.4)
        self.emotion_accuracy[expected_emotion] = self.emotion_accuracy.get(
            expected_emotion, []
        ) + [final_score]

        return min(1.0, final_score)

    def _validate_personality_traits(
        self, enhanced_text: str, expected_traits: list
    ) -> float:
        """
        Validate how well the enhanced text exhibits expected personality traits.
        Returns a score between 0.0 and 1.0.
        """
        trait_markers = {
            "confident": ["certainly", "definitely", "I can", "will"],
            "efficient": ["quickly", "efficiently", "optimal", "streamlined"],
            "clear": ["specifically", "clearly", "precisely", "exactly"],
            "helpful": ["help you", "assist", "support", "guide"],
            "proactive": ["suggest", "recommend", "plan", "prepare"],
        }

        total_score = 0.0
        for trait in expected_traits:
            if trait in trait_markers:
                markers = trait_markers[trait]
                trait_score = sum(
                    1 for marker in markers if marker in enhanced_text.lower()
                ) / len(markers)
                total_score += trait_score

                # Track trait effectiveness
                self.trait_effectiveness[trait] = self.trait_effectiveness.get(
                    trait, []
                ) + [trait_score]

        return min(1.0, total_score / len(expected_traits))

    def get_adaptation_report(self) -> Dict[str, Any]:
        """Generate a report on emotion adaptation and trait effectiveness."""
        report = {
            "total_interactions": len(self.interaction_results),
            "emotion_accuracy": {},
            "trait_effectiveness": {},
            "emotional_transitions": {
                "total_transitions": len(self.emotion_transitions),
                "average_effectiveness": 0.0,
                "transitions": self.emotion_transitions,
            },
            "memory_analysis": self._get_memory_analysis(),
            "overall_performance": {},
        }

        # Calculate emotion accuracy averages
        for emotion, scores in self.emotion_accuracy.items():
            report["emotion_accuracy"][emotion.name] = {
                "average_score": sum(scores) / len(scores),
                "total_samples": len(scores),
            }

        # Calculate trait effectiveness averages
        for trait, scores in self.trait_effectiveness.items():
            report["trait_effectiveness"][trait] = {
                "average_score": sum(scores) / len(scores),
                "total_samples": len(scores),
            }

        # Calculate emotional transition effectiveness
        if self.emotion_transitions:
            effectiveness_scores = [
                t["effectiveness"] for t in self.emotion_transitions
            ]
            report["emotional_transitions"]["average_effectiveness"] = sum(
                effectiveness_scores
            ) / len(effectiveness_scores)

        # Calculate overall performance including emotional transitions
        all_emotion_scores = [
            score for scores in self.emotion_accuracy.values() for score in scores
        ]
        all_trait_scores = [
            score for scores in self.trait_effectiveness.values() for score in scores
        ]
        all_transition_scores = [t["effectiveness"] for t in self.emotion_transitions]

        total_scores = all_emotion_scores + all_trait_scores + all_transition_scores
        report["overall_performance"] = {
            "average_emotion_accuracy": sum(all_emotion_scores)
            / len(all_emotion_scores),
            "average_trait_effectiveness": sum(all_trait_scores)
            / len(all_trait_scores),
            "average_transition_effectiveness": sum(all_transition_scores)
            / len(all_transition_scores),
            "combined_score": sum(total_scores) / len(total_scores),
        }

        return report

    def _get_memory_analysis(self) -> Dict[str, Any]:
        """Analyze memory patterns and learning effectiveness."""
        samantha = self.enhancer.persona_manager.get_persona("Samantha")
        if not samantha or not samantha.memory_engine:
            return {}

        emotional_history = samantha.memory_engine.get_emotional_history()
        patterns = samantha.memory_engine.get_interaction_patterns()

        return {
            "emotional_distribution": emotional_history["emotion_distribution"],
            "most_common_emotion": emotional_history["most_common_emotion"],
            "time_of_day_patterns": patterns["time_of_day"],
            "successful_transitions": len(patterns["emotional_transitions"]),
            "learning_effectiveness": len(patterns["successful_responses"])
            / max(1, emotional_history["total_interactions"]),
        }


async def main():
    """Run the enhanced persona demonstration."""
    enhancer = VoiceEnhancer()
    await enhancer.initialize()

    # Set up Samantha as the default persona
    enhancer.persona_manager.set_default("Samantha")

    simulator = ScenarioSimulator(enhancer)

    # Run both scenarios
    await simulator.run_morning_checkin_scenario()
    await simulator.run_error_recovery_scenario()

    # Generate and display the adaptation report
    report = simulator.get_adaptation_report()
    logger.info("\n=== Adaptation Report ===")
    print(json.dumps(report, indent=2))

    # Display memory analysis
    samantha = enhancer.persona_manager.get_persona("Samantha")
    if samantha and samantha.memory_engine:
        logger.info("\n=== Memory Analysis ===")
        patterns = samantha.memory_engine.get_interaction_patterns()
        print(json.dumps(patterns, indent=2))

    # Save the final state
    stats = enhancer.get_persona_stats()
    logger.info("\n=== Final Persona Stats ===")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
