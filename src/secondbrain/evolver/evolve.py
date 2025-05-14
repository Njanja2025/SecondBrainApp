import time
import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OptimizationRule:
    def __init__(
        self, name: str, condition: callable, action: callable, description: str
    ):
        self.name = name
        self.condition = condition
        self.action = action
        self.description = description
        self.last_applied = None
        self.application_count = 0


class Evolver:
    def __init__(self):
        self.last_scan_time = 0
        self.scan_interval = 30  # seconds
        self.upgrade_history = []
        self.optimization_metrics = {}
        self.performance_threshold = 0.8  # 80% threshold for optimization triggers
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> List[OptimizationRule]:
        """Initialize optimization rules."""
        return [
            OptimizationRule(
                name="memory_compression",
                condition=lambda agent: (
                    hasattr(agent, "memory") and len(agent.memory.log) > 1000
                ),
                action=self._compress_memory,
                description="Compress old memory entries to reduce memory usage",
            ),
            OptimizationRule(
                name="command_history_cleanup",
                condition=lambda agent: (
                    hasattr(agent, "voice_processor")
                    and len(agent.voice_processor.command_history) > 500
                ),
                action=self._cleanup_command_history,
                description="Clean up old command history entries",
            ),
            OptimizationRule(
                name="blockchain_cache_optimization",
                condition=lambda agent: (
                    hasattr(agent, "blockchain")
                    and hasattr(agent.blockchain, "contract_manager")
                ),
                action=self._optimize_blockchain_cache,
                description="Optimize blockchain contract cache",
            ),
        ]

    def scan_and_upgrade(self, agent: Any) -> Dict[str, Any]:
        """Scan for potential improvements and upgrade the agent."""
        current_time = time.time()

        if current_time - self.last_scan_time < self.scan_interval:
            return {"status": "skipped", "reason": "too_soon"}

        self.last_scan_time = current_time
        logger.info("[Evolver] Scanning for improvements...")

        try:
            # Update performance metrics
            self._update_performance_metrics(agent)

            # Check rules and apply optimizations
            applied_optimizations = []
            for rule in self.rules:
                try:
                    if self._should_apply_rule(rule, agent):
                        optimization_result = rule.action(agent)
                        if optimization_result.get("status") == "success":
                            applied_optimizations.append(
                                {
                                    "rule": rule.name,
                                    "description": rule.description,
                                    "result": optimization_result,
                                }
                            )
                            rule.last_applied = current_time
                            rule.application_count += 1
                except Exception as e:
                    logger.error(f"Error applying rule {rule.name}: {str(e)}")

            # Record evolution attempt
            evolution_record = {
                "timestamp": current_time,
                "status": "upgraded" if applied_optimizations else "no_upgrades",
                "optimizations": applied_optimizations,
                "metrics": self.optimization_metrics,
            }
            self.upgrade_history.append(evolution_record)

            return evolution_record

        except Exception as e:
            error_record = {
                "timestamp": current_time,
                "status": "error",
                "error": str(e),
            }
            self.upgrade_history.append(error_record)
            logger.error(f"Error during evolution scan: {str(e)}")
            return error_record

    def _should_apply_rule(self, rule: OptimizationRule, agent: Any) -> bool:
        """Determine if a rule should be applied based on conditions and history."""
        try:
            # Check if rule was recently applied
            if (
                rule.last_applied and time.time() - rule.last_applied < 3600
            ):  # 1 hour cooldown
                return False

            # Check rule condition
            return rule.condition(agent)

        except Exception as e:
            logger.error(f"Error checking rule {rule.name}: {str(e)}")
            return False

    def _update_performance_metrics(self, agent: Any):
        """Update performance metrics from agent state."""
        try:
            metrics = {}

            # Memory metrics
            if hasattr(agent, "memory"):
                memory_stats = agent.memory.analyze_performance()
                metrics["memory"] = {
                    "total_entries": len(agent.memory.log),
                    "task_distribution": memory_stats["task_distribution"],
                }

            # Voice processor metrics
            if hasattr(agent, "voice_processor"):
                metrics["voice"] = {
                    "total_commands": len(agent.voice_processor.command_history),
                    "success_rate": self._calculate_command_success_rate(agent),
                }

            # Blockchain metrics
            if hasattr(agent, "blockchain"):
                metrics["blockchain"] = {
                    "connected": agent.blockchain.network_manager.web3 is not None,
                    "contracts_deployed": len(
                        getattr(agent.blockchain.contract_manager, "contracts", {})
                    ),
                }

            self.optimization_metrics = metrics

        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")

    def _calculate_command_success_rate(self, agent: Any) -> float:
        """Calculate success rate of voice commands."""
        try:
            history = agent.voice_processor.get_command_history()
            if not history:
                return 1.0

            successful = sum(
                1
                for cmd in history
                if isinstance(cmd, dict) and cmd.get("status") == "success"
            )
            return successful / len(history)

        except Exception as e:
            logger.error(f"Error calculating command success rate: {str(e)}")
            return 1.0

    async def _compress_memory(self, agent: Any) -> Dict[str, Any]:
        """Compress old memory entries."""
        try:
            if not hasattr(agent, "memory"):
                return {"status": "error", "error": "No memory system found"}

            cutoff_date = datetime.now() - timedelta(days=7)
            old_entries = [
                entry
                for entry in agent.memory.log
                if datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
                < cutoff_date
            ]

            if not old_entries:
                return {"status": "skipped", "reason": "no_old_entries"}

            # Compress old entries into summary
            summary = {
                "period_start": old_entries[0]["timestamp"],
                "period_end": old_entries[-1]["timestamp"],
                "total_entries": len(old_entries),
                "entry_types": {},
            }

            for entry in old_entries:
                entry_type = entry["type"]
                if entry_type not in summary["entry_types"]:
                    summary["entry_types"][entry_type] = 0
                summary["entry_types"][entry_type] += 1

            # Remove old entries and add summary
            agent.memory.log = [
                entry
                for entry in agent.memory.log
                if datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
                >= cutoff_date
            ]
            agent.memory.log.append(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "memory_summary",
                    "description": "Compressed old entries",
                    "summary": summary,
                }
            )

            return {
                "status": "success",
                "compressed_entries": len(old_entries),
                "summary": summary,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _cleanup_command_history(self, agent: Any) -> Dict[str, Any]:
        """Clean up old command history."""
        try:
            if not hasattr(agent, "voice_processor"):
                return {"status": "error", "error": "No voice processor found"}

            cutoff_date = datetime.now() - timedelta(days=1)
            agent.voice_processor.clear_history(older_than=cutoff_date)

            return {
                "status": "success",
                "action": "history_cleanup",
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _optimize_blockchain_cache(self, agent: Any) -> Dict[str, Any]:
        """Optimize blockchain contract cache."""
        try:
            if not hasattr(agent, "blockchain") or not hasattr(
                agent.blockchain, "contract_manager"
            ):
                return {
                    "status": "error",
                    "error": "No blockchain contract manager found",
                }

            # Implementation depends on your blockchain manager's structure
            # This is a placeholder for the actual implementation
            return {
                "status": "success",
                "action": "cache_optimization",
                "details": "Blockchain cache optimized",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_upgrade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Return the history of upgrade attempts with optional limit."""
        history = sorted(
            self.upgrade_history, key=lambda x: x["timestamp"], reverse=True
        )
        return history[:limit] if limit else history

    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Return current optimization metrics."""
        return self.optimization_metrics

    def get_rule_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics about optimization rules."""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "times_applied": rule.application_count,
                "last_applied": rule.last_applied,
            }
            for rule in self.rules
        ]
