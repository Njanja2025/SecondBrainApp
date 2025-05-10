"""
Access control and authentication system for SecondBrain Dashboard
"""
import json
import logging
import hashlib
import secrets
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum, auto

logger = logging.getLogger(__name__)

class Role(Enum):
    """System roles with hierarchical permissions."""
    ADMIN = auto()
    EDITOR = auto()
    VIEWER = auto()

class Permission(Enum):
    """System permissions."""
    # Admin permissions
    MANAGE_USERS = auto()
    MANAGE_ROLES = auto()
    SYSTEM_CONFIG = auto()
    VIEW_AUDIT_LOGS = auto()
    
    # Editor permissions
    EDIT_DASHBOARD = auto()
    MANAGE_ALERTS = auto()
    MANAGE_BACKUPS = auto()
    EXPORT_DATA = auto()
    
    # Viewer permissions
    VIEW_DASHBOARD = auto()
    VIEW_ALERTS = auto()
    VIEW_STATS = auto()

class AccessControl:
    def __init__(self, config_dir: Path):
        """Initialize access control system."""
        self.config_dir = config_dir
        self.users_file = config_dir / 'users.json'
        self.sessions_file = config_dir / 'sessions.json'
        self.roles_file = config_dir / 'roles.json'
        self.audit_log_file = config_dir / 'audit.log'
        
        # Security settings
        self.session_duration = timedelta(hours=24)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.password_min_length = 8
        self.require_special_chars = True
        
        # Role hierarchy and permissions
        self.role_hierarchy = {
            Role.ADMIN: {*Permission},  # Admin has all permissions
            Role.EDITOR: {
                Permission.EDIT_DASHBOARD,
                Permission.MANAGE_ALERTS,
                Permission.MANAGE_BACKUPS,
                Permission.EXPORT_DATA,
                Permission.VIEW_DASHBOARD,
                Permission.VIEW_ALERTS,
                Permission.VIEW_STATS
            },
            Role.VIEWER: {
                Permission.VIEW_DASHBOARD,
                Permission.VIEW_ALERTS,
                Permission.VIEW_STATS
            }
        }
        
        # Initialize configuration files
        self._init_config_files()
        
        # Load configurations
        self.load_users()
        self.load_sessions()
        self.load_roles()

    def _init_config_files(self) -> None:
        """Initialize configuration files if they don't exist."""
        if not self.users_file.exists():
            self._create_default_users()
        if not self.sessions_file.exists():
            self._create_default_sessions()
        if not self.roles_file.exists():
            self._create_default_roles()
        if not self.audit_log_file.exists():
            self.audit_log_file.touch()

    def _create_default_users(self) -> None:
        """Create default users configuration."""
        default_users = {
            'users': {
                'admin': {
                    'password_hash': self._hash_password('admin'),  # Change in production
                    'role': Role.ADMIN.name,
                    'failed_attempts': 0,
                    'last_failed_attempt': None,
                    'locked_until': None,
                    'created_at': datetime.now().isoformat(),
                    'last_login': None,
                    'requires_password_change': True
                }
            }
        }
        with open(self.users_file, 'w') as f:
            json.dump(default_users, f, indent=4)

    def _create_default_sessions(self) -> None:
        """Create default sessions configuration."""
        with open(self.sessions_file, 'w') as f:
            json.dump({'sessions': {}}, f, indent=4)

    def _create_default_roles(self) -> None:
        """Create default roles configuration with hierarchical permissions."""
        default_roles = {
            'roles': {
                Role.ADMIN.name: {
                    'permissions': [perm.name for perm in Permission],
                    'can_assign_roles': [role.name for role in Role],
                    'description': 'Full system access'
                },
                Role.EDITOR.name: {
                    'permissions': [
                        perm.name for perm in self.role_hierarchy[Role.EDITOR]
                    ],
                    'can_assign_roles': [Role.VIEWER.name],
                    'description': 'Can edit dashboard and manage alerts/backups'
                },
                Role.VIEWER.name: {
                    'permissions': [
                        perm.name for perm in self.role_hierarchy[Role.VIEWER]
                    ],
                    'can_assign_roles': [],
                    'description': 'Read-only access to dashboard'
                }
            }
        }
        with open(self.roles_file, 'w') as f:
            json.dump(default_roles, f, indent=4)

    def load_users(self) -> None:
        """Load users configuration."""
        with open(self.users_file) as f:
            self.users = json.load(f)

    def load_sessions(self) -> None:
        """Load active sessions."""
        with open(self.sessions_file) as f:
            self.sessions = json.load(f)
        self._cleanup_expired_sessions()

    def load_roles(self) -> None:
        """Load role definitions."""
        with open(self.roles_file) as f:
            self.roles = json.load(f)

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions."""
        now = datetime.now()
        expired = []
        for token, session in self.sessions['sessions'].items():
            if datetime.fromisoformat(session['expires_at']) < now:
                expired.append(token)
        
        for token in expired:
            del self.sessions['sessions'][token]
        
        if expired:
            self._save_sessions()

    def _save_users(self) -> None:
        """Save users configuration."""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)

    def _save_sessions(self) -> None:
        """Save active sessions."""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=4)

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return session token if successful."""
        if username not in self.users['users']:
            return None

        user = self.users['users'][username]
        now = datetime.now()

        # Check if account is locked
        if user['locked_until'] and datetime.fromisoformat(user['locked_until']) > now:
            logger.warning(f"Account {username} is locked until {user['locked_until']}")
            return None

        # Verify password
        if self._hash_password(password) != user['password_hash']:
            user['failed_attempts'] = user.get('failed_attempts', 0) + 1
            user['last_failed_attempt'] = now.isoformat()
            
            # Lock account if too many failed attempts
            if user['failed_attempts'] >= self.max_failed_attempts:
                user['locked_until'] = (now + self.lockout_duration).isoformat()
                logger.warning(f"Account {username} locked due to too many failed attempts")
            
            self._save_users()
            return None

        # Reset failed attempts on successful login
        user['failed_attempts'] = 0
        user['last_login'] = now.isoformat()
        user['locked_until'] = None
        
        # Create new session
        token = self._generate_session_token()
        self.sessions['sessions'][token] = {
            'username': username,
            'created_at': now.isoformat(),
            'expires_at': (now + self.session_duration).isoformat(),
            'last_activity': now.isoformat()
        }
        
        self._save_users()
        self._save_sessions()
        return token

    def validate_session(self, token: str) -> bool:
        """Validate session token."""
        if token not in self.sessions['sessions']:
            return False

        session = self.sessions['sessions'][token]
        now = datetime.now()
        
        if datetime.fromisoformat(session['expires_at']) < now:
            del self.sessions['sessions'][token]
            self._save_sessions()
            return False

        # Update last activity
        session['last_activity'] = now.isoformat()
        self._save_sessions()
        return True

    def audit_log(self, username: str, action: str, details: str = None) -> None:
        """Log user actions for audit purposes."""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} - User: {username} - Action: {action}"
        if details:
            log_entry += f" - Details: {details}"
        
        with open(self.audit_log_file, 'a') as f:
            f.write(log_entry + '\n')

    def validate_password(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < self.password_min_length:
            return False
        
        if self.require_special_chars:
            special_chars = set('!@#$%^&*()_+-=[]{}|;:,.<>?')
            if not any(char in special_chars for char in password):
                return False
            
        # Check for at least one number and one letter
        has_number = any(char.isdigit() for char in password)
        has_letter = any(char.isalpha() for char in password)
        
        return has_number and has_letter

    def create_user(self, admin_token: str, username: str, password: str, role: Role) -> bool:
        """Create a new user (requires admin privileges)."""
        if not self.has_permission(admin_token, Permission.MANAGE_USERS):
            raise PermissionError("Insufficient privileges to create users")
            
        if not self.validate_password(password):
            raise ValueError("Password does not meet security requirements")
            
        if username in self.users['users']:
            raise ValueError("Username already exists")
            
        admin_username = self.sessions['sessions'][admin_token]['username']
        admin_role = Role[self.users['users'][admin_username]['role']]
        
        # Check if admin can assign the requested role
        if role.name not in self.roles['roles'][admin_role.name]['can_assign_roles']:
            raise PermissionError(f"Cannot assign role {role.name}")
        
        self.users['users'][username] = {
            'password_hash': self._hash_password(password),
            'role': role.name,
            'failed_attempts': 0,
            'last_failed_attempt': None,
            'locked_until': None,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'requires_password_change': True
        }
        
        self._save_users()
        self.audit_log(admin_username, 'create_user', f"Created user: {username} with role: {role.name}")
        return True

    def change_user_role(self, admin_token: str, username: str, new_role: Role) -> bool:
        """Change a user's role (requires admin privileges)."""
        if not self.has_permission(admin_token, Permission.MANAGE_ROLES):
            raise PermissionError("Insufficient privileges to change roles")
            
        if username not in self.users['users']:
            raise ValueError("User does not exist")
            
        admin_username = self.sessions['sessions'][admin_token]['username']
        admin_role = Role[self.users['users'][admin_username]['role']]
        
        # Check if admin can assign the new role
        if new_role.name not in self.roles['roles'][admin_role.name]['can_assign_roles']:
            raise PermissionError(f"Cannot assign role {new_role.name}")
        
        self.users['users'][username]['role'] = new_role.name
        self._save_users()
        self.audit_log(admin_username, 'change_role', f"Changed role for {username} to {new_role.name}")
        return True

    def get_user_permissions(self, token: str) -> Set[Permission]:
        """Get permissions for the user associated with the session token."""
        if not self.validate_session(token):
            return set()

        username = self.sessions['sessions'][token]['username']
        role = Role[self.users['users'][username]['role']]
        return self.role_hierarchy[role]

    def has_permission(self, token: str, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.get_user_permissions(token)

    def has_role(self, token: str, role: Role) -> bool:
        """Check if user has specific role."""
        if not self.validate_session(token):
            return False
            
        username = self.sessions['sessions'][token]['username']
        user_role = Role[self.users['users'][username]['role']]
        return user_role == role

    def logout(self, token: str) -> None:
        """Invalidate session token."""
        if token in self.sessions['sessions']:
            del self.sessions['sessions'][token]
            self._save_sessions()

def require_role(role: Role):
    """Decorator for requiring specific role."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            token = kwargs.get('token')
            if not token or not self.access_control.validate_session(token):
                raise PermissionError("Invalid or expired session")
            if not self.access_control.has_role(token, role):
                raise PermissionError(f"Requires role: {role.name}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: Permission):
    """Decorator for requiring specific permission."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            token = kwargs.get('token')
            if not token or not self.access_control.validate_session(token):
                raise PermissionError("Invalid or expired session")
            if not self.access_control.has_permission(token, permission):
                raise PermissionError(f"Missing required permission: {permission.name}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator 