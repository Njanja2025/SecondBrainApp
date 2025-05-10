#!/usr/bin/env python3
"""
SecondBrain Status Dashboard Generator with Historical Data
"""
import os
import psutil
import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
import logging
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path
from collections import deque
from typing import Dict, List, Optional, Union
from config import (
    DASHBOARD_DIR, BACKUP_DIR, MAX_HISTORY_HOURS,
    REFRESH_INTERVAL, SAMPLE_INTERVAL, CHART_COLORS,
    THRESHOLDS, RESOURCE_LIMITS, CHART_STYLE,
    BACKUP_SETTINGS, LOG_SETTINGS, ALERT_SETTINGS,
    HEALTH_CHECK_SETTINGS, CONFIG_DIR
)
from alerts import AlertManager
from export import DataExporter
from health_check import HealthChecker
from access_control import AccessControl, Role, Permission, require_permission, require_role

# Set up logging with rotation
log_dir = Path(LOG_SETTINGS['log_file']).parent
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_SETTINGS['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            LOG_SETTINGS['log_file'],
            maxBytes=LOG_SETTINGS['max_log_size'],
            backupCount=LOG_SETTINGS['backup_count']
        )
    ]
)
logger = logging.getLogger(__name__)

# Configure matplotlib style
plt.style.use('seaborn')
plt.rcParams.update({
    'font.family': CHART_STYLE['font_family'],
    'font.size': CHART_STYLE['font_size'],
    'axes.titlesize': CHART_STYLE['title_size'],
    'axes.labelsize': CHART_STYLE['label_size'],
    'xtick.labelsize': CHART_STYLE['tick_size'],
    'ytick.labelsize': CHART_STYLE['tick_size'],
    'legend.fontsize': CHART_STYLE['legend_size'],
    'figure.facecolor': CHART_STYLE['background_color'],
    'axes.facecolor': CHART_STYLE['background_color'],
    'grid.color': CHART_STYLE['grid_color'],
    'text.color': CHART_STYLE['text_color'],
    'axes.labelcolor': CHART_STYLE['text_color'],
    'xtick.color': CHART_STYLE['text_color'],
    'ytick.color': CHART_STYLE['text_color']
})

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

class DashboardGenerator:
    def __init__(self):
        """Initialize the dashboard generator with proper error handling."""
        try:
            self._validate_directories()
            self._setup_directories()
            self.max_history = int((MAX_HISTORY_HOURS * 60) / SAMPLE_INTERVAL)
            self.load_history()
            self._cleanup_old_charts()
            
            # Initialize components
            self.alert_manager = AlertManager(ALERT_SETTINGS['config_file'])
            self.data_exporter = DataExporter()
            self.health_checker = HealthChecker()
            self.access_control = AccessControl(CONFIG_DIR)
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard generator: {e}")
            raise

    def _validate_directories(self) -> None:
        """Validate directory paths."""
        if not isinstance(DASHBOARD_DIR, Path):
            raise ValueError("DASHBOARD_DIR must be a Path object")
        if not isinstance(BACKUP_DIR, Path):
            raise ValueError("BACKUP_DIR must be a Path object")

    def _setup_directories(self) -> None:
        """Set up necessary directories with proper permissions."""
        self.dashboard_dir = DASHBOARD_DIR
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.dashboard_dir, 0o755)
        
        self.history_file = self.dashboard_dir / 'history.json'
        self.charts_dir = self.dashboard_dir / 'charts'
        self.charts_dir.mkdir(exist_ok=True)
        os.chmod(self.charts_dir, 0o755)

    def _cleanup_old_charts(self) -> None:
        """Clean up old chart files."""
        try:
            for chart_file in self.charts_dir.glob('*.png'):
                if (datetime.datetime.now().timestamp() - chart_file.stat().st_mtime) > 3600:
                    chart_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup old charts: {e}")

    def _validate_data(self, data: Dict) -> None:
        """Validate data structure and values."""
        required_keys = ['cpu', 'memory', 'disk', 'network_in', 'network_out', 'timestamps']
        if not all(key in data for key in required_keys):
            raise DataValidationError(f"Missing required keys in data: {required_keys}")
        
        for key in required_keys:
            if not isinstance(data[key], (list, deque)):
                raise DataValidationError(f"Invalid data type for {key}")

    def load_history(self) -> None:
        """Load historical data with validation."""
        try:
            if self.history_file.exists():
                with open(self.history_file) as f:
                    data = json.load(f)
                    self._validate_data(data)
                    self.history = {
                        k: deque(v, maxlen=self.max_history)
                        for k, v in data.items()
                    }
            else:
                self.history = {
                    'cpu': deque(maxlen=self.max_history),
                    'memory': deque(maxlen=self.max_history),
                    'disk': deque(maxlen=self.max_history),
                    'network_in': deque(maxlen=self.max_history),
                    'network_out': deque(maxlen=self.max_history),
                    'timestamps': deque(maxlen=self.max_history)
                }
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            raise

    def save_history(self) -> None:
        """Save historical data with atomic write."""
        temp_file = self.history_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump({k: list(v) for k, v in self.history.items()}, f)
            temp_file.replace(self.history_file)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def check_resource_limits(self, stats: Dict) -> List[str]:
        """Check if any resource limits are exceeded."""
        warnings = []
        
        if stats['cpu_percent'] > RESOURCE_LIMITS['cpu_high_watermark']:
            warnings.append(f"CPU usage ({stats['cpu_percent']}%) exceeds high watermark")
            
        if stats['memory_percent'] > RESOURCE_LIMITS['memory_high_watermark']:
            warnings.append(f"Memory usage ({stats['memory_percent']}%) exceeds high watermark")
            
        if stats['disk_percent'] > RESOURCE_LIMITS['disk_high_watermark']:
            warnings.append(f"Disk usage ({stats['disk_percent']}%) exceeds high watermark")
            
        if stats['processes'] > RESOURCE_LIMITS['max_processes']:
            warnings.append(f"Process count ({stats['processes']}) exceeds limit")
            
        free_disk_gb = (100 - stats['disk_percent']) * psutil.disk_usage('/').total / 100 / (1024**3)
        if free_disk_gb < RESOURCE_LIMITS['min_free_disk']:
            warnings.append(f"Free disk space ({free_disk_gb:.1f}GB) below minimum")
            
        return warnings

    @require_permission(Permission.VIEW_DASHBOARD)
    def generate_system_stats(self, token: str = None) -> Dict:
        """Generate system statistics with validation and limits checking."""
        try:
            stats = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'load_avg': os.getloadavg(),
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv
                },
                'processes': len(psutil.pids()),
                'temperature': self.get_cpu_temperature()
            }
            
            # Check resource limits
            warnings = self.check_resource_limits(stats)
            if warnings:
                logger.warning("Resource limits exceeded:\n" + "\n".join(warnings))
            
            # Update history
            self._update_history(stats)
            
            return stats
        except Exception as e:
            logger.error(f"Failed to generate system stats: {e}")
            raise

    @require_permission(Permission.VIEW_DASHBOARD)
    def generate_backup_stats(self, token: str = None) -> Dict:
        """Generate backup statistics with validation."""
        try:
            if not BACKUP_DIR.exists():
                logger.warning(f"Backup directory {BACKUP_DIR} does not exist")
                return self._empty_backup_stats()

            # Get all backup files with supported formats
            backups = []
            for format in BACKUP_SETTINGS['backup_formats']:
                backups.extend(BACKUP_DIR.glob(f"*{format}"))
            
            if not backups:
                return self._empty_backup_stats()

            # Process backup statistics
            return self._process_backup_stats(backups)
            
        except Exception as e:
            logger.error(f"Failed to generate backup stats: {e}")
            return self._empty_backup_stats()

    @require_permission(Permission.VIEW_DASHBOARD)
    def generate_charts(self, system_stats: Dict, token: str = None) -> None:
        """Generate performance charts with historical data."""
        self.generate_resource_chart(system_stats)
        self.generate_historical_chart()
        self.generate_network_chart()

    @require_permission(Permission.VIEW_DASHBOARD)
    def generate(self, token: str = None) -> None:
        """Generate complete dashboard with all components."""
        try:
            # Generate system stats
            system_stats = self.generate_system_stats(token=token)
            backup_stats = self.generate_backup_stats(token=token)
            
            # Run health checks
            health_status = self.health_checker.run_health_checks()
            
            # Process alerts
            alerts = self.alert_manager.process_alerts(system_stats)
            
            # Generate charts
            self.generate_charts(system_stats, token=token)
            
            # Generate HTML
            self.generate_html(system_stats, backup_stats, health_status, alerts)
            
            # Export data if user has permission
            if self.access_control.has_permission(token, Permission.EXPORT_DATA):
                dashboard_data = {
                    'system_stats': system_stats,
                    'backup_stats': backup_stats,
                    'health_status': health_status,
                    'alerts': alerts,
                    'history': {k: list(v) for k, v in self.history.items()}
                }
                self.data_exporter.export_data(dashboard_data)
            
            # Cleanup
            self._cleanup_old_charts()
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard: {e}")
            raise

    def _update_history(self, stats: Dict) -> None:
        """Update historical data."""
        now = datetime.datetime.now().strftime('%H:%M')
        self.history['timestamps'].append(now)
        self.history['cpu'].append(stats['cpu_percent'])
        self.history['memory'].append(stats['memory_percent'])
        self.history['disk'].append(stats['disk_percent'])
        self.history['network_in'].append(stats['network']['bytes_recv'])
        self.history['network_out'].append(stats['network']['bytes_sent'])
        self.save_history()

    def _process_backup_stats(self, backups: List[Path]) -> Dict:
        """Process backup statistics."""
        valid_backups = [b for b in backups if b.stat().st_size >= BACKUP_SETTINGS['min_backup_size']]
        valid_backups.sort(key=lambda x: x.stat().st_mtime)
        
        if len(valid_backups) > BACKUP_SETTINGS['max_backups']:
            valid_backups = valid_backups[-BACKUP_SETTINGS['max_backups']:]

        return {
            'total_backups': len(valid_backups),
            'latest_backup': valid_backups[-1].name if valid_backups else None,
            'backup_sizes': [{'name': b.name, 'size': b.stat().st_size} for b in valid_backups],
            'total_size': sum(b.stat().st_size for b in valid_backups),
            'size_trend': self.calculate_size_trend([b.stat().st_size for b in valid_backups])
        }

    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature if available."""
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            return None
        except Exception as e:
            logger.debug(f"Could not get CPU temperature: {e}")
            return None

    def calculate_size_trend(self, sizes):
        """Calculate backup size trend."""
        if len(sizes) < 2:
            return 0
        return ((sizes[-1] - sizes[-2]) / sizes[-2]) * 100
        
    def generate_resource_chart(self, system_stats):
        """Generate current resource usage chart with improved styling."""
        labels = ['CPU', 'Memory', 'Disk']
        sizes = [system_stats['cpu_percent'], 
                system_stats['memory_percent'],
                system_stats['disk_percent']]
        
        plt.figure(figsize=CHART_STYLE['figure_size'])
        bars = plt.bar(labels, sizes, 
                      color=[CHART_COLORS['cpu'], 
                            CHART_COLORS['memory'], 
                            CHART_COLORS['disk']])
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom',
                    color=CHART_STYLE['text_color'])
        
        plt.title('Current Resource Usage')
        plt.ylabel('Percentage')
        plt.ylim(0, 100)
        plt.grid(True, alpha=CHART_STYLE['grid_alpha'])
        plt.savefig(self.charts_dir / 'resource_usage.png', 
                   dpi=CHART_STYLE['dpi'],
                   bbox_inches='tight',
                   facecolor=CHART_STYLE['background_color'])
        plt.close()
        
    def generate_historical_chart(self):
        """Generate historical usage chart with improved styling."""
        plt.figure(figsize=CHART_STYLE['figure_size'])
        
        timestamps = list(self.history['timestamps'])
        if len(timestamps) > 12:
            n = len(timestamps) // 12
            plt.xticks(range(0, len(timestamps), n), timestamps[::n], rotation=45)
        
        plt.plot(self.history['cpu'], label='CPU', 
                color=CHART_COLORS['cpu'],
                linewidth=CHART_STYLE['line_width'],
                marker='.', markersize=CHART_STYLE['marker_size'])
        plt.plot(self.history['memory'], label='Memory',
                color=CHART_COLORS['memory'],
                linewidth=CHART_STYLE['line_width'],
                marker='.', markersize=CHART_STYLE['marker_size'])
        plt.plot(self.history['disk'], label='Disk',
                color=CHART_COLORS['disk'],
                linewidth=CHART_STYLE['line_width'],
                marker='.', markersize=CHART_STYLE['marker_size'])
        
        plt.title('Resource Usage History (24h)')
        plt.ylabel('Percentage')
        plt.xlabel('Time')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=CHART_STYLE['grid_alpha'])
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'historical_usage.png',
                   dpi=CHART_STYLE['dpi'],
                   bbox_inches='tight',
                   facecolor=CHART_STYLE['background_color'])
        plt.close()
        
    def generate_network_chart(self):
        """Generate network traffic chart."""
        plt.figure(figsize=(12, 6))
        
        timestamps = list(self.history['timestamps'])
        if len(timestamps) > 12:
            n = len(timestamps) // 12
            plt.xticks(range(0, len(timestamps), n), timestamps[::n], rotation=45)
        
        # Convert bytes to MB
        network_in = [b/1024/1024 for b in self.history['network_in']]
        network_out = [b/1024/1024 for b in self.history['network_out']]
        
        plt.plot(network_in, label='Incoming', color='#27ae60')
        plt.plot(network_out, label='Outgoing', color='#c0392b')
        
        plt.title('Network Traffic History (24h)')
        plt.ylabel('MB')
        plt.xlabel('Time')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'network_traffic.png')
        plt.close()
        
    def generate_html(self, system_stats, backup_stats, health_status, alerts):
        """Generate HTML dashboard with dark mode support."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SecondBrain Status Dashboard</title>
            <meta http-equiv="refresh" content="300">
            <style>
                :root {{
                    --bg-color: #f5f6fa;
                    --card-bg: white;
                    --text-color: #2c3e50;
                    --metric-bg: #f8f9fa;
                    --border-color: #ddd;
                    --shadow-color: rgba(0,0,0,0.1);
                }}
                
                @media (prefers-color-scheme: dark) {{
                    :root {{
                        --bg-color: #1a1a1a;
                        --card-bg: #2d2d2d;
                        --text-color: #e0e0e0;
                        --metric-bg: #363636;
                        --border-color: #404040;
                        --shadow-color: rgba(0,0,0,0.3);
                    }}
                }}
                
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    transition: background-color 0.3s ease;
                }}
                
                .status-card {{ 
                    border: 1px solid var(--border-color); 
                    padding: 20px; 
                    margin: 15px;
                    border-radius: 8px;
                    background-color: var(--card-bg);
                    box-shadow: 0 2px 4px var(--shadow-color);
                }}
                
                .chart {{ 
                    margin: 20px 0;
                    padding: 15px;
                    background-color: var(--card-bg);
                    border-radius: 8px;
                    box-shadow: 0 2px 4px var(--shadow-color);
                }}
                
                .critical {{ color: #ff6b6b; font-weight: bold; }}
                .warning {{ color: #ffd93d; font-weight: bold; }}
                .good {{ color: #6bff6b; font-weight: bold; }}
                
                .metric {{ 
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 10px;
                    background-color: var(--metric-bg);
                    border-radius: 4px;
                    transition: background-color 0.3s ease;
                }}
                
                .trend-up {{ color: #ff6b6b; }}
                .trend-down {{ color: #6bff6b; }}
                
                h1, h2 {{ color: var(--text-color); }}
                img {{ max-width: 100%; height: auto; border-radius: 4px; }}
                
                /* Theme toggle button */
                #theme-toggle {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 10px;
                    border-radius: 50%;
                    border: none;
                    background-color: var(--card-bg);
                    color: var(--text-color);
                    cursor: pointer;
                    box-shadow: 0 2px 4px var(--shadow-color);
                }}
            </style>
            <script>
                function toggleTheme() {{
                    const html = document.documentElement;
                    const currentTheme = html.getAttribute('data-theme');
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    html.setAttribute('data-theme', newTheme);
                    localStorage.setItem('theme', newTheme);
                }}
                
                document.addEventListener('DOMContentLoaded', () => {{
                    const savedTheme = localStorage.getItem('theme') || 
                        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                    document.documentElement.setAttribute('data-theme', savedTheme);
                }});
            </script>
        </head>
        <body>
            <button id="theme-toggle" onclick="toggleTheme()">🌓</button>
            <h1>SecondBrain Status Dashboard</h1>
            
            <div class="status-card">
                <h2>System Status</h2>
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span class="{self.get_status_class(system_stats['cpu_percent'])}">{system_stats['cpu_percent']}%</span>
                </div>
                <div class="metric">
                    <span>Memory Usage:</span>
                    <span class="{self.get_status_class(system_stats['memory_percent'])}">{system_stats['memory_percent']}%</span>
                </div>
                <div class="metric">
                    <span>Disk Usage:</span>
                    <span class="{self.get_status_class(system_stats['disk_percent'])}">{system_stats['disk_percent']}%</span>
                </div>
                <div class="metric">
                    <span>Load Average:</span>
                    <span>{system_stats['load_avg']}</span>
                </div>
                <div class="metric">
                    <span>Active Processes:</span>
                    <span>{system_stats['processes']}</span>
                </div>
                {f'''<div class="metric">
                    <span>CPU Temperature:</span>
                    <span>{system_stats['temperature']}°C</span>
                </div>''' if system_stats['temperature'] is not None else ''}
            </div>
            
            <div class="status-card">
                <h2>Backup Status</h2>
                <div class="metric">
                    <span>Total Backups:</span>
                    <span>{backup_stats['total_backups']}</span>
                </div>
                <div class="metric">
                    <span>Latest Backup:</span>
                    <span>{backup_stats['latest_backup']}</span>
                </div>
                <div class="metric">
                    <span>Total Size:</span>
                    <span>{self.format_size(backup_stats['total_size'])}</span>
                </div>
                <div class="metric">
                    <span>Size Trend:</span>
                    <span class="{'trend-up' if backup_stats['size_trend'] > 0 else 'trend-down'}">
                        {backup_stats['size_trend']:+.1f}%
                    </span>
                </div>
            </div>
            
            <div class="chart">
                <h2>Current Resource Usage</h2>
                <img src="charts/resource_usage.png" alt="Resource Usage Chart">
            </div>
            
            <div class="chart">
                <h2>Historical Resource Usage</h2>
                <img src="charts/historical_usage.png" alt="Historical Usage Chart">
            </div>
            
            <div class="chart">
                <h2>Network Traffic</h2>
                <img src="charts/network_traffic.png" alt="Network Traffic Chart">
            </div>
            
            <div class="status-card">
                <h2>System Information</h2>
                <div class="metric">
                    <span>Last Updated:</span>
                    <span>{system_stats['uptime']}</span>
                </div>
                <div class="metric">
                    <span>Network In:</span>
                    <span>{self.format_size(system_stats['network']['bytes_recv'])}</span>
                </div>
                <div class="metric">
                    <span>Network Out:</span>
                    <span>{self.format_size(system_stats['network']['bytes_sent'])}</span>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(self.dashboard_dir / 'index.html', 'w') as f:
            f.write(html_content)
            
    def get_status_class(self, value):
        """Get CSS class based on configured thresholds."""
        if value >= THRESHOLDS['critical']:
            return "critical"
        elif value >= THRESHOLDS['warning']:
            return "warning"
        return "good"
        
    def format_size(self, size):
        """Format size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @require_permission(Permission.MANAGE_BACKUPS)
    def cleanup_old_backups(self, token: str = None) -> None:
        """Clean up old backup files (requires backup management permission)."""
        try:
            retention_days = BACKUP_SETTINGS['retention_days']
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
            
            for format in BACKUP_SETTINGS['backup_formats']:
                for backup in BACKUP_DIR.glob(f"*{format}"):
                    if datetime.datetime.fromtimestamp(backup.stat().st_mtime) < cutoff_date:
                        backup.unlink()
                        logger.info(f"Deleted old backup: {backup.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            raise

    @require_permission(Permission.SYSTEM_CONFIG)
    def update_system_config(self, token: str = None, **config_updates) -> None:
        """Update system configuration (requires system config permission)."""
        try:
            # Validate configuration updates
            for key, value in config_updates.items():
                if key in ['REFRESH_INTERVAL', 'SAMPLE_INTERVAL']:
                    if not isinstance(value, int) or value < 1:
                        raise ValueError(f"Invalid value for {key}: {value}")
                elif key in ['THRESHOLDS', 'RESOURCE_LIMITS']:
                    if not isinstance(value, dict):
                        raise ValueError(f"Invalid value for {key}: {value}")
            
            # Apply updates
            config_file = CONFIG_DIR / 'config.json'
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            config.update(config_updates)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"Updated system configuration: {config_updates}")
            
        except Exception as e:
            logger.error(f"Failed to update system configuration: {e}")
            raise

if __name__ == "__main__":
    dashboard = DashboardGenerator()
    dashboard.generate() 