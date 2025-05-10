# Security Module

The Security module provides comprehensive security features for the SecondBrain application, including encryption, access control, audit logging, and security monitoring.

## Components

### 1. Encryption Manager (`encryption_manager.py`)
- Handles data encryption and decryption using both symmetric and asymmetric encryption
- Manages encryption keys and key rotation
- Provides password-based key derivation
- Supports secure key storage and backup

### 2. Access Control (`access_control.py`)
- Manages user permissions and roles
- Implements role-based access control (RBAC)
- Handles user status and session management
- Provides permission checking and validation

### 3. Audit Logger (`audit_logger.py`)
- Tracks system events and user actions
- Maintains detailed audit logs with timestamps
- Supports event filtering and retrieval
- Implements log rotation and cleanup

### 4. Security Monitor (`security_monitor.py`)
- Monitors system security in real-time
- Detects suspicious activities and patterns
- Generates security alerts
- Tracks failed login attempts and unusual access patterns

## Features

- **Encryption**
  - Symmetric encryption using Fernet
  - Asymmetric encryption using RSA
  - Secure key management
  - Key rotation support

- **Access Control**
  - Role-based permissions
  - User status management
  - Session tracking
  - Permission validation

- **Audit Logging**
  - Event tracking
  - Detailed logging
  - Log management
  - Event retrieval

- **Security Monitoring**
  - Real-time monitoring
  - Alert generation
  - Pattern detection
  - IP reputation tracking

## Usage

### Encryption
```python
from secondbrain.modules.01_Security import EncryptionManager

# Initialize encryption manager
manager = EncryptionManager()

# Encrypt data
encrypted_data = manager.encrypt_symmetric(b"sensitive data")

# Decrypt data
decrypted_data = manager.decrypt_symmetric(encrypted_data)
```

### Access Control
```python
from secondbrain.modules.01_Security import AccessControl

# Initialize access control
ac = AccessControl()

# Create user with roles
ac.create_user("user1", ["user", "editor"])

# Check permissions
has_access = ac.check_permission("user1", "write")
```

### Audit Logging
```python
from secondbrain.modules.01_Security import AuditLogger

# Initialize audit logger
audit = AuditLogger()

# Log event
event_id = audit.log_event(
    event_type="auth",
    user_id="user1",
    action="login",
    resource="system",
    status="success",
    details={"method": "password"}
)
```

### Security Monitoring
```python
from secondbrain.modules.01_Security import SecurityMonitor, AuditLogger

# Initialize security monitor
audit = AuditLogger()
monitor = SecurityMonitor(audit)

# Record login attempt
monitor.record_login_attempt("user1", success=True, ip_address="192.168.1.1")

# Get alerts
alerts = monitor.get_alerts(severity="high")
```

## Configuration

The security module uses configuration files stored in the `config/security` directory:

- `monitor_config.json`: Security monitoring settings
- `users.json`: User and role definitions
- `keys/`: Directory for encryption keys

## Dependencies

- `cryptography`: For encryption operations
- `dataclasses`: For data structures
- `pathlib`: For file path handling
- `typing`: For type hints

## Security Considerations

1. **Key Management**
   - Keys are stored securely
   - Regular key rotation is recommended
   - Backup keys are maintained

2. **Access Control**
   - Principle of least privilege
   - Role-based permissions
   - Session management

3. **Audit Logging**
   - Comprehensive event tracking
   - Secure log storage
   - Log rotation

4. **Monitoring**
   - Real-time detection
   - Alert thresholds
   - IP reputation

## Contributing

When contributing to the security module:

1. Follow security best practices
2. Add comprehensive tests
3. Update documentation
4. Review code thoroughly

## License

This module is part of the SecondBrain application and is subject to its license terms. 