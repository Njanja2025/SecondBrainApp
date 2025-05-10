"""
Service manager for handling third-party integrations.
Manages connections, authentication, and data exchange with external services.
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for a third-party service."""
    name: str
    api_key: str
    api_secret: Optional[str] = None
    base_url: str
    timeout: int = 30
    retry_count: int = 3
    rate_limit: int = 100
    rate_period: int = 60

class ServiceManager:
    """Manages third-party service integrations."""
    
    def __init__(self, config_dir: str = "config/integration"):
        """Initialize the service manager.
        
        Args:
            config_dir: Directory to store service configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_services()
    
    def _setup_logging(self):
        """Set up logging for the service manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_services(self):
        """Load service configurations."""
        try:
            config_file = self.config_dir / "services.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.services = {name: ServiceConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.services = {}
                self._save_services()
            
            logger.info("Service configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load service configurations: {str(e)}")
            raise
    
    def _save_services(self):
        """Save service configurations."""
        try:
            config_file = self.config_dir / "services.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.services.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save service configurations: {str(e)}")
    
    def add_service(self, config: ServiceConfig) -> bool:
        """Add a new service configuration.
        
        Args:
            config: Service configuration
            
        Returns:
            bool: True if service was added successfully
        """
        try:
            if config.name in self.services:
                logger.error(f"Service {config.name} already exists")
                return False
            
            self.services[config.name] = config
            self._save_services()
            
            logger.info(f"Added service configuration for {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add service {config.name}: {str(e)}")
            return False
    
    def remove_service(self, name: str) -> bool:
        """Remove a service configuration.
        
        Args:
            name: Service name
            
        Returns:
            bool: True if service was removed successfully
        """
        try:
            if name not in self.services:
                logger.error(f"Service {name} not found")
                return False
            
            del self.services[name]
            self._save_services()
            
            logger.info(f"Removed service configuration for {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove service {name}: {str(e)}")
            return False
    
    def get_service(self, name: str) -> Optional[ServiceConfig]:
        """Get service configuration.
        
        Args:
            name: Service name
            
        Returns:
            Service configuration if found
        """
        return self.services.get(name)
    
    def list_services(self) -> List[str]:
        """List all configured services.
        
        Returns:
            List of service names
        """
        return list(self.services.keys())
    
    def make_request(self, service_name: str, endpoint: str, method: str = "GET",
                    data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make a request to a service.
        
        Args:
            service_name: Name of the service
            endpoint: API endpoint
            method: HTTP method
            data: Request data
            
        Returns:
            Response data if successful
        """
        try:
            service = self.get_service(service_name)
            if not service:
                logger.error(f"Service {service_name} not found")
                return None
            
            url = f"{service.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            headers = {
                "Authorization": f"Bearer {service.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=service.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {service_name} failed: {str(e)}")
            return None
    
    def validate_service(self, name: str) -> bool:
        """Validate service configuration and connection.
        
        Args:
            name: Service name
            
        Returns:
            bool: True if service is valid and connected
        """
        try:
            service = self.get_service(name)
            if not service:
                logger.error(f"Service {name} not found")
                return False
            
            # Make a test request
            response = self.make_request(name, "health")
            if not response:
                return False
            
            logger.info(f"Service {name} is valid and connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate service {name}: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    manager = ServiceManager()
    
    # Add a service
    config = ServiceConfig(
        name="example_service",
        api_key="test_key",
        base_url="https://api.example.com"
    )
    manager.add_service(config)
    
    # Make a request
    response = manager.make_request(
        service_name="example_service",
        endpoint="data",
        method="GET"
    )
    print("Response:", response) 