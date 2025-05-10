"""
Access control system for SecondBrain application.
Provides role-based access control and integrates with encryption utilities.
"""
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import jwt
from ..utils.encryption_utils import EncryptionUtils, EncryptionError

@dataclass
class User:
    """User data structure."""
    id: str
    username: str
    role: str
    email: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

class AccessControlError(Exception):
    """Custom exception for access control related errors."""
    pass

class AccessControl:
    """Manages access control and permissions for the SecondBrain application."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize access control system.
        
        Args:
            secret_key: Optional secret key for JWT token generation.
                       If not provided, will use encryption key.
        """
        self.encryption_utils = EncryptionUtils()
        self.secret_key = secret_key or self.encryption_utils._load_key()
        
        # Define role-based permissions
        self.authorized_roles = {
            "admin": ["read", "write", "delete", "decrypt", "manage_users"],
            "user": ["read", "write", "encrypt"],
            "viewer": ["read"]
        }
        
        # Store active sessions
        self.active_sessions: Dict[str, User] = {}
        
        # Token expiration time (24 hours)
        self.token_expiry = timedelta(hours=24)
    
    def has_permission(self, role: str, action: str) -> bool:
        """
        Check if a role has permission for a specific action.
        
        Args:
            role: User role
            action: Action to check permission for
            
        Returns:
            bool: True if role has permission, False otherwise
        """
        return action in self.authorized_roles.get(role, [])
    
    def generate_token(self, user: User) -> str:
        """
        Generate JWT token for user authentication.
        
        Args:
            user: User object
            
        Returns:
            str: JWT token
            
        Raises:
            AccessControlError: If token generation fails
        """
        try:
            payload = {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "exp": datetime.utcnow() + self.token_expiry
            }
            return jwt.encode(payload, self.secret_key, algorithm="HS256")
        except Exception as e:
            raise AccessControlError(f"Failed to generate token: {str(e)}")
    
    def verify_token(self, token: str) -> User:
        """
        Verify JWT token and return associated user.
        
        Args:
            token: JWT token to verify
            
        Returns:
            User: User object associated with token
            
        Raises:
            AccessControlError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return User(
                id=payload["user_id"],
                username=payload["username"],
                role=payload["role"]
            )
        except jwt.ExpiredSignatureError:
            raise AccessControlError("Token has expired")
        except jwt.InvalidTokenError:
            raise AccessControlError("Invalid token")
    
    def encrypt_data(self, user: User, data: Union[str, bytes]) -> str:
        """
        Encrypt data with permission check.
        
        Args:
            user: User performing the encryption
            data: Data to encrypt
            
        Returns:
            str: Encrypted data
            
        Raises:
            AccessControlError: If user lacks permission
        """
        if not self.has_permission(user.role, "encrypt"):
            raise AccessControlError(f"User {user.username} lacks encryption permission")
        return self.encryption_utils.encrypt(data)
    
    def decrypt_data(self, user: User, encrypted_data: Union[str, bytes]) -> str:
        """
        Decrypt data with permission check.
        
        Args:
            user: User performing the decryption
            encrypted_data: Data to decrypt
            
        Returns:
            str: Decrypted data
            
        Raises:
            AccessControlError: If user lacks permission
        """
        if not self.has_permission(user.role, "decrypt"):
            raise AccessControlError(f"User {user.username} lacks decryption permission")
        return self.encryption_utils.decrypt(encrypted_data)
    
    def create_session(self, user: User) -> str:
        """
        Create a new user session.
        
        Args:
            user: User to create session for
            
        Returns:
            str: Session token
        """
        token = self.generate_token(user)
        self.active_sessions[token] = user
        return token
    
    def end_session(self, token: str) -> None:
        """
        End a user session.
        
        Args:
            token: Session token to end
            
        Raises:
            AccessControlError: If session doesn't exist
        """
        if token not in self.active_sessions:
            raise AccessControlError("Invalid session token")
        del self.active_sessions[token]

# Example usage
if __name__ == "__main__":
    # Initialize access control
    access_control = AccessControl()
    
    # Create test users
    admin = User(id="1", username="admin", role="admin")
    user = User(id="2", username="user", role="user")
    viewer = User(id="3", username="viewer", role="viewer")
    
    # Test permissions
    print(f"Admin can decrypt: {access_control.has_permission('admin', 'decrypt')}")
    print(f"User can decrypt: {access_control.has_permission('user', 'decrypt')}")
    print(f"Viewer can write: {access_control.has_permission('viewer', 'write')}")
    
    # Test encryption/decryption with permissions
    test_data = "Sensitive information"
    
    try:
        # Admin can encrypt and decrypt
        encrypted = access_control.encrypt_data(admin, test_data)
        decrypted = access_control.decrypt_data(admin, encrypted)
        print(f"Admin decryption successful: {decrypted == test_data}")
        
        # User can only encrypt
        encrypted = access_control.encrypt_data(user, test_data)
        try:
            access_control.decrypt_data(user, encrypted)
        except AccessControlError as e:
            print(f"User decryption blocked as expected: {str(e)}")
        
        # Viewer can't encrypt
        try:
            access_control.encrypt_data(viewer, test_data)
        except AccessControlError as e:
            print(f"Viewer encryption blocked as expected: {str(e)}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}") 