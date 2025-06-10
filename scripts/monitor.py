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
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)

class MemoryEngineMonitor:
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
                }
            },
            'retention': {
                'metrics_days': 30,
                'logs_days': 7
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
            return {
                'metric': 'memory_usage',
                'value': memory_percent,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Failed to check memory usage: {e}")
            return None

    def check_cpu_usage(self):
        """Check CPU usage."""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=1)
            return {
                'metric': 'cpu_usage',
                'value': cpu_percent,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Failed to check CPU usage: {e}")
            return None

    def check_disk_usage(self):
        """Check disk usage."""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                'metric': 'disk_usage',
                'value': disk_usage.percent,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat()
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
            
            conn.close()
            
            return {
                'metric': 'db_health',
                'value': {
                    'integrity': integrity,
                    'indexes': len(indexes),
                    'has_stats': bool(stats)
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
                "SELECT * FROM memory_engine ORDER BY timestamp DESC LIMIT 10"
            ]
            
            results = {}
            for query in queries:
                start_time = time.time()
                cursor.execute(query)
                cursor.fetchall()
                duration = time.time() - start_time
                results[query] = duration
            
            conn.close()
            
            return {
                'metric': 'query_performance',
                'value': results,
                'unit': 'seconds',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Failed to check query performance: {e}")
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

    def collect_metrics(self):
        """Collect all metrics."""
        metrics = [
            self.check_db_size(),
            self.check_memory_usage(),
            self.check_cpu_usage(),
            self.check_disk_usage(),
            self.check_db_health(),
            self.check_query_performance()
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
        logging.info("Starting memory engine monitor...")
        
        # Start worker threads
        self.metrics_thread = threading.Thread(target=self.metrics_worker)
        self.alert_thread = threading.Thread(target=self.alert_worker)
        
        self.metrics_thread.start()
        self.alert_thread.start()
        
        try:
            while True:
                self.collect_metrics()
                self.cleanup_old_data()
                time.sleep(self.config['check_interval'])
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the monitoring system."""
        logging.info("Stopping memory engine monitor...")
        self.running = False
        
        # Wait for queues to be processed
        self.metrics_queue.join()
        self.alert_queue.join()
        
        # Wait for worker threads
        self.metrics_thread.join()
        self.alert_thread.join()
        
        logging.info("Monitor stopped.")

def main():
    parser = argparse.ArgumentParser(description='Memory Engine Monitor')
    parser.add_argument('--config', default='monitor_config.json',
                      help='Path to configuration file')
    args = parser.parse_args()
    
    monitor = MemoryEngineMonitor(args.config)
    monitor.start()

if __name__ == "__main__":
    main() 