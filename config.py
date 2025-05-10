"""
Configuration settings for the SecondBrain Dashboard
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(os.getenv('SECONDBRAIN_BASE_DIR', os.path.expanduser('~/secondbrain')))
DASHBOARD_DIR = Path(os.getenv('DASHBOARD_OUTPUT_DIR', BASE_DIR / 'dashboard'))
BACKUP_DIR = Path(os.getenv('BACKUP_DIR', BASE_DIR / 'backups'))
CONFIG_DIR = BASE_DIR / 'config'
EXPORT_DIR = BASE_DIR / 'exports'

# Ensure all directories exist
for directory in [BASE_DIR, DASHBOARD_DIR, BACKUP_DIR, CONFIG_DIR, EXPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Dashboard settings
MAX_HISTORY_HOURS = int(os.getenv('MAX_HISTORY_HOURS', '24'))
REFRESH_INTERVAL = int(os.getenv('REFRESH_INTERVAL', '300'))  # seconds
SAMPLE_INTERVAL = int(os.getenv('SAMPLE_INTERVAL', '5'))  # minutes

# Resource monitoring limits
RESOURCE_LIMITS = {
    'cpu_high_watermark': float(os.getenv('CPU_HIGH_WATERMARK', '80')),  # percentage
    'memory_high_watermark': float(os.getenv('MEMORY_HIGH_WATERMARK', '80')),  # percentage
    'disk_high_watermark': float(os.getenv('DISK_HIGH_WATERMARK', '85')),  # percentage
    'max_processes': int(os.getenv('MAX_PROCESSES', '500')),
    'min_free_disk': float(os.getenv('MIN_FREE_DISK', '10')),  # GB
}

# Chart settings
CHART_COLORS = {
    'cpu': '#2ecc71',
    'memory': '#3498db',
    'disk': '#e74c3c',
    'network_in': '#27ae60',
    'network_out': '#c0392b',
    'background': '#ffffff',
    'grid': '#f0f0f0',
    'text': '#2c3e50'
}

# Chart style settings
CHART_STYLE = {
    'figure_size': (12, 6),
    'dpi': 100,
    'grid_alpha': 0.7,
    'line_width': 2,
    'marker_size': 4,
    'font_family': 'sans-serif',
    'font_size': 10,
    'title_size': 14,
    'label_size': 12,
    'tick_size': 10,
    'legend_size': 10,
    'background_color': CHART_COLORS['background'],
    'grid_color': CHART_COLORS['grid'],
    'text_color': CHART_COLORS['text']
}

# Resource thresholds (percentage)
THRESHOLDS = {
    'critical': float(os.getenv('THRESHOLD_CRITICAL', '90')),
    'warning': float(os.getenv('THRESHOLD_WARNING', '75'))
}

# Backup settings
BACKUP_SETTINGS = {
    'max_backups': int(os.getenv('MAX_BACKUPS', '10')),
    'min_backup_size': int(os.getenv('MIN_BACKUP_SIZE', '1024')),  # bytes
    'backup_formats': ['.tar.gz', '.zip', '.backup'],
    'compression_level': int(os.getenv('BACKUP_COMPRESSION_LEVEL', '9')),
    'retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
}

# Logging settings
LOG_SETTINGS = {
    'log_file': BASE_DIR / 'logs' / 'dashboard.log',
    'max_log_size': 1024 * 1024 * 10,  # 10 MB
    'backup_count': 5,
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
}

# Alert settings
ALERT_SETTINGS = {
    'config_file': CONFIG_DIR / 'alerts.json',
    'enabled': os.getenv('ENABLE_ALERTS', 'true').lower() == 'true',
    'email': {
        'enabled': os.getenv('ENABLE_EMAIL_ALERTS', 'false').lower() == 'true',
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('SMTP_USERNAME', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'from_addr': os.getenv('ALERT_FROM_EMAIL', ''),
        'to_addrs': os.getenv('ALERT_TO_EMAILS', '').split(',')
    }
}

# Export settings
EXPORT_SETTINGS = {
    'formats': ['json', 'csv', 'xlsx'],
    'retention_days': int(os.getenv('EXPORT_RETENTION_DAYS', '7')),
    'max_exports': int(os.getenv('MAX_EXPORTS', '100')),
    'compress_exports': os.getenv('COMPRESS_EXPORTS', 'true').lower() == 'true'
}

# Health check settings
HEALTH_CHECK_SETTINGS = {
    'enabled': os.getenv('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true',
    'interval_minutes': int(os.getenv('HEALTH_CHECK_INTERVAL', '5')),
    'timeout_seconds': int(os.getenv('HEALTH_CHECK_TIMEOUT', '30')),
    'services': [
        {'name': 'system', 'enabled': True},
        {'name': 'backup', 'enabled': True},
        {'name': 'alerts', 'enabled': True},
        {'name': 'dashboard', 'enabled': True}
    ]
} 