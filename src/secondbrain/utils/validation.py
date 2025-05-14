"""
Validation utilities for SecondBrain
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class Validator:
    """Validation utilities for SecondBrain."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address.

        Args:
            email: Email address to validate

        Returns:
            True if email is valid
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, List[str]]:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            issues.append("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            issues.append("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")

        return len(issues) == 0, issues

    @staticmethod
    def validate_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
        """
        Validate date string.

        Args:
            date_str: Date string to validate
            format: Expected date format

        Returns:
            True if date is valid
        """
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        pattern = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate configuration dictionary.

        Args:
            config: Configuration to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        required_fields = {
            "app": ["name", "version", "environment"],
            "gui": ["enabled", "theme", "window_size"],
            "voice": ["enabled", "language"],
            "memory": ["max_size_mb", "backup_interval_minutes"],
            "security": ["encryption_enabled", "key_rotation_days"],
        }

        # Check required sections
        for section, fields in required_fields.items():
            if section not in config:
                issues.append(f"Missing required section: {section}")
                continue

            # Check required fields in section
            for field in fields:
                if field not in config[section]:
                    issues.append(f"Missing required field: {section}.{field}")

        # Validate specific fields
        if "gui" in config:
            if not isinstance(config["gui"].get("enabled"), bool):
                issues.append("gui.enabled must be boolean")
            if not isinstance(config["gui"].get("window_size"), list):
                issues.append("gui.window_size must be a list")

        if "memory" in config:
            if not isinstance(config["memory"].get("max_size_mb"), (int, float)):
                issues.append("memory.max_size_mb must be a number")

        return len(issues) == 0, issues

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Remove potentially dangerous characters
        text = re.sub(r"[<>]", "", text)
        # Remove multiple spaces
        text = re.sub(r"\s+", " ", text)
        # Trim whitespace
        return text.strip()

    @staticmethod
    def validate_json_schema(
        data: Dict[str, Any], schema: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate data against JSON schema.

        Args:
            data: Data to validate
            schema: JSON schema to validate against

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        def validate_type(value: Any, expected_type: str) -> bool:
            if expected_type == "string":
                return isinstance(value, str)
            elif expected_type == "number":
                return isinstance(value, (int, float))
            elif expected_type == "boolean":
                return isinstance(value, bool)
            elif expected_type == "array":
                return isinstance(value, list)
            elif expected_type == "object":
                return isinstance(value, dict)
            return False

        def validate_object(obj: Dict[str, Any], schema_obj: Dict[str, Any]) -> None:
            if "properties" in schema_obj:
                for prop, prop_schema in schema_obj["properties"].items():
                    if prop in obj:
                        if not validate_type(obj[prop], prop_schema["type"]):
                            issues.append(f"Invalid type for {prop}")
                    elif prop_schema.get("required", False):
                        issues.append(f"Missing required property: {prop}")

        validate_object(data, schema)
        return len(issues) == 0, issues
