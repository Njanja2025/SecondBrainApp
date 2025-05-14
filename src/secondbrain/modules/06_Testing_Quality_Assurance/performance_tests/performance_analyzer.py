"""
Performance analyzer for handling performance tests.
Manages benchmarks, metrics collection, and performance analysis.
"""

import os
import json
import logging
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfig:
    """Configuration for performance tests."""

    name: str
    benchmarks: List[Dict[str, Any]]
    duration: int = 60
    interval: float = 1.0
    metrics: List[str] = None
    threshold: Dict[str, float] = None


class PerformanceAnalyzer:
    """Manages performance test execution and analysis."""

    def __init__(self, config_dir: str = "config/performance_tests"):
        """Initialize the performance analyzer.

        Args:
            config_dir: Directory to store performance test configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self._init_metrics()

    def _setup_logging(self):
        """Set up logging for the performance analyzer."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _load_configs(self):
        """Load performance test configurations."""
        try:
            config_file = self.config_dir / "performance_configs.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    self.configs = {
                        name: PerformanceConfig(**config)
                        for name, config in json.load(f).items()
                    }
            else:
                self.configs = {}
                self._save_configs()

            logger.info("Performance test configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load performance test configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save performance test configurations."""
        try:
            config_file = self.config_dir / "performance_configs.json"

            with open(config_file, "w") as f:
                json.dump(
                    {name: vars(config) for name, config in self.configs.items()},
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save performance test configurations: {str(e)}")

    def _init_metrics(self):
        """Initialize metrics collection."""
        self.metrics_data = {}
        self.metrics_thread = None
        self.stop_metrics = False

    def create_config(self, config: PerformanceConfig) -> bool:
        """Create a new performance test configuration.

        Args:
            config: Performance test configuration

        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False

            self.configs[config.name] = config
            self._save_configs()

            logger.info(f"Created performance test configuration {config.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create performance test configuration {config.name}: {str(e)}"
            )
            return False

    def update_config(self, name: str, config: PerformanceConfig) -> bool:
        """Update an existing performance test configuration.

        Args:
            name: Configuration name
            config: New performance test configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            self.configs[name] = config
            self._save_configs()

            logger.info(f"Updated performance test configuration {name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to update performance test configuration {name}: {str(e)}"
            )
            return False

    def delete_config(self, name: str) -> bool:
        """Delete a performance test configuration.

        Args:
            name: Configuration name

        Returns:
            bool: True if configuration was deleted successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            del self.configs[name]
            self._save_configs()

            logger.info(f"Deleted performance test configuration {name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to delete performance test configuration {name}: {str(e)}"
            )
            return False

    def get_config(self, name: str) -> Optional[PerformanceConfig]:
        """Get performance test configuration.

        Args:
            name: Configuration name

        Returns:
            Performance test configuration if found
        """
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all performance test configurations.

        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

    def run_tests(self, config_name: str) -> Dict[str, Any]:
        """Run performance tests.

        Args:
            config_name: Configuration name

        Returns:
            Test results
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return {"success": False, "error": "Configuration not found"}

            results = {
                "timestamp": datetime.now().isoformat(),
                "config": config_name,
                "benchmarks": [],
                "metrics": {},
                "summary": {"total": 0, "passed": 0, "failed": 0},
            }

            # Start metrics collection
            self._start_metrics_collection(config)

            # Run benchmarks
            for benchmark in config.benchmarks:
                benchmark_result = self._run_benchmark(benchmark, config)
                results["benchmarks"].append(benchmark_result)

                if benchmark_result["status"] == "passed":
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1

                results["summary"]["total"] += 1

            # Stop metrics collection
            self._stop_metrics_collection()

            # Add metrics data
            results["metrics"] = self.metrics_data

            logger.info(f"Ran performance tests for configuration {config_name}")
            return results

        except Exception as e:
            logger.error(
                f"Failed to run performance tests for configuration {config_name}: {str(e)}"
            )
            return {"success": False, "error": str(e)}

    def _start_metrics_collection(self, config: PerformanceConfig):
        """Start collecting performance metrics.

        Args:
            config: Performance test configuration
        """
        try:
            self.stop_metrics = False
            self.metrics_data = {metric: [] for metric in config.metrics}

            def collect_metrics():
                while not self.stop_metrics:
                    for metric in config.metrics:
                        value = self._get_metric_value(metric)
                        self.metrics_data[metric].append(
                            {"timestamp": datetime.now().isoformat(), "value": value}
                        )
                    time.sleep(config.interval)

            self.metrics_thread = threading.Thread(target=collect_metrics)
            self.metrics_thread.start()

        except Exception as e:
            logger.error(f"Failed to start metrics collection: {str(e)}")
            raise

    def _stop_metrics_collection(self):
        """Stop collecting performance metrics."""
        try:
            self.stop_metrics = True
            if self.metrics_thread:
                self.metrics_thread.join()

        except Exception as e:
            logger.error(f"Failed to stop metrics collection: {str(e)}")
            raise

    def _get_metric_value(self, metric: str) -> float:
        """Get the current value of a metric.

        Args:
            metric: Metric name

        Returns:
            Metric value
        """
        try:
            if metric == "cpu_percent":
                return psutil.cpu_percent()
            elif metric == "memory_percent":
                return psutil.virtual_memory().percent
            elif metric == "disk_io":
                return (
                    psutil.disk_io_counters().read_bytes
                    + psutil.disk_io_counters().write_bytes
                )
            elif metric == "network_io":
                return (
                    psutil.net_io_counters().bytes_sent
                    + psutil.net_io_counters().bytes_recv
                )
            else:
                logger.error(f"Unsupported metric: {metric}")
                return 0.0

        except Exception as e:
            logger.error(f"Failed to get metric value for {metric}: {str(e)}")
            return 0.0

    def _run_benchmark(
        self, benchmark: Dict[str, Any], config: PerformanceConfig
    ) -> Dict[str, Any]:
        """Run a performance benchmark.

        Args:
            benchmark: Benchmark configuration
            config: Performance test configuration

        Returns:
            Benchmark results
        """
        try:
            result = {
                "name": benchmark["name"],
                "status": "failed",
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "metrics": {},
                "error": None,
            }

            # Run benchmark
            if "test" in benchmark:
                try:
                    start_time = time.time()
                    benchmark["test"]()
                    end_time = time.time()

                    # Calculate metrics
                    for metric in config.metrics:
                        values = [m["value"] for m in self.metrics_data[metric]]
                        if values:
                            result["metrics"][metric] = {
                                "min": min(values),
                                "max": max(values),
                                "avg": sum(values) / len(values),
                            }

                    # Check thresholds
                    if config.threshold:
                        for metric, threshold in config.threshold.items():
                            if metric in result["metrics"]:
                                if result["metrics"][metric]["avg"] > threshold:
                                    result["status"] = "failed"
                                    result["error"] = (
                                        f"Metric {metric} exceeded threshold"
                                    )
                                    break

                    if not result["error"]:
                        result["status"] = "passed"

                except Exception as e:
                    result["status"] = "failed"
                    result["error"] = str(e)

            result["end_time"] = datetime.now().isoformat()
            return result

        except Exception as e:
            logger.error(f"Failed to run benchmark {benchmark['name']}: {str(e)}")
            return {"name": benchmark["name"], "status": "failed", "error": str(e)}

    def add_benchmark(self, config_name: str, benchmark: Dict[str, Any]) -> bool:
        """Add a benchmark to a configuration.

        Args:
            config_name: Configuration name
            benchmark: Benchmark configuration

        Returns:
            bool: True if benchmark was added successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False

            config.benchmarks.append(benchmark)
            self._save_configs()

            logger.info(f"Added benchmark to configuration {config_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to add benchmark to configuration {config_name}: {str(e)}"
            )
            return False

    def remove_benchmark(self, config_name: str, benchmark_name: str) -> bool:
        """Remove a benchmark from a configuration.

        Args:
            config_name: Configuration name
            benchmark_name: Benchmark name

        Returns:
            bool: True if benchmark was removed successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False

            config.benchmarks = [
                b for b in config.benchmarks if b.get("name") != benchmark_name
            ]
            self._save_configs()

            logger.info(f"Removed benchmark from configuration {config_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to remove benchmark from configuration {config_name}: {str(e)}"
            )
            return False


# Example usage
if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()

    # Create performance test configuration
    config = PerformanceConfig(
        name="basic_performance",
        benchmarks=[
            {
                "name": "test_cpu_intensive",
                "test": lambda: [i * i for i in range(1000000)],
            }
        ],
        metrics=["cpu_percent", "memory_percent"],
        threshold={"cpu_percent": 80.0, "memory_percent": 70.0},
    )
    analyzer.create_config(config)

    # Run tests
    results = analyzer.run_tests("basic_performance")
    print("Test results:", results)
