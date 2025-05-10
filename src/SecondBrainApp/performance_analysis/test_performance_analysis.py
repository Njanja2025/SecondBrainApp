"""
Test cases for Performance Analysis module.
Tests metric collection, analysis, and reporting.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
import numpy as np

from .analyzer import (
    PerformanceAnalyzer,
    PerformanceConfig,
    MetricConfig,
    ReportConfig,
    AnalysisResult
)

@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary configuration directory."""
    return tmp_path / "config"

@pytest.fixture
def metric_config():
    """Create a sample metric configuration."""
    return MetricConfig(
        name="test_metric",
        type="custom",
        category="test",
        description="Test metric",
        unit="%",
        threshold=80.0
    )

@pytest.fixture
def report_config():
    """Create a sample report configuration."""
    return ReportConfig(
        name="test_report",
        format="markdown",
        metrics=["test_metric"],
        interval=3600
    )

@pytest.fixture
def performance_config(metric_config, report_config):
    """Create a sample performance configuration."""
    return PerformanceConfig(
        name="test_config",
        metrics=[metric_config],
        reports=[report_config],
        sampling_interval=60,
        analysis_window=3600
    )

@pytest.fixture
def analyzer(config_dir):
    """Create a performance analyzer instance."""
    return PerformanceAnalyzer(config_dir=str(config_dir))

class TestPerformanceAnalyzer:
    """Test cases for performance analyzer."""
    
    def test_init(self, analyzer, config_dir):
        """Test analyzer initialization."""
        assert analyzer.config_dir.exists()
        assert analyzer.configs == {}
    
    def test_create_config(self, analyzer, performance_config):
        """Test configuration creation."""
        assert analyzer.create_config(performance_config)
        assert "test_config" in analyzer.configs
        assert analyzer.configs["test_config"] == performance_config
    
    def test_update_config(self, analyzer, performance_config):
        """Test configuration update."""
        analyzer.create_config(performance_config)
        
        updated_config = PerformanceConfig(
            name="test_config",
            metrics=performance_config.metrics,
            reports=performance_config.reports,
            sampling_interval=30,
            analysis_window=1800
        )
        
        assert analyzer.update_config("test_config", updated_config)
        assert analyzer.configs["test_config"] == updated_config
    
    def test_delete_config(self, analyzer, performance_config):
        """Test configuration deletion."""
        analyzer.create_config(performance_config)
        assert analyzer.delete_config("test_config")
        assert "test_config" not in analyzer.configs
    
    def test_get_config(self, analyzer, performance_config):
        """Test configuration retrieval."""
        analyzer.create_config(performance_config)
        assert analyzer.get_config("test_config") == performance_config
        assert analyzer.get_config("nonexistent") is None
    
    def test_list_configs(self, analyzer, performance_config):
        """Test configuration listing."""
        analyzer.create_config(performance_config)
        assert "test_config" in analyzer.list_configs()
    
    @patch("psutil.cpu_percent")
    def test_collect_metrics_cpu(self, mock_cpu_percent, analyzer, performance_config):
        """Test CPU metric collection."""
        analyzer.create_config(performance_config)
        mock_cpu_percent.return_value = 50.0
        
        metrics = analyzer.collect_metrics("test_config")
        assert "test_metric" in metrics
        assert metrics["test_metric"] == 50.0
    
    @patch("psutil.virtual_memory")
    def test_collect_metrics_memory(self, mock_memory, analyzer, performance_config):
        """Test memory metric collection."""
        analyzer.create_config(performance_config)
        mock_memory.return_value = MagicMock(percent=75.0)
        
        metrics = analyzer.collect_metrics("test_config")
        assert "test_metric" in metrics
        assert metrics["test_metric"] == 75.0
    
    def test_analyze_metrics(self, analyzer, performance_config):
        """Test metric analysis."""
        analyzer.create_config(performance_config)
        
        # Create sample metrics data
        metrics_data = [
            {"test_metric": 50.0},
            {"test_metric": 60.0},
            {"test_metric": 70.0},
            {"test_metric": 80.0},
            {"test_metric": 90.0}  # Anomaly
        ]
        
        result = analyzer.analyze_metrics(metrics_data, performance_config)
        
        assert isinstance(result, AnalysisResult)
        assert "test_metric" in result.metrics
        assert "test_metric_mean" in result.statistics
        assert len(result.anomalies) > 0
        assert len(result.recommendations) > 0
        assert 0 <= result.score <= 100
    
    def test_start_monitoring(self, analyzer, performance_config):
        """Test monitoring start."""
        analyzer.create_config(performance_config)
        analyzer.start_monitoring("test_config")
        
        assert analyzer.is_running
        assert analyzer.analysis_thread is not None
        assert analyzer.analysis_thread.is_alive()
        
        analyzer.stop_monitoring()
    
    def test_stop_monitoring(self, analyzer, performance_config):
        """Test monitoring stop."""
        analyzer.create_config(performance_config)
        analyzer.start_monitoring("test_config")
        analyzer.stop_monitoring()
        
        assert not analyzer.is_running
        assert not analyzer.analysis_thread.is_alive()

if __name__ == "__main__":
    pytest.main([__file__]) 