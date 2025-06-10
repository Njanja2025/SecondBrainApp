#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import psutil
import sqlite3
import requests
import threading
import queue
from datetime import datetime, timedelta
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_monitor.log'),
        logging.StreamHandler()
    ]
)

class EnhancedMonitor:
    def __init__(self, config_path='monitor_config.json'):
        self.config = self.load_config(config_path)
        self.metrics_queue = queue.Queue()
        self.alert_queue = queue.Queue()
        self.running = True

    def load_config(self, config_path):
        """Load monitoring configuration."""
        default_config = {
            'db_path': '/Users/mac/Documents/Applications/BaddyAgent.app/Contents/Resources/SecondBrainApp/brain/memory_engine.db',
            'check_interval': 60,  # seconds
            'metrics': {
                'db_size': {
                    'warning_threshold_mb': 100,
                    'critical_threshold_mb': 500
                },
                'memory_usage': {
                    'warning_threshold_percent': 70,
                    'critical_threshold_percent': 90
                },
                'cpu_usage': {
                    'warning_threshold_percent': 80,
                    'critical_threshold_percent': 95
                },
                'disk_usage': {
                    'warning_threshold_percent': 80,
                    'critical_threshold_percent': 90
                },
                'query_performance': {
                    'warning_threshold_ms': 1000,
                    'critical_threshold_ms': 5000
                },
                'error_rate': {
                    'warning_threshold_percent': 5,
                    'critical_threshold_percent': 10
                }
            },
            'alerts': {
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'smtp_port': 587,
                    'sender': '',
                    'recipients': []
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'headers': {}
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': '',
                    'channel': ''
                }
            },
            'retention': {
                'metrics_days': 30,
                'logs_days': 7
            },
            'dashboards': {
                'enabled': True,
                'port': 8080,
                'auth': {
                    'username': 'admin',
                    'password': 'admin'
                }
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return {**default_config, **json.load(f)}
        return default_config

    def check_db_size(self):
        """Check database size."""
        try:
            size_mb = os.path.getsize(self.config['db_path']) / (1024 * 1024)
            return {
                'metric': 'db_size',
                'value': size_mb,
                'unit': 'MB',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Failed to check DB size: {e}")
            return None

    def check_memory_usage(self):
        """Check memory usage."""
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            memory_info = process.memory_info()
            return {
                'metric': 'memory_usage',
                'value': memory_percent,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'shared': memory_info.shared,
                    'text': memory_info.text,
                    'lib': memory_info.lib,
                    'data': memory_info.data,
                    'dirty': memory_info.dirty
                }
            }
        except Exception as e:
            logging.error(f"Failed to check memory usage: {e}")
            return None

    def check_cpu_usage(self):
        """Check CPU usage."""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=1)
            cpu_times = process.cpu_times()
            return {
                'metric': 'cpu_usage',
                'value': cpu_percent,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'user': cpu_times.user,
                    'system': cpu_times.system,
                    'children_user': cpu_times.children_user,
                    'children_system': cpu_times.children_system
                }
            }
        except Exception as e:
            logging.error(f"Failed to check CPU usage: {e}")
            return None

    def check_disk_usage(self):
        """Check disk usage."""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            return {
                'metric': 'disk_usage',
                'value': disk_usage.percent,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'total': disk_usage.total,
                    'used': disk_usage.used,
                    'free': disk_usage.free,
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                }
            }
        except Exception as e:
            logging.error(f"Failed to check disk usage: {e}")
            return None

    def check_db_health(self):
        """Check database health."""
        try:
            conn = sqlite3.connect(self.config['db_path'])
            cursor = conn.cursor()
            
            # Check table integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            # Check index health
            cursor.execute("PRAGMA index_list")
            indexes = cursor.fetchall()
            
            # Check for long-running transactions
            cursor.execute("""
                SELECT * FROM sqlite_master 
                WHERE type='table' AND name='sqlite_stat1'
            """)
            stats = cursor.fetchone()
            
            # Check for database locks
            cursor.execute("PRAGMA busy_timeout")
            busy_timeout = cursor.fetchone()[0]
            
            # Check for database corruption
            cursor.execute("PRAGMA quick_check")
            quick_check = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'metric': 'db_health',
                'value': {
                    'integrity': integrity,
                    'indexes': len(indexes),
                    'has_stats': bool(stats),
                    'busy_timeout': busy_timeout,
                    'quick_check': quick_check
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Failed to check DB health: {e}")
            return None

    def check_query_performance(self):
        """Check query performance."""
        try:
            conn = sqlite3.connect(self.config['db_path'])
            cursor = conn.cursor()
            
            # Sample queries to check performance
            queries = [
                "SELECT COUNT(*) FROM memory_engine",
                "SELECT * FROM memory_engine LIMIT 1",
                "SELECT * FROM memory_engine ORDER BY timestamp DESC LIMIT 10",
                "SELECT COUNT(*) FROM memory_engine WHERE timestamp > datetime('now', '-1 day')",
                "SELECT COUNT(*) FROM memory_engine GROUP BY strftime('%Y-%m-%d', timestamp)"
            ]
            
            results = {}
            for query in queries:
                start_time = time.time()
                cursor.execute(query)
                cursor.fetchall()
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                results[query] = duration
            
            conn.close()
            
            return {
                'metric': 'query_performance',
                'value': results,
                'unit': 'milliseconds',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Failed to check query performance: {e}")
            return None

    def check_error_rate(self):
        """Check error rate in logs."""
        try:
            log_file = 'enhanced_monitor.log'
            if not os.path.exists(log_file):
                return None
            
            with open(log_file, 'r') as f:
                logs = f.readlines()
            
            total_logs = len(logs)
            error_logs = sum(1 for log in logs if 'ERROR' in log)
            
            error_rate = (error_logs / total_logs * 100) if total_logs > 0 else 0
            
            return {
                'metric': 'error_rate',
                'value': error_rate,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'total_logs': total_logs,
                    'error_logs': error_logs
                }
            }
        except Exception as e:
            logging.error(f"Failed to check error rate: {e}")
            return None

    def evaluate_metrics(self, metrics):
        """Evaluate metrics against thresholds."""
        alerts = []
        
        for metric in metrics:
            if not metric:
                continue
                
            metric_config = self.config['metrics'].get(metric['metric'])
            if not metric_config:
                continue
            
            value = metric['value']
            if isinstance(value, dict):
                continue
            
            if value >= metric_config['critical_threshold_percent']:
                alerts.append({
                    'level': 'critical',
                    'metric': metric['metric'],
                    'value': value,
                    'threshold': metric_config['critical_threshold_percent'],
                    'timestamp': datetime.now().isoformat()
                })
            elif value >= metric_config['warning_threshold_percent']:
                alerts.append({
                    'level': 'warning',
                    'metric': metric['metric'],
                    'value': value,
                    'threshold': metric_config['warning_threshold_percent'],
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts

    def send_alert(self, alert):
        """Send alert through configured channels."""
        if self.config['alerts']['email']['enabled']:
            self.send_email_alert(alert)
        
        if self.config['alerts']['webhook']['enabled']:
            self.send_webhook_alert(alert)
        
        if self.config['alerts']['slack']['enabled']:
            self.send_slack_alert(alert)

    def send_email_alert(self, alert):
        """Send email alert."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            message = f"""
            Alert: {alert['level'].upper()}
            Metric: {alert['metric']}
            Value: {alert['value']} {alert.get('unit', '')}
            Threshold: {alert['threshold']}
            Time: {alert['timestamp']}
            """
            
            msg = MIMEText(message)
            msg['Subject'] = f"Memory Engine Alert: {alert['level']}"
            msg['From'] = self.config['alerts']['email']['sender']
            msg['To'] = ', '.join(self.config['alerts']['email']['recipients'])
            
            with smtplib.SMTP(
                self.config['alerts']['email']['smtp_server'],
                self.config['alerts']['email']['smtp_port']
            ) as server:
                server.starttls()
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")

    def send_webhook_alert(self, alert):
        """Send webhook alert."""
        try:
            response = requests.post(
                self.config['alerts']['webhook']['url'],
                json=alert,
                headers=self.config['alerts']['webhook']['headers']
            )
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to send webhook alert: {e}")

    def send_slack_alert(self, alert):
        """Send Slack alert."""
        try:
            message = {
                'channel': self.config['alerts']['slack']['channel'],
                'text': f"""
                *Memory Engine Alert: {alert['level'].upper()}*
                • Metric: {alert['metric']}
                • Value: {alert['value']} {alert.get('unit', '')}
                • Threshold: {alert['threshold']}
                • Time: {alert['timestamp']}
                """
            }
            
            response = requests.post(
                self.config['alerts']['slack']['webhook_url'],
                json=message
            )
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to send Slack alert: {e}")

    def cleanup_old_data(self):
        """Clean up old metrics and logs."""
        try:
            # Clean up old metrics
            metrics_dir = 'metrics'
            if os.path.exists(metrics_dir):
                cutoff_date = datetime.now() - timedelta(days=self.config['retention']['metrics_days'])
                for file in os.listdir(metrics_dir):
                    file_path = os.path.join(metrics_dir, file)
                    if os.path.getctime(file_path) < cutoff_date.timestamp():
                        os.remove(file_path)
            
            # Clean up old logs
            cutoff_date = datetime.now() - timedelta(days=self.config['retention']['logs_days'])
            for file in os.listdir('.'):
                if file.endswith('.log'):
                    if os.path.getctime(file) < cutoff_date.timestamp():
                        os.remove(file)
        except Exception as e:
            logging.error(f"Failed to cleanup old data: {e}")

    def start_dashboard(self):
        """Start monitoring dashboard."""
        try:
            from flask import Flask, render_template, jsonify, request
            from flask_basicauth import BasicAuth
            
            app = Flask(__name__)
            app.config['BASIC_AUTH_USERNAME'] = self.config['dashboards']['auth']['username']
            app.config['BASIC_AUTH_PASSWORD'] = self.config['dashboards']['auth']['password']
            basic_auth = BasicAuth(app)
            
            @app.route('/')
            @basic_auth.required
            def index():
                return render_template('dashboard.html')
            
            @app.route('/metrics')
            @basic_auth.required
            def get_metrics():
                metrics = []
                while not self.metrics_queue.empty():
                    metrics.extend(self.metrics_queue.get())
                return jsonify(metrics)
            
            @app.route('/alerts')
            @basic_auth.required
            def get_alerts():
                alerts = []
                while not self.alert_queue.empty():
                    alerts.append(self.alert_queue.get())
                return jsonify(alerts)
            
            app.run(port=self.config['dashboards']['port'])
        except Exception as e:
            logging.error(f"Failed to start dashboard: {e}")

    def collect_metrics(self):
        """Collect all metrics."""
        metrics = [
            self.check_db_size(),
            self.check_memory_usage(),
            self.check_cpu_usage(),
            self.check_disk_usage(),
            self.check_db_health(),
            self.check_query_performance(),
            self.check_error_rate()
        ]
        
        # Filter out None values
        metrics = [m for m in metrics if m]
        
        # Store metrics
        self.metrics_queue.put(metrics)
        
        # Evaluate metrics
        alerts = self.evaluate_metrics(metrics)
        for alert in alerts:
            self.alert_queue.put(alert)

    def metrics_worker(self):
        """Worker thread to process metrics."""
        while self.running:
            try:
                metrics = self.metrics_queue.get(timeout=1)
                
                # Store metrics to file
                timestamp = datetime.now().strftime('%Y%m%d')
                metrics_file = f'metrics/metrics_{timestamp}.json'
                os.makedirs('metrics', exist_ok=True)
                
                with open(metrics_file, 'a') as f:
                    json.dump(metrics, f)
                    f.write('\n')
                
                self.metrics_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Metrics worker error: {e}")

    def alert_worker(self):
        """Worker thread to process alerts."""
        while self.running:
            try:
                alert = self.alert_queue.get(timeout=1)
                self.send_alert(alert)
                self.alert_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Alert worker error: {e}")

    def start(self):
        """Start the monitoring system."""
        logging.info("Starting enhanced memory engine monitor...")
        
        # Start worker threads
        self.metrics_thread = threading.Thread(target=self.metrics_worker)
        self.alert_thread = threading.Thread(target=self.alert_worker)
        
        self.metrics_thread.start()
        self.alert_thread.start()
        
        # Start dashboard if enabled
        if self.config['dashboards']['enabled']:
            self.dashboard_thread = threading.Thread(target=self.start_dashboard)
            self.dashboard_thread.start()
        
        try:
            while True:
                self.collect_metrics()
                self.cleanup_old_data()
                time.sleep(self.config['check_interval'])
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the monitoring system."""
        logging.info("Stopping enhanced memory engine monitor...")
        self.running = False
        
        # Wait for queues to be processed
        self.metrics_queue.join()
        self.alert_queue.join()
        
        # Wait for worker threads
        self.metrics_thread.join()
        self.alert_thread.join()
        
        if self.config['dashboards']['enabled']:
            self.dashboard_thread.join()
        
        logging.info("Monitor stopped.")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Memory Engine Monitor')
    parser.add_argument('--config', default='monitor_config.json',
                      help='Path to configuration file')
    args = parser.parse_args()
    
    monitor = EnhancedMonitor(args.config)
    monitor.start()

if __name__ == "__main__":
    main() 