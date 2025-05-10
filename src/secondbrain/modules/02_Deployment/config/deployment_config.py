"""
Deployment configuration manager for SecondBrain application.
Handles environment-specific configurations and deployment settings.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentConfig:
    """Represents environment-specific configuration."""
    name: str
    settings: Dict[str, Any]
    credentials: Dict[str, str]
    services: Dict[str, Dict[str, Any]]

class DeploymentConfig:
    """Manages deployment configurations and environment settings."""
    
    def __init__(self, config_dir: str = "config/deployment"):
        """Initialize the deployment configuration manager.
        
        Args:
            config_dir: Directory to store deployment configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_config()
    
    def _setup_logging(self):
        """Set up logging for the configuration manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_config(self):
        """Load deployment configuration."""
        try:
            config_file = self.config_dir / "deployment.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Default configuration
                self.config = {
                    "environments": ["dev", "staging", "prod"],
                    "default_environment": "dev",
                    "deployment_timeout": 300,
                    "max_retries": 3,
                    "backup_enabled": True,
                    "monitoring_enabled": True
                }
                
                # Save default configuration
                with open(config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
            
            logger.info("Deployment configuration loaded")
            
        except Exception as e:
            logger.error(f"Failed to load deployment configuration: {str(e)}")
            raise
    
    def get_environment_config(self, environment: str) -> Optional[EnvironmentConfig]:
        """Get configuration for a specific environment.
        
        Args:
            environment: Environment name
            
        Returns:
            Environment configuration if found, None otherwise
        """
        try:
            if environment not in self.config["environments"]:
                logger.error(f"Invalid environment: {environment}")
                return None
            
            env_dir = self.config_dir / "environments" / environment
            env_dir.mkdir(parents=True, exist_ok=True)
            
            # Load environment settings
            settings_file = env_dir / "settings.yaml"
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = yaml.safe_load(f)
            else:
                settings = {}
            
            # Load environment credentials
            credentials_file = env_dir / "credentials.yaml"
            if credentials_file.exists():
                with open(credentials_file, 'r') as f:
                    credentials = yaml.safe_load(f)
            else:
                credentials = {}
            
            # Load environment services
            services_file = env_dir / "services.yaml"
            if services_file.exists():
                with open(services_file, 'r') as f:
                    services = yaml.safe_load(f)
            else:
                services = {}
            
            return EnvironmentConfig(
                name=environment,
                settings=settings,
                credentials=credentials,
                services=services
            )
            
        except Exception as e:
            logger.error(f"Failed to get environment configuration for {environment}: {str(e)}")
            return None
    
    def update_environment_config(self, environment: str, settings: Dict[str, Any],
                                credentials: Dict[str, str], services: Dict[str, Dict[str, Any]]) -> bool:
        """Update configuration for a specific environment.
        
        Args:
            environment: Environment name
            settings: Environment settings
            credentials: Environment credentials
            services: Environment services
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if environment not in self.config["environments"]:
                logger.error(f"Invalid environment: {environment}")
                return False
            
            env_dir = self.config_dir / "environments" / environment
            env_dir.mkdir(parents=True, exist_ok=True)
            
            # Update environment settings
            with open(env_dir / "settings.yaml", 'w') as f:
                yaml.dump(settings, f)
            
            # Update environment credentials
            with open(env_dir / "credentials.yaml", 'w') as f:
                yaml.dump(credentials, f)
            
            # Update environment services
            with open(env_dir / "services.yaml", 'w') as f:
                yaml.dump(services, f)
            
            logger.info(f"Updated configuration for environment {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update environment configuration for {environment}: {str(e)}")
            return False
    
    def get_deployment_settings(self) -> Dict[str, Any]:
        """Get deployment settings.
        
        Returns:
            Dictionary of deployment settings
        """
        return self.config
    
    def update_deployment_settings(self, settings: Dict[str, Any]) -> bool:
        """Update deployment settings.
        
        Args:
            settings: New deployment settings
            
        Returns:
            bool: True if settings were updated successfully
        """
        try:
            self.config.update(settings)
            
            with open(self.config_dir / "deployment.json", 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("Updated deployment settings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update deployment settings: {str(e)}")
            return False
    
    def validate_environment(self, environment: str) -> bool:
        """Validate environment configuration.
        
        Args:
            environment: Environment name to validate
            
        Returns:
            bool: True if environment configuration is valid
        """
        try:
            config = self.get_environment_config(environment)
            if not config:
                return False
            
            # Validate required settings
            required_settings = ["app_name", "version", "deployment_path"]
            for setting in required_settings:
                if setting not in config.settings:
                    logger.error(f"Missing required setting: {setting}")
                    return False
            
            # Validate required credentials
            required_credentials = ["api_key", "secret_key"]
            for credential in required_credentials:
                if credential not in config.credentials:
                    logger.error(f"Missing required credential: {credential}")
                    return False
            
            # Validate required services
            required_services = ["database", "cache", "storage"]
            for service in required_services:
                if service not in config.services:
                    logger.error(f"Missing required service: {service}")
                    return False
            
            logger.info(f"Environment {environment} configuration is valid")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate environment {environment}: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    config = DeploymentConfig()
    
    # Get environment configuration
    env_config = config.get_environment_config("dev")
    
    # Update environment configuration
    config.update_environment_config(
        environment="dev",
        settings={
            "app_name": "SecondBrain",
            "version": "1.0.0",
            "deployment_path": "/opt/secondbrain"
        },
        credentials={
            "api_key": "test_key",
            "secret_key": "test_secret"
        },
        services={
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "cache": {
                "host": "localhost",
                "port": 6379
            },
            "storage": {
                "path": "/data/storage"
            }
        }
    )
    
    # Validate environment
    is_valid = config.validate_environment("dev")
    print("Environment is valid:", is_valid) 