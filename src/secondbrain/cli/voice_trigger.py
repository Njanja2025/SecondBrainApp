import pyttsx3
import speech_recognition as sr
import objc
from Foundation import (
    NSObject,
    NSBundle,
    NSDate,
    NSProcessInfo,
    NSNotificationCenter,
    NSUserNotification,
    NSUserNotificationCenter,
)
from AppKit import (
    NSSpeechSynthesizer,
    NSWorkspace,
    NSApplication,
    NSApp,
    NSWorkspace,
    NSWorkspaceDidWakeNotification,
    NSWorkspaceDidSleepNotification,
    NSWorkspaceWillSleepNotification,
    NSWorkspaceWillPowerOffNotification,
)
import sys
import logging
import psutil
import platform
import time
from datetime import datetime
import json
from pathlib import Path
import os
import requests
import subprocess
import webbrowser
import threading
import queue
import re
from typing import Dict, List, Optional, Union
import socket
import netifaces
import GPUtil
import cpuinfo
import distro
import iwlib
import speedtest
import uptime
import shutil
import uuid
import hashlib
from collections import deque
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/secondbrain_voice.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG_FILE = Path("/tmp/secondbrain_voice_config.json")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Command history for better context
COMMAND_HISTORY = deque(maxlen=10)


class CommandPatterns:
    """Enhanced command patterns for voice recognition."""
    
    def __init__(self):
        self.patterns = {
            "market": {
                "open": [
                    r"open njax market",
                    r"launch njax market",
                    r"start njax market",
                    r"show njax market",
                    r"display njax market",
                    r"access njax market",
                    r"go to njax market",
                    r"enter njax market"
                ],
                "search": [
                    r"search (?:for )?(\w+) in njax",
                    r"find (\w+) in njax",
                    r"look for (\w+) in njax market",
                    r"search njax for (\w+)",
                    r"find (\w+) in the market",
                    r"look up (\w+) in njax",
                    r"search market for (\w+)",
                    r"find (\w+) in njax store"
                ],
                "browse": [
                    r"browse njax market",
                    r"show njax categories",
                    r"list njax items",
                    r"show market categories",
                    r"what categories are available",
                    r"list available categories",
                    r"show all categories",
                    r"display market categories",
                    r"what's in the market",
                    r"show market inventory"
                ],
                "purchase": [
                    r"buy (\w+) from njax",
                    r"purchase (\w+) from market",
                    r"get (\w+) from njax",
                    r"order (\w+) from market",
                    r"add (\w+) to cart",
                    r"put (\w+) in cart",
                    r"buy (\w+) in njax",
                    r"purchase (\w+) in market"
                ],
                "cart": [
                    r"show cart",
                    r"view cart",
                    r"display cart",
                    r"what's in my cart",
                    r"show my cart",
                    r"check cart",
                    r"review cart",
                    r"cart summary"
                ]
            },
            "journal": {
                "start": [
                    r"start journal",
                    r"open journal",
                    r"begin journal",
                    r"create journal entry",
                    r"new journal entry",
                    r"start writing",
                    r"begin writing",
                    r"create new entry",
                    r"start new entry",
                    r"open new journal"
                ],
                "read": [
                    r"read journal",
                    r"show journal entries",
                    r"display journal",
                    r"list journal entries",
                    r"show my entries",
                    r"read my journal",
                    r"view journal",
                    r"check journal",
                    r"show entries",
                    r"list entries"
                ],
                "search": [
                    r"search journal for (\w+)",
                    r"find (\w+) in journal",
                    r"look for (\w+) in journal",
                    r"search entries for (\w+)",
                    r"find entry about (\w+)",
                    r"search for (\w+) in entries",
                    r"look up (\w+) in journal",
                    r"find journal entries about (\w+)",
                    r"search my journal for (\w+)",
                    r"find (\w+) in my entries"
                ],
                "edit": [
                    r"edit journal entry (\w+)",
                    r"modify entry (\w+)",
                    r"update journal entry (\w+)",
                    r"change entry (\w+)",
                    r"edit entry (\w+)",
                    r"modify journal entry (\w+)",
                    r"update entry (\w+)",
                    r"change journal entry (\w+)",
                    r"edit my entry (\w+)",
                    r"modify my entry (\w+)"
                ],
                "tag": [
                    r"add tag (\w+) to entry (\w+)",
                    r"tag entry (\w+) with (\w+)",
                    r"add (\w+) tag to (\w+)",
                    r"mark entry (\w+) with (\w+)",
                    r"label entry (\w+) as (\w+)",
                    r"categorize entry (\w+) as (\w+)",
                    r"add category (\w+) to (\w+)",
                    r"tag (\w+) with (\w+)"
                ]
            },
            "system": {
                "status": [
                    r"system status",
                    r"show status",
                    r"check status",
                    r"what's the status",
                    r"how's the system",
                    r"system health check",
                    r"check system status",
                    r"show system status",
                    r"display system status",
                    r"what's the system status"
                ],
                "health": [
                    r"system health",
                    r"check health",
                    r"show health",
                    r"what's the health",
                    r"system diagnostics",
                    r"run diagnostics",
                    r"check system health",
                    r"show system health",
                    r"display system health",
                    r"what's the system health"
                ],
                "sync": [
                    r"sync system",
                    r"synchronize",
                    r"sync all",
                    r"sync everything",
                    r"update system",
                    r"refresh system",
                    r"synchronize system",
                    r"sync data",
                    r"update all",
                    r"refresh all"
                ],
                "optimize": [
                    r"optimize system",
                    r"clean up system",
                    r"system maintenance",
                    r"run maintenance",
                    r"system cleanup",
                    r"optimize performance",
                    r"clean system",
                    r"maintain system",
                    r"system optimization",
                    r"run optimization"
                ],
                "backup": [
                    r"backup system",
                    r"create backup",
                    r"system backup",
                    r"backup data",
                    r"create system backup",
                    r"backup everything",
                    r"save backup",
                    r"create data backup",
                    r"backup all",
                    r"save system backup"
                ]
            },
            "task": {
                "create": [
                    r"create task (\w+)",
                    r"add task (\w+)",
                    r"new task (\w+)",
                    r"make task (\w+)",
                    r"set task (\w+)",
                    r"add new task (\w+)",
                    r"create new task (\w+)",
                    r"make new task (\w+)",
                    r"set new task (\w+)",
                    r"add to tasks (\w+)"
                ],
                "list": [
                    r"list tasks",
                    r"show tasks",
                    r"display tasks",
                    r"what are my tasks",
                    r"show my tasks",
                    r"list my tasks",
                    r"display my tasks",
                    r"what tasks do i have",
                    r"show all tasks",
                    r"list all tasks"
                ],
                "complete": [
                    r"complete task (\w+)",
                    r"finish task (\w+)",
                    r"mark task (\w+) as done",
                    r"task (\w+) is done",
                    r"finish (\w+) task",
                    r"complete (\w+) task",
                    r"mark (\w+) as complete",
                    r"done with task (\w+)",
                    r"finish (\w+)",
                    r"complete (\w+)"
                ],
                "priority": [
                    r"set priority for task (\w+) to (\w+)",
                    r"change priority of task (\w+) to (\w+)",
                    r"update priority for (\w+) to (\w+)",
                    r"set task (\w+) priority to (\w+)",
                    r"change task (\w+) priority to (\w+)",
                    r"update task (\w+) priority to (\w+)",
                    r"set (\w+) priority to (\w+)",
                    r"change (\w+) priority to (\w+)",
                    r"update (\w+) priority to (\w+)",
                    r"make task (\w+) (\w+) priority"
                ],
                "delete": [
                    r"delete task (\w+)",
                    r"remove task (\w+)",
                    r"cancel task (\w+)",
                    r"drop task (\w+)",
                    r"remove (\w+) task",
                    r"delete (\w+) task",
                    r"cancel (\w+) task",
                    r"drop (\w+) task",
                    r"remove (\w+)",
                    r"delete (\w+)"
                ]
            }
        }
        
    def match_command(self, text: str) -> Dict[str, Any]:
        """Match voice command against patterns."""
        text = text.lower().strip()
        
        for category, commands in self.patterns.items():
            for command, patterns in commands.items():
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        return {
                            "category": category,
                            "command": command,
                            "args": match.groups() if match.groups() else None,
                            "full_match": match.group(0)
                        }
        return None


class SystemHealth:
    def __init__(self):
        self.metrics = {}
        self.dashboard_file = Path("/tmp/secondbrain_health.json")
        self.update_interval = 300  # 5 minutes
        self.last_update = 0
        self.thresholds = {
            "cpu_warning": 80,
            "cpu_critical": 90,
            "memory_warning": 85,
            "memory_critical": 95,
            "disk_warning": 85,
            "disk_critical": 95,
            "battery_warning": 20,
            "battery_critical": 10,
            "temperature_warning": 80,
            "temperature_critical": 90,
            "network_warning": 50,  # Mbps
            "network_critical": 10,  # Mbps
            "process_warning": 100,  # Number of processes
            "process_critical": 150,  # Number of processes
            "load_warning": 2.0,  # System load average
            "load_critical": 3.0,  # System load average
        }
        self.initialize_metrics()
        self.metric_history = {
            "cpu": deque(maxlen=1440),  # 24 hours of history at 1-minute intervals
            "memory": deque(maxlen=1440),
            "disk": deque(maxlen=1440),
            "network": deque(maxlen=1440),
            "temperature": deque(maxlen=1440),
            "processes": deque(maxlen=1440),
            "load": deque(maxlen=1440),
        }
        self.performance_models = {
            "cpu": RandomForestRegressor(n_estimators=200),
            "memory": RandomForestRegressor(n_estimators=200),
            "disk": RandomForestRegressor(n_estimators=200),
            "network": RandomForestRegressor(n_estimators=200),
            "processes": RandomForestRegressor(n_estimators=200),
            "load": RandomForestRegressor(n_estimators=200),
        }
        self.scalers = {
            "cpu": StandardScaler(),
            "memory": StandardScaler(),
            "disk": StandardScaler(),
            "network": StandardScaler(),
            "processes": StandardScaler(),
            "load": StandardScaler(),
        }
        self.anomaly_detectors = {
            "cpu": self._create_anomaly_detector(),
            "memory": self._create_anomaly_detector(),
            "disk": self._create_anomaly_detector(),
            "network": self._create_anomaly_detector(),
            "processes": self._create_anomaly_detector(),
            "load": self._create_anomaly_detector(),
        }
        self.initialize_performance_models()
        self.setup_continuous_monitoring()

    def setup_continuous_monitoring(self):
        """Setup continuous monitoring with enhanced metrics collection."""
        try:
            self.monitoring_thread = threading.Thread(
                target=self._continuous_monitoring, daemon=True
            )
            self.monitoring_thread.start()
        except Exception as e:
            logger.error(f"Error setting up continuous monitoring: {e}")

    def _continuous_monitoring(self):
        """Continuous monitoring with enhanced metrics collection."""
        while True:
            try:
                self.collect_metrics()
                self._check_resource_usage()
                self._check_system_health()
                self._update_performance_models()
                time.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(60)

    def _check_resource_usage(self):
        """Check resource usage with enhanced thresholds."""
        try:
            metrics = self.metrics
            alerts = []

            # CPU checks
            if metrics["cpu"]["percent"] > self.thresholds["cpu_critical"]:
                alerts.append(f"Critical CPU usage: {metrics['cpu']['percent']}%")
            elif metrics["cpu"]["percent"] > self.thresholds["cpu_warning"]:
                alerts.append(f"High CPU usage: {metrics['cpu']['percent']}%")

            # Memory checks
            if metrics["memory"]["percent"] > self.thresholds["memory_critical"]:
                alerts.append(f"Critical memory usage: {metrics['memory']['percent']}%")
            elif metrics["memory"]["percent"] > self.thresholds["memory_warning"]:
                alerts.append(f"High memory usage: {metrics['memory']['percent']}%")

            # Process checks
            process_count = len(psutil.process_iter())
            if process_count > self.thresholds["process_critical"]:
                alerts.append(f"Critical process count: {process_count}")
            elif process_count > self.thresholds["process_warning"]:
                alerts.append(f"High process count: {process_count}")

            # System load checks
            load_avg = os.getloadavg()[0]
            if load_avg > self.thresholds["load_critical"]:
                alerts.append(f"Critical system load: {load_avg}")
            elif load_avg > self.thresholds["load_warning"]:
                alerts.append(f"High system load: {load_avg}")

            return alerts
        except Exception as e:
            logger.error(f"Error checking resource usage: {e}")
            return []

    def _check_system_health(self):
        """Check overall system health with enhanced diagnostics."""
        try:
            health_status = {"status": "healthy", "issues": [], "recommendations": []}

            # Check CPU health
            cpu_temp = self._get_cpu_temperature()
            if cpu_temp and any(
                temp > self.thresholds["temperature_critical"]
                for temp in cpu_temp.values()
            ):
                health_status["status"] = "critical"
                health_status["issues"].append("Critical CPU temperature")
                health_status["recommendations"].append(
                    "Check cooling system and reduce CPU load"
                )

            # Check memory health
            if self.metrics["memory"]["percent"] > self.thresholds["memory_critical"]:
                health_status["status"] = "critical"
                health_status["issues"].append("Critical memory usage")
                health_status["recommendations"].append(
                    "Close unnecessary applications and check for memory leaks"
                )

            # Check disk health
            if self.metrics["disk"]["percent"] > self.thresholds["disk_critical"]:
                health_status["status"] = "critical"
                health_status["issues"].append("Critical disk usage")
                health_status["recommendations"].append(
                    "Free up disk space and check for large files"
                )

            # Check network health
            if (
                self.metrics["network"]["speed"]
                and self.metrics["network"]["speed"]
                < self.thresholds["network_critical"]
            ):
                health_status["status"] = "warning"
                health_status["issues"].append("Low network speed")
                health_status["recommendations"].append(
                    "Check network connection and router status"
                )

            return health_status
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {
                "status": "unknown",
                "issues": ["Error checking system health"],
                "recommendations": [],
            }

    def _update_performance_models(self):
        """Update performance prediction models with enhanced accuracy."""
        try:
            for metric in self.performance_models:
                if len(self.metric_history[metric]) > 10:
                    X = np.array(range(len(self.metric_history[metric]))).reshape(-1, 1)
                    y = np.array(list(self.metric_history[metric]))

                    # Scale the data
                    X_scaled = self.scalers[metric].fit_transform(X)

                    # Update the model
                    self.performance_models[metric].fit(X_scaled, y)

                    # Update anomaly detector
                    self.anomaly_detectors[metric]["mean"] = np.mean(y)
                    self.anomaly_detectors[metric]["std"] = np.std(y)
        except Exception as e:
            logger.error(f"Error updating performance models: {e}")

    def collect_metrics(self):
        """Collect comprehensive system metrics with enhanced monitoring."""
        try:
            # CPU metrics with enhanced monitoring
            self.metrics["cpu"] = {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "load_avg": psutil.getloadavg(),
                "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
                "temperature": self._get_cpu_temperature(),
                "info": cpuinfo.get_cpu_info(),
                "frequency_stats": self._get_cpu_frequency_stats(),
                "power_usage": self._get_cpu_power_usage(),
            }
            self.metric_history["cpu"].append(self.metrics["cpu"]["percent"])

            # Memory metrics with enhanced monitoring
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            self.metrics["memory"] = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_free": swap.free,
                "swap_percent": swap.percent,
                "pressure": self._get_memory_pressure(),
                "page_faults": self._get_page_faults(),
                "memory_stats": self._get_memory_stats(),
            }
            self.metric_history["memory"].append(self.metrics["memory"]["percent"])

            # Enhanced process monitoring
            processes = list(
                psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"])
            )
            self.metrics["processes"] = {
                "count": len(processes),
                "top_cpu": sorted(
                    processes, key=lambda p: p.info["cpu_percent"], reverse=True
                )[:5],
                "top_memory": sorted(
                    processes, key=lambda p: p.info["memory_percent"], reverse=True
                )[:5],
                "zombie_count": len(
                    [p for p in processes if p.status() == psutil.STATUS_ZOMBIE]
                ),
                "thread_count": sum(p.num_threads() for p in processes),
            }
            self.metric_history["processes"].append(self.metrics["processes"]["count"])

            # System load monitoring
            load_avg = os.getloadavg()
            self.metrics["load"] = {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2],
                "cpu_count": os.cpu_count(),
                "load_per_cpu": [avg / os.cpu_count() for avg in load_avg],
            }
            self.metric_history["load"].append(self.metrics["load"]["1min"])

            # Update timestamp and save
            self.metrics["timestamp"] = datetime.now().isoformat()
            self.last_update = time.time()
            self.save_dashboard()

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def _get_cpu_frequency_stats(self):
        """Get CPU frequency statistics."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            return None
        except:
            return None

    def _get_cpu_power_usage(self):
        """Get CPU power usage statistics."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["pmset", "-g", "stats"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    return result.stdout
            return None
        except:
            return None

    def _get_page_faults(self):
        """Get page fault statistics."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(["vm_stat"], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout
            return None
        except:
            return None

    def _get_memory_stats(self):
        """Get detailed memory statistics."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["top", "-l", "1", "-stats", "mem"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    return result.stdout
            return None
        except:
            return None

    def _create_anomaly_detector(self):
        """Create an anomaly detector using statistical methods."""
        return {
            "mean": 0,
            "std": 0,
            "threshold": 2.0,  # Number of standard deviations for anomaly detection
        }

    def detect_anomalies(self, metric: str) -> List[Dict]:
        """Detect anomalies in metric data."""
        try:
            if len(self.metric_history[metric]) > 1:
                data = np.array(list(self.metric_history[metric]))
                detector = self.anomaly_detectors[metric]

                # Update detector statistics
                detector["mean"] = np.mean(data)
                detector["std"] = np.std(data)

                # Detect anomalies
                anomalies = []
                for i, value in enumerate(data):
                    z_score = abs((value - detector["mean"]) / detector["std"])
                    if z_score > detector["threshold"]:
                        anomalies.append(
                            {
                                "index": i,
                                "value": value,
                                "z_score": z_score,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                return anomalies
            return []
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    def predict_performance(self, metric: str, steps: int = 5) -> Dict:
        """Enhanced performance prediction with confidence intervals."""
        try:
            if (
                metric in self.performance_models
                and len(self.metric_history[metric]) > 1
            ):
                data = np.array(list(self.metric_history[metric]))
                X = np.array(range(len(data))).reshape(-1, 1)
                X_pred = np.array(range(len(data), len(data) + steps)).reshape(-1, 1)

                # Scale the data
                X_scaled = self.scalers[metric].fit_transform(X)
                X_pred_scaled = self.scalers[metric].transform(X_pred)

                # Make predictions
                predictions = self.performance_models[metric].predict(X_pred_scaled)

                # Calculate confidence intervals
                predictions_all = []
                for estimator in self.performance_models[metric].estimators_:
                    predictions_all.append(estimator.predict(X_pred_scaled))

                predictions_all = np.array(predictions_all)
                mean_pred = np.mean(predictions_all, axis=0)
                std_pred = np.std(predictions_all, axis=0)

                return {
                    "predictions": mean_pred.tolist(),
                    "confidence_intervals": {
                        "lower": (mean_pred - 1.96 * std_pred).tolist(),
                        "upper": (mean_pred + 1.96 * std_pred).tolist(),
                    },
                }
            return {
                "predictions": [],
                "confidence_intervals": {"lower": [], "upper": []},
            }
        except Exception as e:
            logger.error(f"Error predicting performance: {e}")
            return {
                "predictions": [],
                "confidence_intervals": {"lower": [], "upper": []},
            }

    def analyze_performance(self) -> Dict:
        """Enhanced performance analysis with anomaly detection."""
        try:
            analysis = {}
            for metric in self.metric_history:
                if len(self.metric_history[metric]) > 1:
                    data = np.array(list(self.metric_history[metric]))
                    anomalies = self.detect_anomalies(metric)
                    predictions = self.predict_performance(metric)

                    analysis[metric] = {
                        "mean": np.mean(data),
                        "std": np.std(data),
                        "min": np.min(data),
                        "max": np.max(data),
                        "trend": np.polyfit(range(len(data)), data, 1)[0],
                        "anomalies": anomalies,
                        "predictions": predictions["predictions"],
                        "confidence_intervals": predictions["confidence_intervals"],
                        "seasonality": self._detect_seasonality(data),
                        "volatility": self._calculate_volatility(data),
                    }
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {}

    def _detect_seasonality(self, data: np.ndarray) -> Dict:
        """Detect seasonality in time series data."""
        try:
            if len(data) > 24:  # Need enough data points
                # Calculate autocorrelation
                acf = np.correlate(data, data, mode="full")
                acf = acf[len(acf) // 2 :]

                # Find peaks in autocorrelation
                peaks = []
                for i in range(1, len(acf) - 1):
                    if acf[i] > acf[i - 1] and acf[i] > acf[i + 1]:
                        peaks.append(i)

                if peaks:
                    return {
                        "has_seasonality": True,
                        "period": peaks[0],
                        "strength": acf[peaks[0]],
                    }
            return {"has_seasonality": False}
        except Exception as e:
            logger.error(f"Error detecting seasonality: {e}")
            return {"has_seasonality": False}

    def _calculate_volatility(self, data: np.ndarray) -> float:
        """Calculate volatility of time series data."""
        try:
            returns = np.diff(data) / data[:-1]
            return np.std(returns)
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0

    def generate_performance_report(self) -> str:
        """Generate an enhanced performance report with anomaly detection."""
        try:
            analysis = self.analyze_performance()
            report = []

            for metric, stats in analysis.items():
                trend = "increasing" if stats["trend"] > 0 else "decreasing"
                report.append(f"{metric.upper()} Performance:")
                report.append(f"- Current: {stats['mean']:.1f}%")
                report.append(f"- Range: {stats['min']:.1f}% to {stats['max']:.1f}%")
                report.append(f"- Trend: {trend}")
                report.append(f"- Volatility: {stats['volatility']:.2f}")

                if stats["seasonality"]["has_seasonality"]:
                    report.append(
                        f"- Seasonality: Detected (period: {stats['seasonality']['period']} minutes)"
                    )

                if stats["anomalies"]:
                    report.append("- Anomalies detected:")
                    for anomaly in stats["anomalies"][-3:]:  # Show last 3 anomalies
                        report.append(
                            f"  * {anomaly['value']:.1f}% (z-score: {anomaly['z_score']:.1f})"
                        )

                if stats["predictions"]:
                    report.append("- Predictions:")
                    for i, pred in enumerate(stats["predictions"]):
                        lower = stats["confidence_intervals"]["lower"][i]
                        upper = stats["confidence_intervals"]["upper"][i]
                        report.append(
                            f"  * {i+1} min: {pred:.1f}% (95% CI: {lower:.1f}% - {upper:.1f}%)"
                        )

                report.append("")

            return "\n".join(report)
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return "Error generating performance report"

    def plot_performance(self, metric: str) -> str:
        """Generate an enhanced performance plot with confidence intervals."""
        try:
            if len(self.metric_history[metric]) > 1:
                plt.figure(figsize=(12, 8))
                data = list(self.metric_history[metric])

                # Plot actual data
                plt.plot(data, label="Actual", color="blue")

                # Plot predictions with confidence intervals
                predictions = self.predict_performance(metric)
                if predictions["predictions"]:
                    x_pred = range(
                        len(data), len(data) + len(predictions["predictions"])
                    )
                    plt.plot(
                        x_pred,
                        predictions["predictions"],
                        "--",
                        label="Predicted",
                        color="red",
                    )
                    plt.fill_between(
                        x_pred,
                        predictions["confidence_intervals"]["lower"],
                        predictions["confidence_intervals"]["upper"],
                        color="red",
                        alpha=0.2,
                        label="95% Confidence Interval",
                    )

                # Plot anomalies
                anomalies = self.detect_anomalies(metric)
                if anomalies:
                    anomaly_indices = [a["index"] for a in anomalies]
                    anomaly_values = [a["value"] for a in anomalies]
                    plt.scatter(
                        anomaly_indices, anomaly_values, color="red", label="Anomalies"
                    )

                plt.title(f"{metric.upper()} Performance Analysis")
                plt.xlabel("Time (minutes)")
                plt.ylabel("Usage (%)")
                plt.legend()
                plt.grid(True)

                filename = f"/tmp/{metric}_performance.png"
                plt.savefig(filename)
                plt.close()
                return filename
            return None
        except Exception as e:
            logger.error(f"Error plotting performance: {e}")
            return None

    def initialize_metrics(self):
        """Initialize system metrics with default values."""
        self.metrics = {
            "cpu": {},
            "memory": {},
            "disk": {},
            "network": {},
            "battery": None,
            "temperature": {},
            "processes": {},
            "system": {},
            "gpu": {},
            "timestamp": None,
            "uptime": None,
            "network_speed": None,
            "disk_health": None,
            "system_load": None,
            "performance": {},
        }

    def _get_cpu_temperature(self):
        """Get CPU temperature if available."""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                return {k: v[0].current for k, v in temps.items()}
            return None
        except:
            return None

    def _get_memory_pressure(self):
        """Get memory pressure on macOS."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(["vm_stat"], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout
            return None
        except:
            return None

    def _get_disk_health(self):
        """Get disk health information."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["diskutil", "info", "/"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    return result.stdout
            return None
        except:
            return None

    def _get_network_interfaces(self):
        """Get detailed network interface information."""
        try:
            interfaces = netifaces.interfaces()
            return {
                iface: {
                    "addresses": netifaces.ifaddresses(iface),
                    "status": (
                        "up"
                        if netifaces.AF_INET in netifaces.ifaddresses(iface)
                        else "down"
                    ),
                }
                for iface in interfaces
            }
        except:
            return {}

    def _get_network_speed(self):
        """Get network speed information."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["networksetup", "-getinfo", "Wi-Fi"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout
            return None
        except:
            return None

    def _get_wifi_info(self):
        """Get WiFi information."""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    [
                        "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                        "-I",
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout
            return None
        except:
            return None

    def _get_uptime(self):
        """Get system uptime."""
        try:
            return uptime.uptime()
        except:
            return None

    def _get_system_load(self):
        """Get system load average."""
        try:
            return os.getloadavg()
        except:
            return None

    def _get_distribution_info(self):
        """Get distribution information."""
        try:
            if platform.system() == "Linux":
                return distro.info()
            return None
        except:
            return None

    def _get_ip_address(self):
        """Get system IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def run_network_diagnostics(self):
        """Run comprehensive network diagnostics."""
        try:
            results = {
                "ping": self._run_ping_test(),
                "dns": self._run_dns_test(),
                "speed": self._run_speed_test(),
                "traceroute": self._run_traceroute(),
                "ports": self._check_common_ports(),
            }
            return results
        except Exception as e:
            logger.error(f"Error running network diagnostics: {e}")
            return None

    def _run_ping_test(self):
        """Run ping test to common servers."""
        try:
            servers = ["8.8.8.8", "1.1.1.1", "www.google.com"]
            results = {}
            for server in servers:
                result = subprocess.run(
                    ["ping", "-c", "4", server], capture_output=True, text=True
                )
                results[server] = result.stdout
            return results
        except:
            return None

    def _run_dns_test(self):
        """Run DNS resolution test."""
        try:
            domains = ["google.com", "cloudflare.com", "amazon.com"]
            results = {}
            for domain in domains:
                result = subprocess.run(["dig", domain], capture_output=True, text=True)
                results[domain] = result.stdout
            return results
        except:
            return None

    def _run_speed_test(self):
        """Run internet speed test."""
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download = st.download()
            upload = st.upload()
            return {"download": download, "upload": upload, "server": st.best}
        except:
            return None

    def _run_traceroute(self):
        """Run traceroute to common servers."""
        try:
            servers = ["8.8.8.8", "1.1.1.1", "www.google.com"]
            results = {}
            for server in servers:
                result = subprocess.run(
                    ["traceroute", server], capture_output=True, text=True
                )
                results[server] = result.stdout
            return results
        except:
            return None

    def _check_common_ports(self):
        """Check common network ports."""
        try:
            ports = [80, 443, 22, 53]
            results = {}
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("127.0.0.1", port))
                results[port] = "open" if result == 0 else "closed"
                sock.close()
            return results
        except:
            return None

    def initialize_performance_models(self):
        """Initialize performance prediction models."""
        try:
            for metric in self.performance_models:
                if len(self.metric_history[metric]) > 1:
                    X = np.array(range(len(self.metric_history[metric]))).reshape(-1, 1)
                    y = np.array(list(self.metric_history[metric]))
                    self.performance_models[metric].fit(X, y)
        except Exception as e:
            logger.error(f"Error initializing performance models: {e}")

    def save_dashboard(self):
        """Save system metrics to dashboard file."""
        try:
            with open(self.dashboard_file, "w") as f:
                json.dump(self.metrics, f)
        except Exception as e:
            logger.error(f"Error saving dashboard: {e}")


class MacOSVoiceEngine:
    def __init__(self):
        self.engine = None
        self.voice = None
        self.rate = 175
        self.volume = 1.0
        self.pitch = 1.0
        self.initialize_engine()
        self.feedback_queue = queue.Queue()
        self.feedback_thread = None
        self.is_speaking = False
        self.voice_settings = {
            "default": {"rate": 175, "volume": 1.0, "pitch": 1.0},
            "alert": {"rate": 200, "volume": 1.2, "pitch": 1.2},
            "whisper": {"rate": 150, "volume": 0.8, "pitch": 0.9},
            "command": {"rate": 190, "volume": 1.1, "pitch": 1.1},
        }
        self.initialize_feedback_thread()
        self.health = SystemHealth()
        self.setup_notifications()
        self.setup_system_monitoring()
        self.last_notification_time = {}
        self.notification_cooldown = 300  # 5 minutes

    def initialize_engine(self):
        """Initialize the voice engine with enhanced settings."""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty("voices")

            # Find the best available voice
            preferred_voices = [
                "com.apple.speech.synthesis.voice.karen",  # Australian
                "com.apple.speech.synthesis.voice.daniel",  # British
                "com.apple.speech.synthesis.voice.alex",  # American
                "com.apple.speech.synthesis.voice.samantha",
            ]  # American

            for voice_id in preferred_voices:
                for voice in voices:
                    if voice.id == voice_id:
                        self.voice = voice
                        self.engine.setProperty("voice", voice.id)
                        break
                if self.voice:
                    break

            if not self.voice and voices:
                self.voice = voices[0]
                self.engine.setProperty("voice", self.voice.id)

            # Set default properties
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)

            # Initialize event callbacks
            self.engine.connect("started-utterance", self._on_start_speaking)
            self.engine.connect("finished-utterance", self._on_finish_speaking)
            self.engine.connect("error", self._on_error)

        except Exception as e:
            logger.error(f"Error initializing voice engine: {e}")
            self.engine = None

    def initialize_feedback_thread(self):
        """Initialize the feedback processing thread."""
        try:
            self.feedback_thread = threading.Thread(
                target=self._process_feedback_queue, daemon=True
            )
            self.feedback_thread.start()
        except Exception as e:
            logger.error(f"Error initializing feedback thread: {e}")

    def _process_feedback_queue(self):
        """Process the feedback queue with enhanced error handling."""
        while True:
            try:
                feedback = self.feedback_queue.get()
                if feedback is None:
                    break

                message, feedback_type = feedback
                self._speak_with_settings(message, feedback_type)
                self.feedback_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing feedback: {e}")
                time.sleep(0.1)

    def _speak_with_settings(self, text, feedback_type="default"):
        """Speak with specific voice settings."""
        try:
            if not self.engine:
                return

            settings = self.voice_settings.get(
                feedback_type, self.voice_settings["default"]
            )

            # Apply settings
            self.engine.setProperty("rate", settings["rate"])
            self.engine.setProperty("volume", settings["volume"])

            # Speak the text
            self.engine.say(text)
            self.engine.runAndWait()

        except Exception as e:
            logger.error(f"Error speaking with settings: {e}")

    def _on_start_speaking(self):
        """Handle speech start event."""
        self.is_speaking = True

    def _on_finish_speaking(self):
        """Handle speech finish event."""
        self.is_speaking = False

    def _on_error(self, error):
        """Handle speech engine errors."""
        logger.error(f"Speech engine error: {error}")
        self.is_speaking = False

    def speak(self, text, feedback_type="default"):
        """Speak text with enhanced feedback handling."""
        try:
            if not text:
                return

            # Add to feedback queue
            self.feedback_queue.put((text, feedback_type))

        except Exception as e:
            logger.error(f"Error in speak: {e}")

    def speak_alert(self, text):
        """Speak alert message with enhanced urgency."""
        self.speak(text, "alert")

    def speak_command(self, text):
        """Speak command confirmation with enhanced clarity."""
        self.speak(text, "command")

    def speak_whisper(self, text):
        """Speak in a softer, more subtle tone."""
        self.speak(text, "whisper")

    def stop_speaking(self):
        """Stop current speech with enhanced cleanup."""
        try:
            if self.engine and self.is_speaking:
                self.engine.stop()
                self.is_speaking = False
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")

    def cleanup(self):
        """Clean up voice engine resources."""
        try:
            self.stop_speaking()
            if self.feedback_queue:
                self.feedback_queue.put(None)  # Signal thread to stop
            if self.feedback_thread:
                self.feedback_thread.join(timeout=1.0)
            if self.engine:
                self.engine = None
        except Exception as e:
            logger.error(f"Error cleaning up voice engine: {e}")

    def setup_notifications(self):
        """Setup system notifications with enhanced features."""
        try:
            if platform.system() == "Darwin":
                center = NSNotificationCenter.defaultCenter()

                # System state notifications
                center.addObserver_selector_name_object_(
                    self, "systemDidWake:", NSWorkspaceDidWakeNotification, None
                )
                center.addObserver_selector_name_object_(
                    self, "systemWillSleep:", NSWorkspaceWillSleepNotification, None
                )
                center.addObserver_selector_name_object_(
                    self,
                    "systemWillPowerOff:",
                    NSWorkspaceWillPowerOffNotification,
                    None,
                )

                # Setup user notifications
                self.notification_center = (
                    NSUserNotificationCenter.defaultUserNotificationCenter()
                )
                self.notification_center.setDelegate_(self)
        except Exception as e:
            logger.error(f"Error setting up notifications: {e}")

    def setup_system_monitoring(self):
        """Setup enhanced system monitoring."""
        try:
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitor_system, daemon=True
            )
            self.monitoring_thread.start()
        except Exception as e:
            logger.error(f"Error setting up system monitoring: {e}")

    def _monitor_system(self):
        """Monitor system metrics and trigger notifications."""
        while True:
            try:
                metrics = self.health.collect_metrics()

                # Check for anomalies
                for metric in ["cpu", "memory", "disk", "network"]:
                    anomalies = self.health.detect_anomalies(metric)
                    if anomalies:
                        self._handle_anomaly(metric, anomalies[-1])

                # Check thresholds
                self._check_thresholds(metrics)

                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(60)

    def _handle_anomaly(self, metric: str, anomaly: Dict):
        """Handle detected anomalies."""
        try:
            current_time = time.time()
            if (
                metric not in self.last_notification_time
                or current_time - self.last_notification_time[metric]
                > self.notification_cooldown
            ):

                message = f"Anomaly detected in {metric.upper()}: {anomaly['value']:.1f}% (z-score: {anomaly['z_score']:.1f})"
                self.speak(message, priority=True)
                self._send_notification("System Anomaly", message)
                self.last_notification_time[metric] = current_time
        except Exception as e:
            logger.error(f"Error handling anomaly: {e}")

    def _check_thresholds(self, metrics: Dict):
        """Check system metrics against thresholds."""
        try:
            thresholds = self.health.thresholds

            # CPU threshold check
            if metrics["cpu"]["percent"] > thresholds["cpu_critical"]:
                self._send_threshold_alert("CPU", "critical", metrics["cpu"]["percent"])
            elif metrics["cpu"]["percent"] > thresholds["cpu_warning"]:
                self._send_threshold_alert("CPU", "warning", metrics["cpu"]["percent"])

            # Memory threshold check
            if metrics["memory"]["percent"] > thresholds["memory_critical"]:
                self._send_threshold_alert(
                    "Memory", "critical", metrics["memory"]["percent"]
                )
            elif metrics["memory"]["percent"] > thresholds["memory_warning"]:
                self._send_threshold_alert(
                    "Memory", "warning", metrics["memory"]["percent"]
                )

            # Disk threshold check
            if metrics["disk"]["percent"] > thresholds["disk_critical"]:
                self._send_threshold_alert(
                    "Disk", "critical", metrics["disk"]["percent"]
                )
            elif metrics["disk"]["percent"] > thresholds["disk_warning"]:
                self._send_threshold_alert(
                    "Disk", "warning", metrics["disk"]["percent"]
                )
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")

    def _send_threshold_alert(self, metric: str, level: str, value: float):
        """Send threshold alert notification."""
        try:
            current_time = time.time()
            if (
                f"{metric}_{level}" not in self.last_notification_time
                or current_time - self.last_notification_time[f"{metric}_{level}"]
                > self.notification_cooldown
            ):

                message = f"{metric} usage is {level}: {value:.1f}%"
                self.speak(message, priority=True)
                self._send_notification(f"{metric} {level.title()} Alert", message)
                self.last_notification_time[f"{metric}_{level}"] = current_time
        except Exception as e:
            logger.error(f"Error sending threshold alert: {e}")

    def _send_notification(self, title: str, message: str):
        """Send a system notification."""
        try:
            if platform.system() == "Darwin":
                notification = NSUserNotification.alloc().init()
                notification.setTitle_(title)
                notification.setInformativeText_(message)
                notification.setSoundName_("NSUserNotificationDefaultSoundName")
                self.notification_center.deliverNotification_(notification)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def systemDidWake_(self, notification):
        """Handle system wake notification with enhanced features."""
        try:
            self.speak("System has woken up from sleep", priority=True)
            self.health.collect_metrics()

            # Check system state after wake
            metrics = self.health.metrics
            if metrics["cpu"]["percent"] > 50:
                self.speak("High CPU usage detected after wake", priority=True)
            if metrics["memory"]["percent"] > 80:
                self.speak("High memory usage detected after wake", priority=True)
        except Exception as e:
            logger.error(f"Error handling wake notification: {e}")

    def systemWillSleep_(self, notification):
        """Handle system sleep notification with enhanced features."""
        try:
            # Save current state
            self.health.save_dashboard()

            # Check for active processes
            active_processes = len(psutil.process_iter())
            if active_processes > 50:
                self.speak(
                    f"Warning: {active_processes} processes are still active",
                    priority=True,
                )

            self.speak("System is going to sleep", priority=True)
        except Exception as e:
            logger.error(f"Error handling sleep notification: {e}")

    def systemWillPowerOff_(self, notification):
        """Handle system power off notification with enhanced features."""
        try:
            # Save current state
            self.health.save_dashboard()

            # Check for unsaved work
            if self.health.metrics["disk"]["write_count"] > 0:
                self.speak("Warning: Recent disk writes detected", priority=True)

            self.speak("System is shutting down", priority=True)
        except Exception as e:
            logger.error(f"Error handling power off notification: {e}")


class MacOSSystemFeatures:
    def __init__(self):
        self.workspace = None
        self.app_controller = None
        self.initialize_features()

    def initialize_features(self):
        """Initialize macOS-specific features."""
        try:
            # Initialize workspace
            self.workspace = NSWorkspace.sharedWorkspace()

            # Initialize app controller
            self.app_controller = NSApplication.sharedApplication()

            # Setup notification center
            self.notification_center = (
                NSUserNotificationCenter.defaultUserNotificationCenter()
            )

            # Initialize system preferences
            self.system_preferences = self._get_system_preferences()

            # Initialize accessibility features
            self.accessibility = self._initialize_accessibility()

        except Exception as e:
            logger.error(f"Error initializing macOS features: {e}")

    def _get_system_preferences(self):
        """Get system preferences with enhanced access."""
        try:
            preferences = {}

            # Get display preferences
            display_prefs = self._get_display_preferences()
            preferences["display"] = display_prefs

            # Get sound preferences
            sound_prefs = self._get_sound_preferences()
            preferences["sound"] = sound_prefs

            # Get power preferences
            power_prefs = self._get_power_preferences()
            preferences["power"] = power_prefs

            # Get accessibility preferences
            accessibility_prefs = self._get_accessibility_preferences()
            preferences["accessibility"] = accessibility_prefs

            return preferences
        except Exception as e:
            logger.error(f"Error getting system preferences: {e}")
            return {}

    def _get_display_preferences(self):
        """Get display preferences with enhanced monitoring."""
        try:
            preferences = {}

            # Get screen resolution
            screen = NSScreen.mainScreen()
            if screen:
                preferences["resolution"] = {
                    "width": screen.frame().size.width,
                    "height": screen.frame().size.height,
                }

            # Get brightness
            brightness = self._get_brightness()
            preferences["brightness"] = brightness

            # Get night shift status
            night_shift = self._get_night_shift_status()
            preferences["night_shift"] = night_shift

            return preferences
        except Exception as e:
            logger.error(f"Error getting display preferences: {e}")
            return {}

    def _get_sound_preferences(self):
        """Get sound preferences with enhanced control."""
        try:
            preferences = {}

            # Get system volume
            volume = self._get_system_volume()
            preferences["volume"] = volume

            # Get sound output device
            output_device = self._get_sound_output_device()
            preferences["output_device"] = output_device

            # Get sound input device
            input_device = self._get_sound_input_device()
            preferences["input_device"] = input_device

            return preferences
        except Exception as e:
            logger.error(f"Error getting sound preferences: {e}")
            return {}

    def _get_power_preferences(self):
        """Get power preferences with enhanced monitoring."""
        try:
            preferences = {}

            # Get battery status
            battery = self._get_battery_status()
            preferences["battery"] = battery

            # Get power adapter status
            power_adapter = self._get_power_adapter_status()
            preferences["power_adapter"] = power_adapter

            # Get power mode
            power_mode = self._get_power_mode()
            preferences["power_mode"] = power_mode

            return preferences
        except Exception as e:
            logger.error(f"Error getting power preferences: {e}")
            return {}

    def _get_accessibility_preferences(self):
        """Get accessibility preferences with enhanced features."""
        try:
            preferences = {}

            # Get voice over status
            voice_over = self._get_voice_over_status()
            preferences["voice_over"] = voice_over

            # Get zoom status
            zoom = self._get_zoom_status()
            preferences["zoom"] = zoom

            # Get display accommodations
            display_accommodations = self._get_display_accommodations()
            preferences["display_accommodations"] = display_accommodations

            return preferences
        except Exception as e:
            logger.error(f"Error getting accessibility preferences: {e}")
            return {}

    def _get_brightness(self):
        """Get display brightness."""
        try:
            result = subprocess.run(["brightness"], capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return None
        except:
            return None

    def _get_night_shift_status(self):
        """Get night shift status."""
        try:
            result = subprocess.run(
                [
                    "defaults",
                    "read",
                    "com.apple.CoreBrightness",
                    "CBBlueReductionStatus",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip() == "1"
            return None
        except:
            return None

    def _get_system_volume(self):
        """Get system volume."""
        try:
            result = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
            return None
        except:
            return None

    def _get_sound_output_device(self):
        """Get current sound output device."""
        try:
            result = subprocess.run(
                ["system_profiler", "SPAudioDataType"], capture_output=True, text=True
            )
            if result.returncode == 0:
                # Parse the output to find the current output device
                output = result.stdout
                if "Current Default Output Device:" in output:
                    device = (
                        output.split("Current Default Output Device:")[1]
                        .split("\n")[0]
                        .strip()
                    )
                    return device
            return None
        except:
            return None

    def _get_sound_input_device(self):
        """Get current sound input device."""
        try:
            result = subprocess.run(
                ["system_profiler", "SPAudioDataType"], capture_output=True, text=True
            )
            if result.returncode == 0:
                # Parse the output to find the current input device
                output = result.stdout
                if "Current Default Input Device:" in output:
                    device = (
                        output.split("Current Default Input Device:")[1]
                        .split("\n")[0]
                        .strip()
                    )
                    return device
            return None
        except:
            return None

    def _get_battery_status(self):
        """Get battery status with enhanced monitoring."""
        try:
            result = subprocess.run(
                ["pmset", "-g", "batt"], capture_output=True, text=True
            )
            if result.returncode == 0:
                output = result.stdout
                status = {}

                # Parse battery percentage
                if "InternalBattery" in output:
                    battery_info = output.split("InternalBattery")[1].split("\n")[0]
                    if "%" in battery_info:
                        status["percentage"] = int(battery_info.split("%")[0].strip())

                # Parse charging status
                if "charging" in output.lower():
                    status["charging"] = True
                elif "discharging" in output.lower():
                    status["charging"] = False

                # Parse time remaining
                if "remaining" in output.lower():
                    time_str = output.split("remaining")[0].split()[-1]
                    status["time_remaining"] = time_str

                return status
            return None
        except:
            return None

    def _get_power_adapter_status(self):
        """Get power adapter status."""
        try:
            result = subprocess.run(
                ["pmset", "-g", "ac"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return "AC Power" in result.stdout
            return None
        except:
            return None

    def _get_power_mode(self):
        """Get current power mode."""
        try:
            result = subprocess.run(
                ["pmset", "-g", "custom"], capture_output=True, text=True
            )
            if result.returncode == 0:
                output = result.stdout
                if "lowpowermode" in output.lower():
                    return "low_power"
                return "normal"
            return None
        except:
            return None

    def _get_voice_over_status(self):
        """Get VoiceOver status."""
        try:
            result = subprocess.run(
                [
                    "defaults",
                    "read",
                    "com.apple.universalaccess",
                    "voiceOverOnOffState",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip() == "1"
            return None
        except:
            return None

    def _get_zoom_status(self):
        """Get zoom status."""
        try:
            result = subprocess.run(
                ["defaults", "read", "com.apple.universalaccess", "closeViewEnabled"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip() == "1"
            return None
        except:
            return None

    def _get_display_accommodations(self):
        """Get display accommodations."""
        try:
            accommodations = {}

            # Get invert colors status
            result = subprocess.run(
                [
                    "defaults",
                    "read",
                    "com.apple.universalaccess",
                    "invertColorsEnabled",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                accommodations["invert_colors"] = result.stdout.strip() == "1"

            # Get grayscale status
            result = subprocess.run(
                ["defaults", "read", "com.apple.universalaccess", "grayscaleEnabled"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                accommodations["grayscale"] = result.stdout.strip() == "1"

            # Get reduce transparency status
            result = subprocess.run(
                [
                    "defaults",
                    "read",
                    "com.apple.universalaccess",
                    "reduceTransparencyEnabled",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                accommodations["reduce_transparency"] = result.stdout.strip() == "1"

            return accommodations
        except Exception as e:
            logger.error(f"Error getting display accommodations: {e}")
            return {}

    def _initialize_accessibility(self):
        """Initialize accessibility features."""
        try:
            accessibility = {}

            # Check if accessibility is enabled
            result = subprocess.run(
                [
                    "defaults",
                    "read",
                    "com.apple.universalaccess",
                    "enableAccessibility",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                accessibility["enabled"] = result.stdout.strip() == "1"

            # Get available accessibility features
            accessibility["features"] = self._get_available_accessibility_features()

            return accessibility
        except Exception as e:
            logger.error(f"Error initializing accessibility: {e}")
            return {}

    def _get_available_accessibility_features(self):
        """Get available accessibility features."""
        try:
            features = []

            # Check for VoiceOver
            if self._get_voice_over_status():
                features.append("voice_over")

            # Check for Zoom
            if self._get_zoom_status():
                features.append("zoom")

            # Check for display accommodations
            accommodations = self._get_display_accommodations()
            for feature, enabled in accommodations.items():
                if enabled:
                    features.append(feature)

            return features
        except Exception as e:
            logger.error(f"Error getting available accessibility features: {e}")
            return []


def take_screenshot() -> str:
    """Take a screenshot on macOS with enhanced options."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"

        # Use screencapture with additional options
        subprocess.run(
            [
                "screencapture",
                "-x",  # Don't play sound
                "-t",
                "png",  # Specify format
                "-C",  # Capture cursor
                "-T",
                "0",  # No delay
                "-P",  # Include pointer
                filename,
            ]
        )

        # Verify the screenshot was taken
        if os.path.exists(filename):
            return f"Screenshot saved as {filename}"
        else:
            raise Exception("Screenshot file not created")
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return "Failed to take screenshot"


def record_audio(duration: int = 30) -> str:
    """Start audio recording on macOS with enhanced options."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.m4a"

        # Use ffmpeg with enhanced options
        subprocess.run(
            [
                "ffmpeg",
                "-f",
                "avfoundation",
                "-i",
                ":0",
                "-acodec",
                "aac",
                "-ab",
                "192k",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-t",
                str(duration),
                "-y",  # Overwrite output file if exists
                filename,
            ]
        )

        # Verify the recording was created
        if os.path.exists(filename):
            return f"Audio recording saved as {filename}"
        else:
            raise Exception("Audio file not created")
    except Exception as e:
        logger.error(f"Error recording audio: {e}")
        return "Failed to record audio"


def process_command(command: str) -> str:
    """Process voice command with enhanced recognition and response."""
    command = command.lower().strip()

    # Add command to history
    COMMAND_HISTORY.append(command)

    # Extract numbers from command for thresholds
    numbers = re.findall(r"\d+", command)
    threshold = float(numbers[0]) if numbers else None

    # Enhanced command processing with context
    for cmd_type, patterns in COMMAND_PATTERNS.patterns.items():
        for pattern in patterns:
            if re.search(pattern, command):
                # Handle command based on type
                if cmd_type == "system_status":
                    metrics = get_system_metrics()
                    return format_metrics(metrics)

                elif cmd_type == "cpu_usage":
                    metrics = get_system_metrics()
                    return f"CPU usage is {metrics['cpu']['percent']} percent"

                elif cmd_type == "memory_usage":
                    metrics = get_system_metrics()
                    return f"Memory usage is {metrics['memory']['percent']} percent"

                elif cmd_type == "disk_usage":
                    metrics = get_system_metrics()
                    return f"Disk usage is {metrics['disk']['percent']} percent"

                elif cmd_type == "network_status":
                    metrics = get_system_metrics()
                    net_sent_mb = metrics["network"]["bytes_sent"] / (1024**2)
                    net_recv_mb = metrics["network"]["bytes_recv"] / (1024**2)
                    return f"Network sent {net_sent_mb:.1f} megabytes and received {net_recv_mb:.1f} megabytes"

                elif cmd_type == "battery_status":
                    metrics = get_system_metrics()
                    if metrics["battery"]:
                        return f"Battery is at {metrics['battery']['percent']} percent"
                    return "No battery information available"

                elif cmd_type == "process_list":
                    processes = get_running_processes()
                    return format_processes(processes)

                elif cmd_type == "export_metrics":
                    format_type = "csv" if "csv" in command else "json"
                    filename = export_metrics(format_type)
                    return f"Metrics exported to {filename}"

                elif cmd_type == "open_dashboard":
                    webbrowser.open("http://localhost:5000")
                    return "Opening dashboard in web browser"

                elif cmd_type == "set_alert":
                    if threshold is not None:
                        metric = next(
                            (m for m in ["cpu", "memory", "disk"] if m in command), None
                        )
                        condition = "above" if "above" in command else "below"
                        return set_alert(metric, threshold, condition)
                    return "Please specify metric, condition, and threshold"

                elif cmd_type == "list_alerts":
                    return list_alerts()

                elif cmd_type == "clear_alerts":
                    return clear_alerts()

                elif cmd_type == "system_info":
                    return get_system_info()

                elif cmd_type == "start_journal":
                    return "Opening Journal module"

                elif cmd_type == "take_screenshot":
                    return take_screenshot()

                elif cmd_type == "record_audio":
                    duration = threshold if threshold else 30
                    return record_audio(duration)

                elif cmd_type == "system_control":
                    if "sleep" in command:
                        subprocess.run(["pmset", "sleepnow"])
                        return "Putting system to sleep"
                    elif "restart" in command:
                        subprocess.run(["shutdown", "-r", "now"])
                        return "Restarting system"
                    elif "shutdown" in command or "power off" in command:
                        subprocess.run(["shutdown", "-h", "now"])
                        return "Shutting down system"

                elif cmd_type == "network_diagnostics":
                    results = SystemHealth().run_network_diagnostics()
                    if results:
                        return format_network_diagnostics(results)
                    return "Failed to run network diagnostics"

                elif cmd_type == "system_diagnostics":
                    results = run_system_diagnostics()
                    if results:
                        return format_system_diagnostics(results)
                    return "Failed to run system diagnostics"

                elif cmd_type == "performance_analysis":
                    report = SystemHealth().generate_performance_report()
                    if report:
                        return report
                    return "Failed to generate performance report"

                elif cmd_type == "help":
                    return "Available commands: system status, cpu usage, memory usage, disk usage, network status, battery status, running processes, export metrics, open dashboard, set alert, list alerts, clear alerts, system info, start journal, take screenshot, record audio, system control, network diagnostics, system diagnostics, performance analysis, help, exit"

                elif cmd_type == "exit":
                    return "Goodbye, Commander!"
                return

    return "Command not recognized. Try again."


def main():
    try:
        # Initialize voice engine based on platform
        if platform.system() == "Darwin":
            engine = MacOSVoiceEngine()
        else:
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.setProperty("volume", 0.9)

            # Get available voices and set a female voice if available
            voices = engine.getProperty("voices")
            for voice in voices:
                if "female" in voice.name.lower():
                    engine.setProperty("voice", voice.id)
                    break

        # Initialize speech recognizer with enhanced settings
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 4000
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        # Welcome message
        welcome_message = "Hello, I'm Samantha. How can I help you today?"
        print(welcome_message)
        if platform.system() == "Darwin":
            engine.speak(welcome_message)
        else:
            engine.say(welcome_message)
            engine.runAndWait()

        while True:
            try:
                with sr.Microphone() as source:
                    print("Listening...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

                    print("Recognizing...")
                    try:
                        command = recognizer.recognize_google(audio)
                        print(f"You said: {command}")
                        with open("agent_tasks.txt", "a") as f:
                            f.write(command + "\n")
                        engine.say(f"Command received: {command}")
                        engine.runAndWait()
                    except sr.UnknownValueError:
                        engine.say("I didn't catch that. Please repeat.")
                        engine.runAndWait()

                response = process_command(command)
                print(f"Response: {response}")

                if platform.system() == "Darwin":
                    engine.speak(response)
                else:
                    engine.say(response)
                    engine.runAndWait()

                # Send command and response to Telegram
                send_telegram_message(f"Command: {command}\nResponse: {response}")

                if "Goodbye" in response:
                    break

            except sr.WaitTimeoutError:
                print("No speech detected")
                if platform.system() == "Darwin":
                    engine.speak("I didn't hear anything. Please try again.")
                else:
                    engine.say("I didn't hear anything. Please try again.")
                    engine.runAndWait()
            except sr.UnknownValueError:
                print("Sorry, I didn't catch that")
                if platform.system() == "Darwin":
                    engine.speak("I didn't catch that. Please repeat.")
                else:
                    engine.say("I didn't catch that. Please repeat.")
                    engine.runAndWait()
            except sr.RequestError as e:
                print(f"Error with the speech recognition service: {e}")
                if platform.system() == "Darwin":
                    engine.speak(
                        "Sorry, there was an error with the speech recognition service"
                    )
                else:
                    engine.say(
                        "Sorry, there was an error with the speech recognition service"
                    )
                    engine.runAndWait()
            except Exception as e:
                print(f"Error: {e}")
                logger.error(f"Unexpected error: {e}")
                if platform.system() == "Darwin":
                    engine.speak("Sorry, an error occurred")
                else:
                    engine.say("Sorry, an error occurred")
                    engine.runAndWait()

    except Exception as e:
        logger.error(f"Critical error in main loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
