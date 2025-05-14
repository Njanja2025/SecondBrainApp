"""
Access control module for SecondBrain application.
Manages user permissions, roles, and access rights.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Permission:
    """Represents a permission in the system."""

    name: str
    description: str
    level: int  # Higher level means more privileged


@dataclass
class Role:
    """Represents a role in the system."""

    name: str
    description: str
    permissions: Set[str]
    level: int


@dataclass
class User:
    """Represents a user in the system."""

    username: str
    roles: Set[str]
    status: str = "active"
    last_login: Optional[datetime] = None
    failed_attempts: int = 0


class AccessControl:
    """Manages access control and permissions."""

    def __init__(self, config_dir: str = "config/security"):
        """Initialize the access control system.

        Args:
            config_dir: Directory to store security configuration
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._initialize_permissions()
        self._initialize_roles()
        self._load_users()

    def _setup_logging(self):
        """Set up logging for the access control system."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _initialize_permissions(self):
        """Initialize system permissions."""
        self.permissions = {
            "read": Permission("read", "Read access", 1),
            "write": Permission("write", "Write access", 2),
            "delete": Permission("delete", "Delete access", 3),
            "admin": Permission("admin", "Administrative access", 4),
            "superuser": Permission("superuser", "Superuser access", 5),
        }

    def _initialize_roles(self):
        """Initialize system roles."""
        self.roles = {
            "user": Role("user", "Regular user", {"read", "write"}, 1),
            "editor": Role("editor", "Content editor", {"read", "write", "delete"}, 2),
            "admin": Role(
                "admin", "System administrator", {"read", "write", "delete", "admin"}, 3
            ),
            "superuser": Role(
                "superuser",
                "Superuser",
                {"read", "write", "delete", "admin", "superuser"},
                4,
            ),
        }

    def _load_users(self):
        """Load user data from storage."""
        self.users_file = self.config_dir / "users.json"
        if self.users_file.exists():
            with open(self.users_file, "r") as f:
                self.users = {
                    username: User(**data) for username, data in json.load(f).items()
                }
        else:
            self.users = {}
            self._save_users()

    def _save_users(self):
        """Save user data to storage."""
        with open(self.users_file, "w") as f:
            json.dump(
                {username: user.__dict__ for username, user in self.users.items()},
                f,
                indent=2,
            )

    def create_user(self, username: str, roles: List[str]) -> bool:
        """Create a new user.

        Args:
            username: Username for the new user
            roles: List of roles to assign

        Returns:
            bool: True if user was created successfully
        """
        try:
            if username in self.users:
                logger.error(f"User {username} already exists")
                return False

            # Validate roles
            for role in roles:
                if role not in self.roles:
                    logger.error(f"Invalid role: {role}")
                    return False

            self.users[username] = User(username=username, roles=set(roles))
            self._save_users()
            logger.info(f"Created user {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to create user {username}: {str(e)}")
            return False

    def delete_user(self, username: str) -> bool:
        """Delete a user.

        Args:
            username: Username to delete

        Returns:
            bool: True if user was deleted successfully
        """
        try:
            if username not in self.users:
                logger.error(f"User {username} does not exist")
                return False

            del self.users[username]
            self._save_users()
            logger.info(f"Deleted user {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user {username}: {str(e)}")
            return False

    def assign_role(self, username: str, role: str) -> bool:
        """Assign a role to a user.

        Args:
            username: Username to assign role to
            role: Role to assign

        Returns:
            bool: True if role was assigned successfully
        """
        try:
            if username not in self.users:
                logger.error(f"User {username} does not exist")
                return False

            if role not in self.roles:
                logger.error(f"Invalid role: {role}")
                return False

            self.users[username].roles.add(role)
            self._save_users()
            logger.info(f"Assigned role {role} to user {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to assign role {role} to user {username}: {str(e)}")
            return False

    def remove_role(self, username: str, role: str) -> bool:
        """Remove a role from a user.

        Args:
            username: Username to remove role from
            role: Role to remove

        Returns:
            bool: True if role was removed successfully
        """
        try:
            if username not in self.users:
                logger.error(f"User {username} does not exist")
                return False

            if role not in self.roles:
                logger.error(f"Invalid role: {role}")
                return False

            self.users[username].roles.discard(role)
            self._save_users()
            logger.info(f"Removed role {role} from user {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove role {role} from user {username}: {str(e)}")
            return False

    def check_permission(self, username: str, permission: str) -> bool:
        """Check if a user has a specific permission.

        Args:
            username: Username to check
            permission: Permission to check

        Returns:
            bool: True if user has the permission
        """
        try:
            if username not in self.users:
                logger.error(f"User {username} does not exist")
                return False

            if permission not in self.permissions:
                logger.error(f"Invalid permission: {permission}")
                return False

            user = self.users[username]
            if user.status != "active":
                return False

            # Check if any of the user's roles have the permission
            for role_name in user.roles:
                role = self.roles[role_name]
                if permission in role.permissions:
                    return True

            return False

        except Exception as e:
            logger.error(
                f"Failed to check permission {permission} for user {username}: {str(e)}"
            )
            return False

    def get_user_permissions(self, username: str) -> Set[str]:
        """Get all permissions for a user.

        Args:
            username: Username to get permissions for

        Returns:
            Set of permission names
        """
        try:
            if username not in self.users:
                logger.error(f"User {username} does not exist")
                return set()

            permissions = set()
            for role_name in self.users[username].roles:
                role = self.roles[role_name]
                permissions.update(role.permissions)

            return permissions

        except Exception as e:
            logger.error(f"Failed to get permissions for user {username}: {str(e)}")
            return set()

    def update_user_status(self, username: str, status: str) -> bool:
        """Update a user's status.

        Args:
            username: Username to update
            status: New status

        Returns:
            bool: True if status was updated successfully
        """
        try:
            if username not in self.users:
                logger.error(f"User {username} does not exist")
                return False

            valid_statuses = {"active", "inactive", "locked", "suspended"}
            if status not in valid_statuses:
                logger.error(f"Invalid status: {status}")
                return False

            self.users[username].status = status
            self._save_users()
            logger.info(f"Updated status of user {username} to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update status of user {username}: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    ac = AccessControl()

    # Create a user
    ac.create_user("testuser", ["user"])

    # Assign a role
    ac.assign_role("testuser", "editor")

    # Check permissions
    has_write = ac.check_permission("testuser", "write")
    print("User has write permission:", has_write)

    # Get all permissions
    permissions = ac.get_user_permissions("testuser")
    print("User permissions:", permissions)
