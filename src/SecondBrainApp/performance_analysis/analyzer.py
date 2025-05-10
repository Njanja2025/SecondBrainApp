"""
Performance Analyzer for SecondBrain application.
Manages performance metrics collection, analysis, and reporting.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from scipy import stats
import psutil
import time
import threading
import queue

logger = logging.getLogger(__name__)

@dataclass
class MetricConfig:
    """Configuration for performance metrics."""
    name: str
    type: str  # cpu, memory, disk, network, custom
    category: str  # system, application, database, api
    description: str
    unit: str  # %, MB, ms, etc.
    threshold: float = None
    weight: float = 1.0
    metadata: Dict[str, Any] = None

@dataclass
class ReportConfig:
    """Configuration for performance reports."""
    name: str
    format: str  # json, markdown, html, pdf
    template: str = None
    metrics: List[str] = None
    interval: int = 3600  # seconds
    retention: int = 7  # days
    metadata: Dict[str, Any] = None

@dataclass
class PerformanceConfig:
    """Configuration for performance analysis."""
    name: str
    metrics: List[MetricConfig]
    reports: List[ReportConfig]
    sampling_interval: int = 60  # seconds
    analysis_window: int = 3600  # seconds
    alert_threshold: float = 0.8  # 80%
    metadata: Dict[str, Any] = None

@dataclass
class AnalysisResult:
    """Result of performance analysis."""
    timestamp: datetime
    metrics: Dict[str, float]
    statistics: Dict[str, float]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]
    score: float

class PerformanceAnalyzer:
    """Manages performance analysis and reporting."""
    
    def __init__(self, config_dir: str = "config/performance"):
        """Initialize the performance analyzer.
        
        Args:
            config_dir: Directory to store performance configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self.metrics_queue = queue.Queue()
        self.analysis_thread = None
        self.is_running = False
    
    def _setup_logging(self):
        """Set up logging for the performance analyzer."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load performance configurations."""
        try:
            config_file = self.config_dir / "performance_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    self.configs = {
                        name: PerformanceConfig(
                            name=name,
                            metrics=[MetricConfig(**m) for m in config["metrics"]],
                            reports=[ReportConfig(**r) for r in config["reports"]],
                            **{k: v for k, v in config.items() 
                               if k not in ["name", "metrics", "reports"]}
                        )
                        for name, config in config_data.items()
                    }
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Performance configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load performance configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save performance configurations."""
        try:
            config_file = self.config_dir / "performance_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({
                    name: {
                        "name": config.name,
                        "metrics": [vars(m) for m in config.metrics],
                        "reports": [vars(r) for r in config.reports],
                        "sampling_interval": config.sampling_interval,
                        "analysis_window": config.analysis_window,
                        "alert_threshold": config.alert_threshold,
                        "metadata": config.metadata
                    }
                    for name, config in self.configs.items()
                }, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save performance configurations: {str(e)}")
    
    def create_config(self, config: PerformanceConfig) -> bool:
        """Create a new performance configuration.
        
        Args:
            config: Performance configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created performance configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create performance configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: PerformanceConfig) -> bool:
        """Update an existing performance configuration.
        
        Args:
            name: Configuration name
            config: New performance configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated performance configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update performance configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete a performance configuration.
        
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
            
            logger.info(f"Deleted performance configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete performance configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[PerformanceConfig]:
        """Get performance configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Performance configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all performance configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def collect_metrics(self, config_name: str) -> Dict[str, float]:
        """Collect performance metrics.
        
        Args:
            config_name: Configuration name
            
        Returns:
            Dictionary of metric values
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return {}
            
            metrics = {}
            
            for metric in config.metrics:
                if metric.type == "cpu":
                    metrics[metric.name] = psutil.cpu_percent()
                elif metric.type == "memory":
                    metrics[metric.name] = psutil.virtual_memory().percent
                elif metric.type == "disk":
                    metrics[metric.name] = psutil.disk_usage('/').percent
                elif metric.type == "network":
                    net_io = psutil.net_io_counters()
                    metrics[metric.name] = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # MB
                elif metric.type == "custom":
                    # Implement custom metric collection
                    pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics for {config_name}: {str(e)}")
            return {}
    
    def analyze_metrics(self, metrics_data: List[Dict[str, float]], 
                       config: PerformanceConfig) -> AnalysisResult:
        """Analyze performance metrics.
        
        Args:
            metrics_data: List of metric values over time
            config: Performance configuration
            
        Returns:
            Analysis result
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(metrics_data)
            
            # Calculate statistics
            statistics = {}
            for metric in config.metrics:
                if metric.name in df.columns:
                    statistics[f"{metric.name}_mean"] = df[metric.name].mean()
                    statistics[f"{metric.name}_std"] = df[metric.name].std()
                    statistics[f"{metric.name}_max"] = df[metric.name].max()
                    statistics[f"{metric.name}_min"] = df[metric.name].min()
            
            # Detect anomalies
            anomalies = []
            for metric in config.metrics:
                if metric.name in df.columns:
                    # Use z-score for anomaly detection
                    z_scores = np.abs(stats.zscore(df[metric.name]))
                    anomaly_indices = np.where(z_scores > 3)[0]
                    
                    for idx in anomaly_indices:
                        anomalies.append({
                            "metric": metric.name,
                            "timestamp": df.index[idx],
                            "value": df[metric.name].iloc[idx],
                            "z_score": z_scores[idx]
                        })
            
            # Generate recommendations
            recommendations = []
            for metric in config.metrics:
                if metric.name in df.columns:
                    if df[metric.name].mean() > config.alert_threshold * 100:
                        recommendations.append(
                            f"High {metric.name} usage detected. Consider optimization."
                        )
            
            # Calculate overall score
            score = 100
            for metric in config.metrics:
                if metric.name in df.columns:
                    score -= (df[metric.name].mean() / 100) * metric.weight * 20
            
            return AnalysisResult(
                timestamp=datetime.now(),
                metrics=df.iloc[-1].to_dict(),
                statistics=statistics,
                anomalies=anomalies,
                recommendations=recommendations,
                score=max(0, score)
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze metrics: {str(e)}")
            return None
    
    def start_monitoring(self, config_name: str):
        """Start performance monitoring.
        
        Args:
            config_name: Configuration name
        """
        try:
            if self.is_running:
                logger.error("Monitoring already running")
                return
            
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return
            
            self.is_running = True
            self.analysis_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(config_name,)
            )
            self.analysis_thread.start()
            
            logger.info(f"Started monitoring for {config_name}")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        try:
            if not self.is_running:
                logger.error("Monitoring not running")
                return
            
            self.is_running = False
            if self.analysis_thread:
                self.analysis_thread.join()
            
            logger.info("Stopped monitoring")
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {str(e)}")
    
    def _monitoring_loop(self, config_name: str):
        """Monitoring loop for collecting and analyzing metrics.
        
        Args:
            config_name: Configuration name
        """
        try:
            config = self.get_config(config_name)
            metrics_data = []
            
            while self.is_running:
                # Collect metrics
                metrics = self.collect_metrics(config_name)
                metrics_data.append(metrics)
                
                # Keep only recent data
                if len(metrics_data) > config.analysis_window / config.sampling_interval:
                    metrics_data.pop(0)
                
                # Analyze if enough data
                if len(metrics_data) >= 10:  # Minimum samples for analysis
                    result = self.analyze_metrics(metrics_data, config)
                    if result:
                        self.metrics_queue.put(result)
                
                time.sleep(config.sampling_interval)
            
        except Exception as e:
            logger.error(f"Monitoring loop failed: {str(e)}")
            self.is_running = False

# Example usage
if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    
    # Create performance configuration
    config = PerformanceConfig(
        name="system_metrics",
        metrics=[
            MetricConfig(
                name="cpu_usage",
                type="cpu",
                category="system",
                description="CPU usage percentage",
                unit="%",
                threshold=80.0
            ),
            MetricConfig(
                name="memory_usage",
                type="memory",
                category="system",
                description="Memory usage percentage",
                unit="%",
                threshold=80.0
            )
        ],
        reports=[
            ReportConfig(
                name="system_report",
                format="markdown",
                metrics=["cpu_usage", "memory_usage"],
                interval=3600
            )
        ],
        sampling_interval=60,
        analysis_window=3600
    )
    analyzer.create_config(config)
    
    # Start monitoring
    analyzer.start_monitoring("system_metrics")
    
    # Wait for some results
    time.sleep(300)
    
    # Stop monitoring
    analyzer.stop_monitoring() 