"""
Advanced Email Metrics for SecondBrain application.
Provides enhanced metrics collection and analysis capabilities.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
from textblob import TextBlob
import networkx as nx
from collections import Counter
import re
import threading
import queue

logger = logging.getLogger(__name__)

class AdvancedMetricType:
    """Advanced types of email metrics."""
    ENGAGEMENT = "engagement"
    NETWORK = "network"
    CONTENT = "content"
    BEHAVIOR = "behavior"
    CUSTOM = "custom"

class AdvancedMetricCategory:
    """Advanced categories of email metrics."""
    SENDER = "sender"
    RECIPIENT = "recipient"
    INTERACTION = "interaction"
    PATTERN = "pattern"
    CUSTOM = "custom"

@dataclass
class AdvancedMetricConfig:
    """Configuration for advanced email metrics."""
    name: str
    type: str
    category: str
    description: str
    unit: str
    threshold: float = None
    weight: float = 1.0
    metadata: Dict[str, Any] = None

class AdvancedMetricsAnalyzer:
    """Analyzes advanced email metrics."""
    
    def __init__(self, config_dir: str = "config/email"):
        """Initialize the advanced metrics analyzer.
        
        Args:
            config_dir: Directory to store configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self.metrics_queue = queue.Queue()
        self.analysis_thread = None
        self.is_running = False
    
    def _setup_logging(self):
        """Set up logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load configurations."""
        try:
            config_file = self.config_dir / "advanced_metrics.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = json.load(f)
            else:
                self.configs = {}
                self._save_configs()
        except Exception as e:
            logger.error(f"Failed to load configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save configurations."""
        try:
            config_file = self.config_dir / "advanced_metrics.json"
            with open(config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save configurations: {str(e)}")
    
    def analyze_engagement(self, emails: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze email engagement metrics.
        
        Args:
            emails: List of email data
            
        Returns:
            Dictionary of engagement metrics
        """
        try:
            metrics = {}
            
            # Response rate
            total_emails = len(emails)
            responded_emails = sum(1 for e in emails if e.get("in_reply_to"))
            metrics["response_rate"] = (responded_emails / total_emails) * 100
            
            # Response time distribution
            response_times = []
            for email in emails:
                if email.get("in_reply_to"):
                    response_time = (email["date"] - email["in_reply_to_date"]).total_seconds()
                    response_times.append(response_time)
            
            if response_times:
                metrics["avg_response_time"] = np.mean(response_times)
                metrics["response_time_std"] = np.std(response_times)
            
            # Thread participation
            thread_counts = Counter(e.get("thread_id") for e in emails)
            metrics["avg_thread_length"] = np.mean(list(thread_counts.values()))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze engagement: {str(e)}")
            return {}
    
    def analyze_network(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email network metrics.
        
        Args:
            emails: List of email data
            
        Returns:
            Dictionary of network metrics
        """
        try:
            # Create network graph
            G = nx.DiGraph()
            
            # Add edges (sender -> recipient)
            for email in emails:
                sender = email.get("from")
                recipients = email.get("to", []) + email.get("cc", [])
                for recipient in recipients:
                    G.add_edge(sender, recipient)
            
            metrics = {}
            
            # Centrality measures
            metrics["degree_centrality"] = nx.degree_centrality(G)
            metrics["betweenness_centrality"] = nx.betweenness_centrality(G)
            metrics["eigenvector_centrality"] = nx.eigenvector_centrality(G)
            
            # Network statistics
            metrics["density"] = nx.density(G)
            metrics["average_clustering"] = nx.average_clustering(G)
            metrics["average_shortest_path"] = nx.average_shortest_path_length(G)
            
            # Community detection
            communities = nx.community.greedy_modularity_communities(G.to_undirected())
            metrics["community_count"] = len(communities)
            metrics["community_sizes"] = [len(c) for c in communities]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze network: {str(e)}")
            return {}
    
    def analyze_content(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email content metrics.
        
        Args:
            emails: List of email data
            
        Returns:
            Dictionary of content metrics
        """
        try:
            metrics = {}
            
            # Sentiment analysis
            sentiments = []
            for email in emails:
                text = email.get("body", "")
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)
            
            metrics["avg_sentiment"] = np.mean(sentiments)
            metrics["sentiment_std"] = np.std(sentiments)
            
            # Content length
            lengths = [len(e.get("body", "")) for e in emails]
            metrics["avg_length"] = np.mean(lengths)
            metrics["length_std"] = np.std(lengths)
            
            # Keyword analysis
            keywords = Counter()
            for email in emails:
                text = email.get("body", "").lower()
                words = re.findall(r'\w+', text)
                keywords.update(words)
            
            metrics["top_keywords"] = dict(keywords.most_common(10))
            
            # Language detection
            languages = Counter()
            for email in emails:
                text = email.get("body", "")
                blob = TextBlob(text)
                languages[blob.detect_language()] += 1
            
            metrics["language_distribution"] = dict(languages)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze content: {str(e)}")
            return {}
    
    def analyze_behavior(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email behavior metrics.
        
        Args:
            emails: List of email data
            
        Returns:
            Dictionary of behavior metrics
        """
        try:
            metrics = {}
            
            # Time-based patterns
            hours = [e["date"].hour for e in emails]
            metrics["peak_hours"] = Counter(hours).most_common(3)
            
            # Response patterns
            response_times = []
            for email in emails:
                if email.get("in_reply_to"):
                    response_time = (email["date"] - email["in_reply_to_date"]).total_seconds()
                    response_times.append(response_time)
            
            if response_times:
                metrics["response_time_distribution"] = {
                    "mean": np.mean(response_times),
                    "median": np.median(response_times),
                    "std": np.std(response_times)
                }
            
            # Thread behavior
            thread_lengths = Counter(e.get("thread_id") for e in emails).values()
            metrics["thread_behavior"] = {
                "avg_length": np.mean(list(thread_lengths)),
                "max_length": max(thread_lengths),
                "min_length": min(thread_lengths)
            }
            
            # Recipient patterns
            recipient_counts = Counter()
            for email in emails:
                recipients = email.get("to", []) + email.get("cc", [])
                recipient_counts[len(recipients)] += 1
            
            metrics["recipient_patterns"] = dict(recipient_counts)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze behavior: {str(e)}")
            return {}
    
    def detect_anomalies(self, metrics: Dict[str, Any], 
                        config: AdvancedMetricConfig) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics.
        
        Args:
            metrics: Dictionary of metrics
            config: Metric configuration
            
        Returns:
            List of detected anomalies
        """
        try:
            anomalies = []
            
            # Z-score based detection
            for metric_name, values in metrics.items():
                if isinstance(values, (list, np.ndarray)):
                    z_scores = np.abs(stats.zscore(values))
                    anomaly_indices = np.where(z_scores > 3)[0]
                    
                    for idx in anomaly_indices:
                        anomalies.append({
                            "metric": metric_name,
                            "value": values[idx],
                            "z_score": z_scores[idx],
                            "timestamp": datetime.now()
                        })
            
            # Threshold based detection
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    if config.threshold and value > config.threshold:
                        anomalies.append({
                            "metric": metric_name,
                            "value": value,
                            "threshold": config.threshold,
                            "timestamp": datetime.now()
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {str(e)}")
            return []
    
    def generate_recommendations(self, metrics: Dict[str, Any], 
                               anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on metrics and anomalies.
        
        Args:
            metrics: Dictionary of metrics
            anomalies: List of anomalies
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            
            # Engagement recommendations
            if "response_rate" in metrics:
                if metrics["response_rate"] < 50:
                    recommendations.append(
                        "Low response rate detected. Consider following up on important emails."
                    )
            
            # Network recommendations
            if "density" in metrics:
                if metrics["density"] < 0.1:
                    recommendations.append(
                        "Low network density detected. Consider expanding communication network."
                    )
            
            # Content recommendations
            if "avg_sentiment" in metrics:
                if metrics["avg_sentiment"] < -0.2:
                    recommendations.append(
                        "Negative sentiment trend detected. Review communication tone."
                    )
            
            # Behavior recommendations
            if "response_time_distribution" in metrics:
                avg_response = metrics["response_time_distribution"]["mean"]
                if avg_response > 86400:  # More than 24 hours
                    recommendations.append(
                        "High average response time detected. Consider improving response time."
                    )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return []

# Example usage
if __name__ == "__main__":
    analyzer = AdvancedMetricsAnalyzer()
    
    # Sample email data
    emails = [
        {
            "from": "user1@example.com",
            "to": ["user2@example.com"],
            "cc": ["user3@example.com"],
            "subject": "Test email",
            "body": "This is a test email.",
            "date": datetime.now(),
            "thread_id": "thread1"
        }
    ]
    
    # Analyze metrics
    engagement_metrics = analyzer.analyze_engagement(emails)
    network_metrics = analyzer.analyze_network(emails)
    content_metrics = analyzer.analyze_content(emails)
    behavior_metrics = analyzer.analyze_behavior(emails)
    
    # Detect anomalies
    config = AdvancedMetricConfig(
        name="engagement_metrics",
        type=AdvancedMetricType.ENGAGEMENT,
        category=AdvancedMetricCategory.INTERACTION,
        description="Email engagement metrics",
        unit="percentage",
        threshold=80.0
    )
    
    anomalies = analyzer.detect_anomalies(engagement_metrics, config)
    recommendations = analyzer.generate_recommendations(
        engagement_metrics, anomalies
    ) 