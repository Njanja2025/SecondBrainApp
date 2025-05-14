"""
Email analytics utility for tracking and analyzing email notifications.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.linear_model import (
    LinearRegression,
    Ridge,
    Lasso,
    ElasticNet,
    HuberRegressor,
    RANSACRegressor,
)
from sklearn.preprocessing import StandardScaler, RobustScaler, PolynomialFeatures
from sklearn.ensemble import (
    IsolationForest,
    RandomForestRegressor,
    GradientBoostingRegressor,
    VotingRegressor,
    StackingRegressor,
)
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    TimeSeriesSplit,
    cross_val_score,
)
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    explained_variance_score,
    max_error,
)
from sklearn.decomposition import PCA, FastICA
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import (
    LSTM,
    Dense,
    Dropout,
    Bidirectional,
    Conv1D,
    MaxPooling1D,
    Flatten,
    GRU,
    Attention,
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psutil
import threading
import time
from prophet import Prophet
import networkx as nx
from scipy import stats
from scipy.signal import detrend
import warnings

warnings.filterwarnings("ignore")
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/email_analytics.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class EmailAnalytics:
    """Handles email analytics and reporting."""

    def __init__(self):
        """Initialize email analytics."""
        self.db_path = "data/email_queue.db"
        self.reports_dir = Path("reports/email_analytics")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._start_monitoring()
        self.models = {}
        self._init_models()
        self.monitoring_thread = None
        self.alert_thresholds = {
            "cpu_usage": 80,
            "memory_usage": 80,
            "disk_usage": 80,
            "error_rate": 5,
            "response_time": 1000,  # ms
            "queue_size": 1000,
            "processing_time": 5000,  # ms
            "consecutive_failures": 3,
        }
        self.performance_metrics = {
            "queue_size": 0,
            "processing_time": 0,
            "consecutive_failures": 0,
            "last_success_time": None,
        }

    def _init_db(self):
        """Initialize the database with additional tables for analytics."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Create analytics tables
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS email_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value REAL,
                    timestamp TIMESTAMP,
                    period TEXT
                )
            """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS email_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    event_data TEXT,
                    timestamp TIMESTAMP
                )
            """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_io REAL,
                    error_rate REAL,
                    response_time REAL,
                    queue_size INTEGER,
                    processing_time REAL,
                    consecutive_failures INTEGER,
                    timestamp TIMESTAMP
                )
            """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    predicted_value REAL,
                    confidence REAL,
                    model_name TEXT,
                    timestamp TIMESTAMP
                )
            """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric TEXT,
                    value REAL,
                    threshold REAL,
                    severity TEXT,
                    status TEXT,
                    timestamp TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    timestamp TIMESTAMP
                )
            """
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error initializing analytics database: {e}")

    def _init_models(self):
        """Initialize machine learning models."""
        try:
            # Traditional ML models
            self.models["linear"] = LinearRegression()
            self.models["ridge"] = Ridge(alpha=1.0)
            self.models["lasso"] = Lasso(alpha=1.0)
            self.models["elastic_net"] = ElasticNet(alpha=1.0, l1_ratio=0.5)
            self.models["huber"] = HuberRegressor()
            self.models["ransac"] = RANSACRegressor()
            self.models["random_forest"] = RandomForestRegressor(
                n_estimators=100, random_state=42
            )
            self.models["gradient_boosting"] = GradientBoostingRegressor(
                n_estimators=100, random_state=42
            )
            self.models["neural_network"] = MLPRegressor(
                hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42
            )

            # Deep Learning models
            # LSTM model
            self.models["lstm"] = Sequential(
                [
                    Bidirectional(LSTM(50, activation="relu", return_sequences=True)),
                    Dropout(0.2),
                    Bidirectional(LSTM(30, activation="relu")),
                    Dropout(0.2),
                    Dense(1),
                ]
            )
            self.models["lstm"].compile(optimizer=Adam(learning_rate=0.001), loss="mse")

            # GRU model
            self.models["gru"] = Sequential(
                [
                    Bidirectional(GRU(50, activation="relu", return_sequences=True)),
                    Dropout(0.2),
                    Bidirectional(GRU(30, activation="relu")),
                    Dropout(0.2),
                    Dense(1),
                ]
            )
            self.models["gru"].compile(optimizer=Adam(learning_rate=0.001), loss="mse")

            # CNN-LSTM model
            self.models["cnn_lstm"] = Sequential(
                [
                    Conv1D(
                        filters=64,
                        kernel_size=3,
                        activation="relu",
                        input_shape=(24, 5),
                    ),
                    MaxPooling1D(pool_size=2),
                    LSTM(50, activation="relu", return_sequences=True),
                    Dropout(0.2),
                    LSTM(30, activation="relu"),
                    Dropout(0.2),
                    Dense(1),
                ]
            )
            self.models["cnn_lstm"].compile(
                optimizer=Adam(learning_rate=0.001), loss="mse"
            )

            # Time series models
            self.models["prophet"] = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=True,
                changepoint_prior_scale=0.05,
            )

            # Clustering models
            self.models["kmeans"] = KMeans(n_clusters=3, random_state=42)
            self.models["dbscan"] = DBSCAN(eps=0.5, min_samples=5)
            self.models["agglomerative"] = AgglomerativeClustering(n_clusters=3)
            self.models["gmm"] = GaussianMixture(n_components=3, random_state=42)

            # Ensemble models
            estimators = [
                ("rf", self.models["random_forest"]),
                ("gb", self.models["gradient_boosting"]),
                ("nn", self.models["neural_network"]),
            ]
            self.models["voting"] = VotingRegressor(estimators=estimators)
            self.models["stacking"] = StackingRegressor(
                estimators=estimators, final_estimator=LinearRegression()
            )

            logger.info("Machine learning models initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing models: {e}")

    def _start_monitoring(self):
        """Start system monitoring in a background thread."""

        def monitor_system():
            while True:
                try:
                    # Collect system metrics
                    cpu_usage = psutil.cpu_percent()
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage("/")
                    network = psutil.net_io_counters()

                    # Get email metrics
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()

                    # Get queue size
                    c.execute(
                        'SELECT COUNT(*) FROM email_queue WHERE status = "pending"'
                    )
                    queue_size = c.fetchone()[0]

                    # Get error rate
                    c.execute(
                        """
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures
                        FROM email_queue
                        WHERE created_at >= datetime('now', '-1 hour')
                    """
                    )
                    total, failures = c.fetchone()
                    error_rate = (failures / total * 100) if total > 0 else 0

                    # Get average response time and processing time
                    c.execute(
                        """
                        SELECT 
                            AVG(CASE WHEN status = 'sent' 
                                THEN (julianday(sent_at) - julianday(created_at)) * 24 * 60 * 60 * 1000
                                ELSE NULL END) as avg_response_time,
                            AVG(CASE WHEN status = 'sent' 
                                THEN (julianday(processed_at) - julianday(created_at)) * 24 * 60 * 60 * 1000
                                ELSE NULL END) as avg_processing_time
                        FROM email_queue
                        WHERE created_at >= datetime('now', '-1 hour')
                    """
                    )
                    avg_response_time, avg_processing_time = c.fetchone()
                    avg_response_time = avg_response_time or 0
                    avg_processing_time = avg_processing_time or 0

                    # Get consecutive failures
                    c.execute(
                        """
                        SELECT COUNT(*) FROM (
                            SELECT status,
                                ROW_NUMBER() OVER (ORDER BY created_at) as rn
                            FROM email_queue
                            WHERE created_at >= datetime('now', '-1 hour')
                            ORDER BY created_at DESC
                        ) WHERE status = 'failed'
                    """
                    )
                    consecutive_failures = c.fetchone()[0]

                    # Update performance metrics
                    self.performance_metrics.update(
                        {
                            "queue_size": queue_size,
                            "processing_time": avg_processing_time,
                            "consecutive_failures": consecutive_failures,
                        }
                    )

                    # Store metrics in database
                    c.execute(
                        """
                        INSERT INTO system_metrics 
                        (cpu_usage, memory_usage, disk_usage, network_io, error_rate, 
                         response_time, queue_size, processing_time, consecutive_failures, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                        (
                            cpu_usage,
                            memory.percent,
                            disk.percent,
                            network.bytes_sent + network.bytes_recv,
                            error_rate,
                            avg_response_time,
                            queue_size,
                            avg_processing_time,
                            consecutive_failures,
                        ),
                    )

                    # Check for alerts
                    self._check_alerts(
                        {
                            "cpu_usage": cpu_usage,
                            "memory_usage": memory.percent,
                            "disk_usage": disk.percent,
                            "error_rate": error_rate,
                            "response_time": avg_response_time,
                            "queue_size": queue_size,
                            "processing_time": avg_processing_time,
                            "consecutive_failures": consecutive_failures,
                        }
                    )

                    conn.commit()
                    conn.close()

                    # Sleep for 5 minutes
                    time.sleep(300)

                except Exception as e:
                    logger.error(f"Error in system monitoring: {e}")
                    time.sleep(60)  # Sleep for 1 minute on error

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=monitor_system, daemon=True)
        self.monitoring_thread.start()

    def _check_alerts(self, metrics: Dict[str, float]):
        """Check if any metrics exceed thresholds and trigger alerts."""
        alerts = []
        for metric, value in metrics.items():
            if value > self.alert_thresholds[metric]:
                severity = (
                    "critical"
                    if value > self.alert_thresholds[metric] * 1.5
                    else "warning"
                )
                alerts.append(
                    {
                        "metric": metric,
                        "value": value,
                        "threshold": self.alert_thresholds[metric],
                        "severity": severity,
                        "status": "active",
                        "timestamp": datetime.now(),
                    }
                )
                logger.warning(
                    f"Alert: {metric} exceeded threshold ({value} > {self.alert_thresholds[metric]})"
                )

        if alerts:
            self._store_alerts(alerts)

    def _store_alerts(self, alerts: List[Dict[str, Any]]):
        """Store alerts in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            for alert in alerts:
                c.execute(
                    """
                    INSERT INTO alerts 
                    (metric, value, threshold, severity, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        alert["metric"],
                        alert["value"],
                        alert["threshold"],
                        alert["severity"],
                        alert["status"],
                        alert["timestamp"],
                    ),
                )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing alerts: {e}")

    def resolve_alert(self, alert_id: int):
        """Resolve an alert."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                UPDATE alerts 
                SET status = 'resolved', resolved_at = datetime('now')
                WHERE id = ?
            """,
                (alert_id,),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error resolving alert: {e}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                SELECT id, metric, value, threshold, severity, timestamp
                FROM alerts
                WHERE status = 'active'
                ORDER BY severity DESC, timestamp DESC
            """
            )

            alerts = []
            for row in c.fetchall():
                alerts.append(
                    {
                        "id": row[0],
                        "metric": row[1],
                        "value": row[2],
                        "threshold": row[3],
                        "severity": row[4],
                        "timestamp": row[5],
                    }
                )

            conn.close()
            return alerts

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics

    def analyze_performance_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Analyze performance patterns using statistical methods."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get performance data
            c.execute(
                """
                SELECT 
                    strftime('%Y-%m-%d %H', created_at) as hour,
                    COUNT(*) as volume,
                    AVG(CASE WHEN status = 'sent' 
                        THEN julianday(sent_at) - julianday(created_at) 
                        ELSE NULL END) * 24 * 60 as avg_delivery_time,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures,
                    AVG(CASE WHEN status = 'sent' 
                        THEN (julianday(sent_at) - julianday(created_at)) * 24 * 60 * 60 * 1000
                        ELSE NULL END) as avg_response_time
                FROM email_queue
                WHERE created_at >= datetime('now', ?)
                GROUP BY hour
                ORDER BY hour
            """,
                (f"-{days} days",),
            )

            data = pd.DataFrame(
                c.fetchall(),
                columns=[
                    "hour",
                    "volume",
                    "delivery_time",
                    "failures",
                    "response_time",
                ],
            )
            data["hour"] = pd.to_datetime(data["hour"])

            # Calculate statistical metrics
            stats_metrics = {
                "volume": {
                    "mean": data["volume"].mean(),
                    "std": data["volume"].std(),
                    "skew": stats.skew(data["volume"]),
                    "kurtosis": stats.kurtosis(data["volume"]),
                    "min": data["volume"].min(),
                    "max": data["volume"].max(),
                    "median": data["volume"].median(),
                    "q1": data["volume"].quantile(0.25),
                    "q3": data["volume"].quantile(0.75),
                    "iqr": data["volume"].quantile(0.75)
                    - data["volume"].quantile(0.25),
                    "cv": (
                        data["volume"].std() / data["volume"].mean()
                        if data["volume"].mean() != 0
                        else 0
                    ),
                },
                "delivery_time": {
                    "mean": data["delivery_time"].mean(),
                    "std": data["delivery_time"].std(),
                    "skew": stats.skew(data["delivery_time"].dropna()),
                    "kurtosis": stats.kurtosis(data["delivery_time"].dropna()),
                    "min": data["delivery_time"].min(),
                    "max": data["delivery_time"].max(),
                    "median": data["delivery_time"].median(),
                    "q1": data["delivery_time"].quantile(0.25),
                    "q3": data["delivery_time"].quantile(0.75),
                    "iqr": data["delivery_time"].quantile(0.75)
                    - data["delivery_time"].quantile(0.25),
                    "cv": (
                        data["delivery_time"].std() / data["delivery_time"].mean()
                        if data["delivery_time"].mean() != 0
                        else 0
                    ),
                },
                "failures": {
                    "mean": data["failures"].mean(),
                    "std": data["failures"].std(),
                    "skew": stats.skew(data["failures"]),
                    "kurtosis": stats.kurtosis(data["failures"]),
                    "min": data["failures"].min(),
                    "max": data["failures"].max(),
                    "median": data["failures"].median(),
                    "q1": data["failures"].quantile(0.25),
                    "q3": data["failures"].quantile(0.75),
                    "iqr": data["failures"].quantile(0.75)
                    - data["failures"].quantile(0.25),
                    "cv": (
                        data["failures"].std() / data["failures"].mean()
                        if data["failures"].mean() != 0
                        else 0
                    ),
                },
                "response_time": {
                    "mean": data["response_time"].mean(),
                    "std": data["response_time"].std(),
                    "skew": stats.skew(data["response_time"].dropna()),
                    "kurtosis": stats.kurtosis(data["response_time"].dropna()),
                    "min": data["response_time"].min(),
                    "max": data["response_time"].max(),
                    "median": data["response_time"].median(),
                    "q1": data["response_time"].quantile(0.25),
                    "q3": data["response_time"].quantile(0.75),
                    "iqr": data["response_time"].quantile(0.75)
                    - data["response_time"].quantile(0.25),
                    "cv": (
                        data["response_time"].std() / data["response_time"].mean()
                        if data["response_time"].mean() != 0
                        else 0
                    ),
                },
            }

            # Calculate correlations
            correlations = data[
                ["volume", "delivery_time", "failures", "response_time"]
            ].corr()

            # Perform time series decomposition
            volume_ts = data.set_index("hour")["volume"]
            delivery_time_ts = data.set_index("hour")["delivery_time"]
            failures_ts = data.set_index("hour")["failures"]
            response_time_ts = data.set_index("hour")["response_time"]

            # Calculate moving averages
            volume_ma = volume_ts.rolling(window=24).mean()
            delivery_time_ma = delivery_time_ts.rolling(window=24).mean()
            failures_ma = failures_ts.rolling(window=24).mean()
            response_time_ma = response_time_ts.rolling(window=24).mean()

            # Calculate seasonality
            volume_seasonal = volume_ts - volume_ma
            delivery_time_seasonal = delivery_time_ts - delivery_time_ma
            failures_seasonal = failures_ts - failures_ma
            response_time_seasonal = response_time_ts - response_time_ma

            # Calculate trends
            volume_trend = detrend(volume_ts.values)
            delivery_time_trend = detrend(delivery_time_ts.values)
            failures_trend = detrend(failures_ts.values)
            response_time_trend = detrend(response_time_ts.values)

            # Perform statistical tests
            statistical_tests = {
                "volume": {
                    "normality": stats.normaltest(volume_ts.values),
                    "stationarity": stats.adfuller(volume_ts.values),
                    "seasonality": stats.periodogram(volume_ts.values)[1],
                },
                "delivery_time": {
                    "normality": stats.normaltest(delivery_time_ts.dropna().values),
                    "stationarity": stats.adfuller(delivery_time_ts.dropna().values),
                    "seasonality": stats.periodogram(delivery_time_ts.dropna().values)[
                        1
                    ],
                },
                "failures": {
                    "normality": stats.normaltest(failures_ts.values),
                    "stationarity": stats.adfuller(failures_ts.values),
                    "seasonality": stats.periodogram(failures_ts.values)[1],
                },
                "response_time": {
                    "normality": stats.normaltest(response_time_ts.dropna().values),
                    "stationarity": stats.adfuller(response_time_ts.dropna().values),
                    "seasonality": stats.periodogram(response_time_ts.dropna().values)[
                        1
                    ],
                },
            }

            # Calculate performance metrics
            performance_metrics = {
                "volume": {
                    "peak_hour": volume_ts.idxmax(),
                    "peak_value": volume_ts.max(),
                    "valley_hour": volume_ts.idxmin(),
                    "valley_value": volume_ts.min(),
                    "peak_to_valley_ratio": (
                        volume_ts.max() / volume_ts.min()
                        if volume_ts.min() != 0
                        else float("inf")
                    ),
                },
                "delivery_time": {
                    "peak_hour": delivery_time_ts.idxmax(),
                    "peak_value": delivery_time_ts.max(),
                    "valley_hour": delivery_time_ts.idxmin(),
                    "valley_value": delivery_time_ts.min(),
                    "peak_to_valley_ratio": (
                        delivery_time_ts.max() / delivery_time_ts.min()
                        if delivery_time_ts.min() != 0
                        else float("inf")
                    ),
                },
                "failures": {
                    "peak_hour": failures_ts.idxmax(),
                    "peak_value": failures_ts.max(),
                    "valley_hour": failures_ts.idxmin(),
                    "valley_value": failures_ts.min(),
                    "peak_to_valley_ratio": (
                        failures_ts.max() / failures_ts.min()
                        if failures_ts.min() != 0
                        else float("inf")
                    ),
                },
                "response_time": {
                    "peak_hour": response_time_ts.idxmax(),
                    "peak_value": response_time_ts.max(),
                    "valley_hour": response_time_ts.idxmin(),
                    "valley_value": response_time_ts.min(),
                    "peak_to_valley_ratio": (
                        response_time_ts.max() / response_time_ts.min()
                        if response_time_ts.min() != 0
                        else float("inf")
                    ),
                },
            }

            conn.close()

            return {
                "statistical_metrics": stats_metrics,
                "correlations": correlations.to_dict(),
                "time_series": {
                    "volume": {
                        "trend": volume_trend.tolist(),
                        "seasonal": volume_seasonal.to_dict(),
                        "moving_average": volume_ma.to_dict(),
                    },
                    "delivery_time": {
                        "trend": delivery_time_trend.tolist(),
                        "seasonal": delivery_time_seasonal.to_dict(),
                        "moving_average": delivery_time_ma.to_dict(),
                    },
                    "failures": {
                        "trend": failures_trend.tolist(),
                        "seasonal": failures_seasonal.to_dict(),
                        "moving_average": failures_ma.to_dict(),
                    },
                    "response_time": {
                        "trend": response_time_trend.tolist(),
                        "seasonal": response_time_seasonal.to_dict(),
                        "moving_average": response_time_ma.to_dict(),
                    },
                },
                "statistical_tests": statistical_tests,
                "performance_metrics": performance_metrics,
            }

        except Exception as e:
            logger.error(f"Error analyzing performance patterns: {e}")
            return {}

    def evaluate_models(self, days: int = 30) -> Dict[str, Any]:
        """Evaluate all machine learning models."""
        try:
            # Get historical data
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get hourly email volumes
            c.execute(
                """
                SELECT 
                    strftime('%Y-%m-%d %H', created_at) as hour,
                    COUNT(*) as volume
                FROM email_queue
                WHERE created_at >= datetime('now', ?)
                GROUP BY hour
                ORDER BY hour
            """,
                (f"-{days} days",),
            )

            data = pd.DataFrame(c.fetchall(), columns=["hour", "volume"])
            data["hour"] = pd.to_datetime(data["hour"])

            # Prepare features
            data["hour_of_day"] = data["hour"].dt.hour
            data["day_of_week"] = data["hour"].dt.dayofweek
            data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)
            data["month"] = data["hour"].dt.month
            data["quarter"] = data["hour"].dt.quarter

            # Create lag features
            for lag in [1, 2, 3, 24]:
                data[f"volume_lag_{lag}"] = data["volume"].shift(lag)

            # Create rolling features
            for window in [3, 6, 12, 24]:
                data[f"volume_ma_{window}"] = (
                    data["volume"].rolling(window=window).mean()
                )
                data[f"volume_std_{window}"] = (
                    data["volume"].rolling(window=window).std()
                )

            # Drop rows with NaN values
            data = data.dropna()

            # Prepare features and target
            features = (
                ["hour_of_day", "day_of_week", "is_weekend", "month", "quarter"]
                + [f"volume_lag_{i}" for i in [1, 2, 3, 24]]
                + [f"volume_ma_{i}" for i in [3, 6, 12, 24]]
                + [f"volume_std_{i}" for i in [3, 6, 12, 24]]
            )

            X = data[features]
            y = data["volume"]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Evaluate models
            model_scores = {}
            for name, model in self.models.items():
                if name not in [
                    "lstm",
                    "gru",
                    "cnn_lstm",
                    "prophet",
                    "kmeans",
                    "dbscan",
                    "agglomerative",
                    "gmm",
                ]:
                    # Train model
                    model.fit(X_train_scaled, y_train)

                    # Make predictions
                    y_pred = model.predict(X_test_scaled)

                    # Calculate metrics
                    model_scores[name] = {
                        "mse": mean_squared_error(y_test, y_pred),
                        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                        "mae": mean_absolute_error(y_test, y_pred),
                        "mape": mean_absolute_percentage_error(y_test, y_pred),
                        "r2": r2_score(y_test, y_pred),
                    }

                    # Store model performance
                    c.execute(
                        """
                        INSERT INTO model_performance 
                        (model_name, metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?, datetime('now'))
                    """,
                        (name, "mse", model_scores[name]["mse"]),
                    )

                    c.execute(
                        """
                        INSERT INTO model_performance 
                        (model_name, metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?, datetime('now'))
                    """,
                        (name, "rmse", model_scores[name]["rmse"]),
                    )

                    c.execute(
                        """
                        INSERT INTO model_performance 
                        (model_name, metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?, datetime('now'))
                    """,
                        (name, "mae", model_scores[name]["mae"]),
                    )

                    c.execute(
                        """
                        INSERT INTO model_performance 
                        (model_name, metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?, datetime('now'))
                    """,
                        (name, "mape", model_scores[name]["mape"]),
                    )

                    c.execute(
                        """
                        INSERT INTO model_performance 
                        (model_name, metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?, datetime('now'))
                    """,
                        (name, "r2", model_scores[name]["r2"]),
                    )

            conn.commit()
            conn.close()

            return {
                "model_scores": model_scores,
                "best_model": max(model_scores.items(), key=lambda x: x[1]["r2"])[0],
            }

        except Exception as e:
            logger.error(f"Error evaluating models: {e}")
            return {}

    def generate_advanced_report(self, days: int = 30) -> str:
        """Generate an advanced analytics report with interactive visualizations."""
        try:
            # Get performance patterns
            patterns = self.analyze_performance_patterns(days)

            # Create subplots
            fig = make_subplots(
                rows=4,
                cols=2,
                subplot_titles=(
                    "Email Volume Distribution",
                    "Delivery Time Distribution",
                    "Failure Rate Distribution",
                    "Response Time Distribution",
                    "Volume Trend Analysis",
                    "Delivery Time Trend Analysis",
                    "Failure Rate Trend Analysis",
                    "Response Time Trend Analysis",
                ),
                specs=[
                    [{"type": "histogram"}, {"type": "histogram"}],
                    [{"type": "histogram"}, {"type": "histogram"}],
                    [{"type": "scatter"}, {"type": "scatter"}],
                    [{"type": "scatter"}, {"type": "scatter"}],
                ],
            )

            # Add histograms with KDE
            for i, (metric, data) in enumerate(
                [
                    ("volume", patterns["statistical_metrics"]["volume"]),
                    ("delivery_time", patterns["statistical_metrics"]["delivery_time"]),
                    ("failures", patterns["statistical_metrics"]["failures"]),
                    ("response_time", patterns["statistical_metrics"]["response_time"]),
                ]
            ):
                row = i // 2 + 1
                col = i % 2 + 1

                # Add histogram
                fig.add_trace(
                    go.Histogram(
                        x=data["values"],
                        name=f"{metric} distribution",
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

                # Add KDE
                kde = stats.gaussian_kde(data["values"])
                x_range = np.linspace(min(data["values"]), max(data["values"]), 100)
                fig.add_trace(
                    go.Scatter(
                        x=x_range,
                        y=kde(x_range),
                        name=f"{metric} KDE",
                        line=dict(color="red"),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

            # Add trend analysis
            for i, (metric, data) in enumerate(
                [
                    ("volume", patterns["time_series"]["volume"]),
                    ("delivery_time", patterns["time_series"]["delivery_time"]),
                    ("failures", patterns["time_series"]["failures"]),
                    ("response_time", patterns["time_series"]["response_time"]),
                ]
            ):
                row = i // 2 + 3
                col = i % 2 + 1

                # Add trend line
                fig.add_trace(
                    go.Scatter(
                        x=list(data["moving_average"].keys()),
                        y=list(data["moving_average"].values()),
                        name=f"{metric} trend",
                        line=dict(color="blue"),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

                # Add seasonal component
                fig.add_trace(
                    go.Scatter(
                        x=list(data["seasonal"].keys()),
                        y=list(data["seasonal"].values()),
                        name=f"{metric} seasonal",
                        line=dict(color="green"),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

            # Update layout
            fig.update_layout(
                height=1200,
                width=1600,
                title_text="Advanced Email Analytics Report",
                showlegend=True,
                template="plotly_white",
            )

            # Add annotations for statistical tests
            for i, (metric, tests) in enumerate(patterns["statistical_tests"].items()):
                row = i // 2 + 1
                col = i % 2 + 1

                # Add normality test results
                fig.add_annotation(
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=1.05 - (row * 0.25),
                    text=f"{metric.capitalize()} Normality Test: p-value = {tests['normality'][1]:.4f}",
                    showarrow=False,
                )

                # Add stationarity test results
                fig.add_annotation(
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=1.02 - (row * 0.25),
                    text=f"{metric.capitalize()} Stationarity Test: p-value = {tests['stationarity'][1]:.4f}",
                    showarrow=False,
                )

            # Save the report
            report_path = (
                self.reports_dir
                / f"advanced_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            fig.write_html(str(report_path))

            # Generate summary statistics
            summary = {
                "overall_metrics": {
                    "total_emails": sum(
                        patterns["statistical_metrics"]["volume"]["values"]
                    ),
                    "avg_delivery_time": patterns["statistical_metrics"][
                        "delivery_time"
                    ]["mean"],
                    "failure_rate": patterns["statistical_metrics"]["failures"]["mean"]
                    / patterns["statistical_metrics"]["volume"]["mean"]
                    * 100,
                    "avg_response_time": patterns["statistical_metrics"][
                        "response_time"
                    ]["mean"],
                },
                "peak_performance": {
                    "volume": patterns["performance_metrics"]["volume"],
                    "delivery_time": patterns["performance_metrics"]["delivery_time"],
                    "failures": patterns["performance_metrics"]["failures"],
                    "response_time": patterns["performance_metrics"]["response_time"],
                },
                "statistical_tests": patterns["statistical_tests"],
            }

            # Save summary to JSON
            summary_path = (
                self.reports_dir
                / f"advanced_report_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=4, default=str)

            return str(report_path)

        except Exception as e:
            logger.error(f"Error generating advanced report: {e}")
            return ""

    def detect_anomalies_advanced(self, days: int = 30) -> Dict[str, Any]:
        """Detect anomalies using multiple methods and ensemble approach."""
        try:
            # Get historical data
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get hourly metrics
            c.execute(
                """
                SELECT 
                    strftime('%Y-%m-%d %H', created_at) as hour,
                    COUNT(*) as volume,
                    AVG(CASE WHEN status = 'sent' 
                        THEN julianday(sent_at) - julianday(created_at) 
                        ELSE NULL END) * 24 * 60 as avg_delivery_time,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures,
                    AVG(CASE WHEN status = 'sent' 
                        THEN (julianday(sent_at) - julianday(created_at)) * 24 * 60 * 60 * 1000
                        ELSE NULL END) as avg_response_time
                FROM email_queue
                WHERE created_at >= datetime('now', ?)
                GROUP BY hour
                ORDER BY hour
            """,
                (f"-{days} days",),
            )

            data = pd.DataFrame(
                c.fetchall(),
                columns=[
                    "hour",
                    "volume",
                    "delivery_time",
                    "failures",
                    "response_time",
                ],
            )
            data["hour"] = pd.to_datetime(data["hour"])

            # Prepare features for anomaly detection
            features = ["volume", "delivery_time", "failures", "response_time"]
            X = data[features].fillna(0)

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Initialize anomaly detection methods
            methods = {
                "isolation_forest": IsolationForest(contamination=0.1, random_state=42),
                "dbscan": DBSCAN(eps=0.5, min_samples=5),
                "gmm": GaussianMixture(n_components=3, random_state=42),
                "kmeans": KMeans(n_clusters=3, random_state=42),
            }

            # Detect anomalies using each method
            anomaly_scores = {}
            for name, method in methods.items():
                if name == "isolation_forest":
                    # Isolation Forest returns -1 for anomalies, 1 for normal
                    scores = method.fit_predict(X_scaled)
                    anomaly_scores[name] = (scores == -1).astype(int)
                elif name == "dbscan":
                    # DBSCAN returns -1 for anomalies, cluster labels for normal
                    scores = method.fit_predict(X_scaled)
                    anomaly_scores[name] = (scores == -1).astype(int)
                else:
                    # GMM and KMeans use distance to cluster centers
                    if name == "gmm":
                        method.fit(X_scaled)
                        scores = -method.score_samples(X_scaled)
                    else:
                        method.fit(X_scaled)
                        scores = method.transform(X_scaled).min(axis=1)

                    # Convert to binary using threshold
                    threshold = np.percentile(scores, 90)  # Top 10% as anomalies
                    anomaly_scores[name] = (scores > threshold).astype(int)

            # Ensemble approach: combine results from all methods
            ensemble_scores = np.mean(
                [scores for scores in anomaly_scores.values()], axis=0
            )
            ensemble_anomalies = (ensemble_scores > 0.5).astype(int)

            # Get anomaly details
            anomaly_details = []
            for i, is_anomaly in enumerate(ensemble_anomalies):
                if is_anomaly:
                    hour = data.iloc[i]["hour"]
                    metrics = {
                        "volume": data.iloc[i]["volume"],
                        "delivery_time": data.iloc[i]["delivery_time"],
                        "failures": data.iloc[i]["failures"],
                        "response_time": data.iloc[i]["response_time"],
                    }

                    # Calculate deviation from normal
                    deviations = {}
                    for metric, value in metrics.items():
                        mean = data[metric].mean()
                        std = data[metric].std()
                        if std != 0:
                            deviations[metric] = (value - mean) / std
                        else:
                            deviations[metric] = 0

                    anomaly_details.append(
                        {
                            "hour": hour,
                            "metrics": metrics,
                            "deviations": deviations,
                            "method_scores": {
                                name: scores[i]
                                for name, scores in anomaly_scores.items()
                            },
                        }
                    )

            # Store anomalies in database
            for anomaly in anomaly_details:
                c.execute(
                    """
                    INSERT INTO email_events 
                    (event_type, event_data, timestamp)
                    VALUES (?, ?, ?)
                """,
                    ("anomaly", json.dumps(anomaly), anomaly["hour"]),
                )

            conn.commit()
            conn.close()

            return {
                "total_anomalies": sum(ensemble_anomalies),
                "anomaly_details": anomaly_details,
                "method_scores": {
                    name: sum(scores) for name, scores in anomaly_scores.items()
                },
                "ensemble_score": sum(ensemble_anomalies),
            }

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {}

    def predict_metrics_advanced(self, hours: int = 24) -> Dict[str, Any]:
        """Predict future metrics using ensemble of models."""
        try:
            # Get historical data
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get hourly metrics
            c.execute(
                """
                SELECT 
                    strftime('%Y-%m-%d %H', created_at) as hour,
                    COUNT(*) as volume,
                    AVG(CASE WHEN status = 'sent' 
                        THEN julianday(sent_at) - julianday(created_at) 
                        ELSE NULL END) * 24 * 60 as avg_delivery_time,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures,
                    AVG(CASE WHEN status = 'sent' 
                        THEN (julianday(sent_at) - julianday(created_at)) * 24 * 60 * 60 * 1000
                        ELSE NULL END) as avg_response_time
                FROM email_queue
                WHERE created_at >= datetime('now', '-30 days')
                GROUP BY hour
                ORDER BY hour
            """
            )

            data = pd.DataFrame(
                c.fetchall(),
                columns=[
                    "hour",
                    "volume",
                    "delivery_time",
                    "failures",
                    "response_time",
                ],
            )
            data["hour"] = pd.to_datetime(data["hour"])

            # Prepare features
            data["hour_of_day"] = data["hour"].dt.hour
            data["day_of_week"] = data["hour"].dt.dayofweek
            data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)
            data["month"] = data["hour"].dt.month
            data["quarter"] = data["hour"].dt.quarter

            # Create lag features
            for lag in [1, 2, 3, 24]:
                for col in ["volume", "delivery_time", "failures", "response_time"]:
                    data[f"{col}_lag_{lag}"] = data[col].shift(lag)

            # Create rolling features
            for window in [3, 6, 12, 24]:
                for col in ["volume", "delivery_time", "failures", "response_time"]:
                    data[f"{col}_ma_{window}"] = data[col].rolling(window=window).mean()
                    data[f"{col}_std_{window}"] = data[col].rolling(window=window).std()

            # Drop rows with NaN values
            data = data.dropna()

            # Prepare features and targets
            feature_cols = [
                col
                for col in data.columns
                if col
                not in ["hour", "volume", "delivery_time", "failures", "response_time"]
            ]
            X = data[feature_cols]
            y = data[["volume", "delivery_time", "failures", "response_time"]]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train models for each target
            predictions = {}
            for target in ["volume", "delivery_time", "failures", "response_time"]:
                # Train models
                model_predictions = []
                for name, model in self.models.items():
                    if name not in [
                        "lstm",
                        "gru",
                        "cnn_lstm",
                        "prophet",
                        "kmeans",
                        "dbscan",
                        "agglomerative",
                        "gmm",
                    ]:
                        # Train model
                        model.fit(X_train_scaled, y_train[target])

                        # Make predictions
                        y_pred = model.predict(X_test_scaled)
                        model_predictions.append(y_pred)

                # Ensemble predictions
                ensemble_pred = np.mean(model_predictions, axis=0)
                ensemble_std = np.std(model_predictions, axis=0)

                predictions[target] = {
                    "mean": ensemble_pred.tolist(),
                    "std": ensemble_std.tolist(),
                    "confidence_interval": {
                        "lower": (ensemble_pred - 1.96 * ensemble_std).tolist(),
                        "upper": (ensemble_pred + 1.96 * ensemble_std).tolist(),
                    },
                }

                # Store predictions in database
                for i, (mean, std) in enumerate(zip(ensemble_pred, ensemble_std)):
                    c.execute(
                        """
                        INSERT INTO predictions 
                        (metric_name, predicted_value, confidence, model_name, timestamp)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """,
                        (target, float(mean), float(std), "ensemble"),
                    )

            conn.commit()
            conn.close()

            return predictions

        except Exception as e:
            logger.error(f"Error predicting metrics: {e}")
            return {}

    def evaluate_models_advanced(self, days: int = 30) -> Dict[str, Any]:
        """Evaluate models with advanced metrics and visualizations."""
        try:
            # Get historical data
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get hourly metrics
            c.execute(
                """
                SELECT 
                    strftime('%Y-%m-%d %H', created_at) as hour,
                    COUNT(*) as volume,
                    AVG(CASE WHEN status = 'sent' 
                        THEN julianday(sent_at) - julianday(created_at) 
                        ELSE NULL END) * 24 * 60 as avg_delivery_time,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures,
                    AVG(CASE WHEN status = 'sent' 
                        THEN (julianday(sent_at) - julianday(created_at)) * 24 * 60 * 60 * 1000
                        ELSE NULL END) as avg_response_time
                FROM email_queue
                WHERE created_at >= datetime('now', ?)
                GROUP BY hour
                ORDER BY hour
            """,
                (f"-{days} days",),
            )

            data = pd.DataFrame(
                c.fetchall(),
                columns=[
                    "hour",
                    "volume",
                    "delivery_time",
                    "failures",
                    "response_time",
                ],
            )
            data["hour"] = pd.to_datetime(data["hour"])

            # Prepare features
            data["hour_of_day"] = data["hour"].dt.hour
            data["day_of_week"] = data["hour"].dt.dayofweek
            data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)
            data["month"] = data["hour"].dt.month
            data["quarter"] = data["hour"].dt.quarter

            # Create lag features
            for lag in [1, 2, 3, 24]:
                for col in ["volume", "delivery_time", "failures", "response_time"]:
                    data[f"{col}_lag_{lag}"] = data[col].shift(lag)

            # Create rolling features
            for window in [3, 6, 12, 24]:
                for col in ["volume", "delivery_time", "failures", "response_time"]:
                    data[f"{col}_ma_{window}"] = data[col].rolling(window=window).mean()
                    data[f"{col}_std_{window}"] = data[col].rolling(window=window).std()

            # Drop rows with NaN values
            data = data.dropna()

            # Prepare features and targets
            feature_cols = [
                col
                for col in data.columns
                if col
                not in ["hour", "volume", "delivery_time", "failures", "response_time"]
            ]
            X = data[feature_cols]
            y = data[["volume", "delivery_time", "failures", "response_time"]]

            # Split data using time series split
            tscv = TimeSeriesSplit(n_splits=5)

            # Initialize results storage
            model_results = {}

            # Create visualization figure
            fig = make_subplots(
                rows=4,
                cols=2,
                subplot_titles=(
                    "Model Performance Comparison",
                    "Feature Importance",
                    "Prediction vs Actual",
                    "Residual Analysis",
                    "Cross-Validation Scores",
                    "Learning Curves",
                    "Error Distribution",
                    "Confidence Intervals",
                ),
            )

            # Evaluate each target
            for target in ["volume", "delivery_time", "failures", "response_time"]:
                model_results[target] = {}

                # Cross-validation scores
                cv_scores = {}
                for name, model in self.models.items():
                    if name not in [
                        "lstm",
                        "gru",
                        "cnn_lstm",
                        "prophet",
                        "kmeans",
                        "dbscan",
                        "agglomerative",
                        "gmm",
                    ]:
                        scores = cross_val_score(
                            model, X, y[target], cv=tscv, scoring="r2"
                        )
                        cv_scores[name] = scores

                        # Add to visualization
                        fig.add_trace(
                            go.Box(
                                y=scores,
                                name=name,
                                boxpoints="all",
                                jitter=0.3,
                                pointpos=-1.8,
                            ),
                            row=1,
                            col=1,
                        )

                # Train-test split
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y[target], test_size=0.2, random_state=42
                )

                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)

                # Train and evaluate models
                for name, model in self.models.items():
                    if name not in [
                        "lstm",
                        "gru",
                        "cnn_lstm",
                        "prophet",
                        "kmeans",
                        "dbscan",
                        "agglomerative",
                        "gmm",
                    ]:
                        # Train model
                        model.fit(X_train_scaled, y_train)

                        # Make predictions
                        y_pred = model.predict(X_test_scaled)

                        # Calculate metrics
                        metrics = {
                            "mse": mean_squared_error(y_test, y_pred),
                            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                            "mae": mean_absolute_error(y_test, y_pred),
                            "mape": mean_absolute_percentage_error(y_test, y_pred),
                            "r2": r2_score(y_test, y_pred),
                            "explained_variance": explained_variance_score(
                                y_test, y_pred
                            ),
                            "max_error": max_error(y_test, y_pred),
                        }

                        model_results[target][name] = metrics

                        # Store in database
                        for metric_name, value in metrics.items():
                            c.execute(
                                """
                                INSERT INTO model_performance 
                                (model_name, metric_name, metric_value, timestamp)
                                VALUES (?, ?, ?, datetime('now'))
                            """,
                                (name, metric_name, value),
                            )

                        # Add to visualization
                        # Prediction vs Actual
                        fig.add_trace(
                            go.Scatter(
                                x=y_test,
                                y=y_pred,
                                mode="markers",
                                name=f"{name} - {target}",
                                showlegend=False,
                            ),
                            row=1,
                            col=2,
                        )

                        # Residual Analysis
                        residuals = y_test - y_pred
                        fig.add_trace(
                            go.Scatter(
                                x=y_pred,
                                y=residuals,
                                mode="markers",
                                name=f"{name} - {target}",
                                showlegend=False,
                            ),
                            row=2,
                            col=2,
                        )

                        # Error Distribution
                        fig.add_trace(
                            go.Histogram(
                                x=residuals, name=f"{name} - {target}", showlegend=False
                            ),
                            row=3,
                            col=2,
                        )

                        # Feature Importance (for tree-based models)
                        if hasattr(model, "feature_importances_"):
                            importances = model.feature_importances_
                            indices = np.argsort(importances)[::-1]

                            fig.add_trace(
                                go.Bar(
                                    x=[feature_cols[i] for i in indices],
                                    y=importances[indices],
                                    name=f"{name} - {target}",
                                    showlegend=False,
                                ),
                                row=1,
                                col=2,
                            )

            # Update layout
            fig.update_layout(
                height=1600,
                width=2000,
                title_text="Advanced Model Evaluation Report",
                showlegend=True,
                template="plotly_white",
            )

            # Save the report
            report_path = (
                self.reports_dir
                / f"model_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            fig.write_html(str(report_path))

            conn.commit()
            conn.close()

            return {"model_results": model_results, "report_path": str(report_path)}

        except Exception as e:
            logger.error(f"Error evaluating models: {e}")
            return {}

    def monitor_system_advanced(self) -> Dict[str, Any]:
        """Advanced system monitoring with predictive alerts."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Get system metrics for the last 24 hours
            c.execute(
                """
                SELECT 
                    cpu_usage, memory_usage, disk_usage, network_io,
                    error_rate, response_time, queue_size, processing_time,
                    consecutive_failures, timestamp
                FROM system_metrics
                WHERE timestamp >= datetime('now', '-24 hours')
                ORDER BY timestamp
            """
            )

            metrics = pd.DataFrame(
                c.fetchall(),
                columns=[
                    "cpu_usage",
                    "memory_usage",
                    "disk_usage",
                    "network_io",
                    "error_rate",
                    "response_time",
                    "queue_size",
                    "processing_time",
                    "consecutive_failures",
                    "timestamp",
                ],
            )
            metrics["timestamp"] = pd.to_datetime(metrics["timestamp"])

            # Calculate trend analysis
            trends = {}
            for col in metrics.columns[:-1]:  # Exclude timestamp
                series = metrics[col]
                trend = {
                    "current": series.iloc[-1],
                    "mean_24h": series.mean(),
                    "std_24h": series.std(),
                    "min_24h": series.min(),
                    "max_24h": series.max(),
                    "trend_1h": series.tail(12).mean()
                    - series.tail(24).head(12).mean(),
                    "zscore": (
                        (series.iloc[-1] - series.mean()) / series.std()
                        if series.std() != 0
                        else 0
                    ),
                }
                trends[col] = trend

            # Predict next hour values using exponential smoothing
            predictions = {}
            for col in metrics.columns[:-1]:
                series = metrics[col]
                model = ExponentialSmoothing(
                    series, seasonal_periods=24, trend="add", seasonal="add"
                ).fit()
                forecast = model.forecast(12)  # Next hour (12 5-minute intervals)
                predictions[col] = {
                    "mean": forecast.mean(),
                    "std": forecast.std(),
                    "lower": forecast.mean() - 1.96 * forecast.std(),
                    "upper": forecast.mean() + 1.96 * forecast.std(),
                }

            # Generate alerts based on current values and predictions
            alerts = []
            for metric, trend in trends.items():
                threshold = self.alert_thresholds.get(metric, float("inf"))
                prediction = predictions[metric]

                # Current value alert
                if trend["current"] > threshold:
                    severity = (
                        "critical" if trend["current"] > threshold * 1.5 else "warning"
                    )
                    alerts.append(
                        {
                            "metric": metric,
                            "type": "current",
                            "value": trend["current"],
                            "threshold": threshold,
                            "severity": severity,
                            "message": f"{metric} exceeds threshold: {trend['current']:.2f} > {threshold:.2f}",
                        }
                    )

                # Trend alert
                if trend["zscore"] > 2:  # More than 2 standard deviations from mean
                    alerts.append(
                        {
                            "metric": metric,
                            "type": "trend",
                            "value": trend["zscore"],
                            "threshold": 2,
                            "severity": "warning",
                            "message": f"{metric} shows abnormal trend: z-score = {trend['zscore']:.2f}",
                        }
                    )

                # Prediction alert
                if prediction["lower"] > threshold:
                    alerts.append(
                        {
                            "metric": metric,
                            "type": "prediction",
                            "value": prediction["mean"],
                            "threshold": threshold,
                            "severity": "warning",
                            "message": f"{metric} predicted to exceed threshold: {prediction['mean']:.2f} > {threshold:.2f}",
                        }
                    )

            # Store alerts in database
            for alert in alerts:
                c.execute(
                    """
                    INSERT INTO alerts 
                    (metric, value, threshold, severity, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                    (
                        alert["metric"],
                        alert["value"],
                        alert["threshold"],
                        alert["severity"],
                        "active",
                    ),
                )

            # Create visualization
            fig = make_subplots(
                rows=3,
                cols=2,
                subplot_titles=(
                    "System Metrics Trends",
                    "Resource Usage",
                    "Performance Metrics",
                    "Error Rates",
                    "Predictions",
                    "Alert Distribution",
                ),
            )

            # Add system metrics trends
            for i, metric in enumerate(["cpu_usage", "memory_usage", "disk_usage"]):
                fig.add_trace(
                    go.Scatter(
                        x=metrics["timestamp"],
                        y=metrics[metric],
                        name=metric,
                        mode="lines",
                    ),
                    row=1,
                    col=1,
                )

            # Add resource usage
            fig.add_trace(
                go.Bar(
                    x=["CPU", "Memory", "Disk", "Network"],
                    y=[
                        metrics["cpu_usage"].iloc[-1],
                        metrics["memory_usage"].iloc[-1],
                        metrics["disk_usage"].iloc[-1],
                        metrics["network_io"].iloc[-1],
                    ],
                    name="Current Usage",
                ),
                row=1,
                col=2,
            )

            # Add performance metrics
            for metric in ["response_time", "processing_time", "queue_size"]:
                fig.add_trace(
                    go.Scatter(
                        x=metrics["timestamp"],
                        y=metrics[metric],
                        name=metric,
                        mode="lines",
                    ),
                    row=2,
                    col=1,
                )

            # Add error rates
            fig.add_trace(
                go.Scatter(
                    x=metrics["timestamp"],
                    y=metrics["error_rate"],
                    name="Error Rate",
                    mode="lines",
                ),
                row=2,
                col=2,
            )

            # Add predictions
            for metric in predictions:
                fig.add_trace(
                    go.Scatter(
                        x=["Now", "+1h"],
                        y=[metrics[metric].iloc[-1], predictions[metric]["mean"]],
                        name=f"{metric} prediction",
                        mode="lines+markers",
                        error_y=dict(
                            type="data",
                            array=[0, predictions[metric]["std"] * 1.96],
                            visible=True,
                        ),
                    ),
                    row=3,
                    col=1,
                )

            # Add alert distribution
            alert_counts = (
                pd.DataFrame(alerts)
                .groupby(["metric", "severity"])
                .size()
                .unstack(fill_value=0)
            )
            fig.add_trace(
                go.Bar(
                    x=alert_counts.index,
                    y=alert_counts["warning"],
                    name="Warning Alerts",
                    marker_color="yellow",
                ),
                row=3,
                col=2,
            )
            fig.add_trace(
                go.Bar(
                    x=alert_counts.index,
                    y=alert_counts["critical"],
                    name="Critical Alerts",
                    marker_color="red",
                ),
                row=3,
                col=2,
            )

            # Update layout
            fig.update_layout(
                height=1200,
                width=1600,
                title_text="System Monitoring Dashboard",
                showlegend=True,
                template="plotly_white",
            )

            # Save the dashboard
            dashboard_path = (
                self.reports_dir
                / f"monitoring_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            fig.write_html(str(dashboard_path))

            conn.commit()
            conn.close()

            return {
                "trends": trends,
                "predictions": predictions,
                "alerts": alerts,
                "dashboard_path": str(dashboard_path),
            }

        except Exception as e:
            logger.error(f"Error in advanced system monitoring: {e}")
            return {}


# Create a singleton instance
email_analytics = EmailAnalytics()
