"""
Security monitoring system for SecondBrain application.
Provides real-time monitoring, threat detection, and alerting capabilities.
"""
import datetime
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import json
import logging
from threading import Lock
import time
from collections import defaultdict
import ipaddress
from ..security.audit_system import AuditSystem, SecurityAlert

logger = logging.getLogger(__name__)

@dataclass
class SecurityMetrics:
    """Security metrics data structure."""
    failed_attempts: int = 0
    last_attempt: Optional[datetime] = None
    suspicious_ips: Set[str] = set()
    unusual_times: int = 0
    concurrent_sessions: int = 0

class SecurityMonitor:
    """Manages security monitoring and threat detection."""
    
    def __init__(self, audit_system: AuditSystem):
        """
        Initialize security monitor.
        
        Args:
            audit_system: AuditSystem instance for logging
        """
        self.audit_system = audit_system
        self.lock = Lock()
        
        # Security thresholds
        self.thresholds = {
            'failed_logins_per_hour': 5,
            'failed_logins_per_minute': 3,
            'api_requests_per_minute': 100,
            'suspicious_ip_requests': 50,
            'concurrent_sessions_per_user': 3,
            'unusual_time_access': 10  # Number of accesses during unusual hours
        }
        
        # Time windows for monitoring
        self.time_windows = {
            'unusual_hours': (23, 5),  # 11 PM to 5 AM
            'high_risk_hours': (0, 4)   # Midnight to 4 AM
        }
        
        # User metrics storage
        self.user_metrics: Dict[str, SecurityMetrics] = defaultdict(SecurityMetrics)
        
        # IP reputation tracking
        self.ip_reputation: Dict[str, Dict[str, Any]] = {}
        
        # Known good IPs (whitelist)
        self.known_good_ips: Set[str] = set()
        
        # Start monitoring
        self._start_monitoring()
    
    def record_login_attempt(
        self,
        user_id: str,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """
        Record a login attempt and check for suspicious activity.
        
        Args:
            user_id: User ID
            username: Username
            success: Whether login was successful
            ip_address: IP address of the attempt
            session_id: Session ID if available
        """
        with self.lock:
            now = datetime.utcnow()
            metrics = self.user_metrics[user_id]
            
            # Update metrics
            if not success:
                metrics.failed_attempts += 1
                metrics.last_attempt = now
                
                # Check for rapid failed attempts
                if self._check_rapid_failed_attempts(user_id):
                    self._trigger_alert(
                        'rapid_failed_logins',
                        'high',
                        f'Rapid failed login attempts for user {username}',
                        {
                            'user_id': user_id,
                            'username': username,
                            'ip_address': ip_address,
                            'attempts': metrics.failed_attempts
                        }
                    )
            else:
                # Reset failed attempts on success
                metrics.failed_attempts = 0
            
            # Check for unusual time access
            if self._is_unusual_time(now):
                metrics.unusual_times += 1
                if metrics.unusual_times >= self.thresholds['unusual_time_access']:
                    self._trigger_alert(
                        'unusual_time_access',
                        'medium',
                        f'Multiple unusual time accesses for user {username}',
                        {
                            'user_id': user_id,
                            'username': username,
                            'ip_address': ip_address,
                            'access_count': metrics.unusual_times
                        }
                    )
            
            # Check IP reputation
            if ip_address and not self._is_known_good_ip(ip_address):
                self._check_ip_reputation(ip_address, user_id, username)
    
    def _check_rapid_failed_attempts(self, user_id: str) -> bool:
        """Check for rapid failed login attempts."""
        metrics = self.user_metrics[user_id]
        if not metrics.last_attempt:
            return False
        
        time_diff = datetime.utcnow() - metrics.last_attempt
        return (metrics.failed_attempts >= self.thresholds['failed_logins_per_minute'] and
                time_diff.total_seconds() < 60)
    
    def _is_unusual_time(self, timestamp: datetime) -> bool:
        """Check if the timestamp is during unusual hours."""
        hour = timestamp.hour
        return (hour >= self.time_windows['unusual_hours'][0] or
                hour < self.time_windows['unusual_hours'][1])
    
    def _is_known_good_ip(self, ip_address: str) -> bool:
        """Check if IP is in the known good list."""
        return ip_address in self.known_good_ips
    
    def _check_ip_reputation(self, ip_address: str, user_id: str, username: str):
        """Check and update IP reputation."""
        if ip_address not in self.ip_reputation:
            self.ip_reputation[ip_address] = {
                'first_seen': datetime.utcnow(),
                'attempts': 0,
                'successful_logins': 0,
                'failed_logins': 0,
                'associated_users': set()
            }
        
        rep = self.ip_reputation[ip_address]
        rep['attempts'] += 1
        rep['associated_users'].add(user_id)
        
        # Check for suspicious patterns
        if (len(rep['associated_users']) > 3 or
            rep['attempts'] > self.thresholds['suspicious_ip_requests']):
            self._trigger_alert(
                'suspicious_ip',
                'high',
                f'Suspicious activity from IP {ip_address}',
                {
                    'ip_address': ip_address,
                    'attempts': rep['attempts'],
                    'associated_users': list(rep['associated_users'])
                }
            )
    
    def _trigger_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """Create a security alert."""
        alert = SecurityAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details
        )
        self.audit_system.create_security_alert(alert)
        logger.warning(f"Security Alert: {message}")
    
    def _start_monitoring(self):
        """Start security monitoring in background thread."""
        def monitor_security():
            while True:
                try:
                    self._check_security_metrics()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in security monitoring: {e}")
                    time.sleep(60)
        
        import threading
        thread = threading.Thread(target=monitor_security, daemon=True)
        thread.start()
    
    def _check_security_metrics(self):
        """Check security metrics and generate alerts if needed."""
        with self.lock:
            now = datetime.utcnow()
            
            # Check for users with high failed attempts
            for user_id, metrics in self.user_metrics.items():
                if metrics.failed_attempts >= self.thresholds['failed_logins_per_hour']:
                    self._trigger_alert(
                        'high_failed_attempts',
                        'high',
                        f'High number of failed login attempts for user {user_id}',
                        {
                            'user_id': user_id,
                            'attempts': metrics.failed_attempts,
                            'time_window': '1 hour'
                        }
                    )
            
            # Clean up old metrics
            self._cleanup_old_metrics()
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics data."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        # Clean user metrics
        for user_id in list(self.user_metrics.keys()):
            metrics = self.user_metrics[user_id]
            if metrics.last_attempt and metrics.last_attempt < cutoff:
                del self.user_metrics[user_id]
        
        # Clean IP reputation
        for ip in list(self.ip_reputation.keys()):
            rep = self.ip_reputation[ip]
            if rep['first_seen'] < cutoff:
                del self.ip_reputation[ip]
    
    def add_known_good_ip(self, ip_address: str) -> None:
        """Add an IP to the known good list."""
        self.known_good_ips.add(ip_address)
    
    def remove_known_good_ip(self, ip_address: str) -> None:
        """Remove an IP from the known good list."""
        self.known_good_ips.discard(ip_address)
    
    def get_user_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get security metrics for a user."""
        metrics = self.user_metrics.get(user_id, SecurityMetrics())
        return {
            'failed_attempts': metrics.failed_attempts,
            'last_attempt': metrics.last_attempt.isoformat() if metrics.last_attempt else None,
            'unusual_times': metrics.unusual_times,
            'concurrent_sessions': metrics.concurrent_sessions
        }
    
    def get_ip_reputation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get reputation data for an IP address."""
        if ip_address not in self.ip_reputation:
            return None
        
        rep = self.ip_reputation[ip_address]
        return {
            'first_seen': rep['first_seen'].isoformat(),
            'attempts': rep['attempts'],
            'successful_logins': rep['successful_logins'],
            'failed_logins': rep['failed_logins'],
            'associated_users': list(rep['associated_users'])
        }

# Example usage
if __name__ == "__main__":
    # Initialize audit system and security monitor
    audit_system = AuditSystem()
    security_monitor = SecurityMonitor(audit_system)
    
    # Add some known good IPs
    security_monitor.add_known_good_ip("192.168.1.1")
    
    # Simulate login attempts
    for _ in range(6):
        security_monitor.record_login_attempt(
            user_id="test_user",
            username="test_user",
            success=False,
            ip_address="192.168.1.2"
        )
    
    # Simulate successful login
    security_monitor.record_login_attempt(
        user_id="test_user",
        username="test_user",
        success=True,
        ip_address="192.168.1.2"
    )
    
    # Get user metrics
    metrics = security_monitor.get_user_metrics("test_user")
    print(f"User metrics: {json.dumps(metrics, indent=2)}")
    
    # Get IP reputation
    ip_rep = security_monitor.get_ip_reputation("192.168.1.2")
    print(f"IP reputation: {json.dumps(ip_rep, indent=2)}")
    
    # Get security alerts
    alerts = audit_system.get_security_alerts()
    print(f"Security alerts: {json.dumps(alerts, indent=2)}") 