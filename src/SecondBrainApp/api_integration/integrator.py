"""
API Integrator for handling external API integrations.
Manages API connections, requests, and responses.
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import asyncio
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuration for API integration."""
    name: str
    base_url: str
    auth_type: str  # basic, oauth2, api_key, none
    auth_config: Dict[str, Any]
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds
    retry_count: int = 3
    retry_delay: int = 1  # seconds
    headers: Dict[str, str] = None
    metadata: Dict[str, Any] = None
    description: str = None

class APILogger:
    """Logs API requests and responses."""
    
    def __init__(self, log_dir: str = "logs/api"):
        """Initialize the API logger.
        
        Args:
            log_dir: Directory to store API logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging for API requests."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def log_request(self, api_name: str, request: Dict[str, Any]):
        """Log an API request.
        
        Args:
            api_name: Name of the API
            request: Request details
        """
        try:
            log_file = self.log_dir / f"{api_name}_requests.json"
            timestamp = datetime.now().isoformat()
            
            log_entry = {
                "timestamp": timestamp,
                "request": request
            }
            
            with open(log_file, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
            
            logger.info(f"Logged request for API {api_name}")
            
        except Exception as e:
            logger.error(f"Failed to log request for API {api_name}: {str(e)}")
    
    def log_response(self, api_name: str, response: Dict[str, Any]):
        """Log an API response.
        
        Args:
            api_name: Name of the API
            response: Response details
        """
        try:
            log_file = self.log_dir / f"{api_name}_responses.json"
            timestamp = datetime.now().isoformat()
            
            log_entry = {
                "timestamp": timestamp,
                "response": response
            }
            
            with open(log_file, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
            
            logger.info(f"Logged response for API {api_name}")
            
        except Exception as e:
            logger.error(f"Failed to log response for API {api_name}: {str(e)}")

class APIIntegrator:
    """Manages API integrations and requests."""
    
    def __init__(self, config_dir: str = "config/api"):
        """Initialize the API integrator.
        
        Args:
            config_dir: Directory to store API configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self.logger = APILogger()
        self.session = requests.Session()
        self.async_session = None
    
    def _setup_logging(self):
        """Set up logging for the API integrator."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load API configurations."""
        try:
            config_file = self.config_dir / "api_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: APIConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("API configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load API configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save API configurations."""
        try:
            config_file = self.config_dir / "api_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save API configurations: {str(e)}")
    
    def create_config(self, config: APIConfig) -> bool:
        """Create a new API configuration.
        
        Args:
            config: API configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created API configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create API configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: APIConfig) -> bool:
        """Update an existing API configuration.
        
        Args:
            name: Configuration name
            config: New API configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated API configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update API configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete an API configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            bool: True if configuration was deleted successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            del self.configs[name]
            self._save_configs()
            
            logger.info(f"Deleted API configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete API configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[APIConfig]:
        """Get API configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            API configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all API configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    @sleep_and_retry
    @limits(calls=100, period=60)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def make_request(self, api_name: str, method: str, endpoint: str,
                    params: Optional[Dict[str, Any]] = None,
                    data: Optional[Dict[str, Any]] = None,
                    json_data: Optional[Dict[str, Any]] = None,
                    headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Make an API request.
        
        Args:
            api_name: API configuration name
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Request headers
            
        Returns:
            API response if successful
        """
        try:
            config = self.get_config(api_name)
            if not config:
                logger.error(f"Configuration {api_name} not found")
                return None
            
            # Prepare request
            url = f"{config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            request_headers = config.headers or {}
            if headers:
                request_headers.update(headers)
            
            # Log request
            request_log = {
                "method": method,
                "url": url,
                "params": params,
                "data": data,
                "json": json_data,
                "headers": request_headers
            }
            self.logger.log_request(api_name, request_log)
            
            # Make request
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=config.timeout
            )
            
            # Log response
            response_log = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text
            }
            self.logger.log_response(api_name, response_log)
            
            # Handle response
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to make request to API {api_name}: {str(e)}")
            return None
    
    async def make_async_request(self, api_name: str, method: str, endpoint: str,
                               params: Optional[Dict[str, Any]] = None,
                               data: Optional[Dict[str, Any]] = None,
                               json_data: Optional[Dict[str, Any]] = None,
                               headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Make an asynchronous API request.
        
        Args:
            api_name: API configuration name
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Request headers
            
        Returns:
            API response if successful
        """
        try:
            config = self.get_config(api_name)
            if not config:
                logger.error(f"Configuration {api_name} not found")
                return None
            
            # Initialize async session if needed
            if not self.async_session:
                self.async_session = aiohttp.ClientSession()
            
            # Prepare request
            url = f"{config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            request_headers = config.headers or {}
            if headers:
                request_headers.update(headers)
            
            # Log request
            request_log = {
                "method": method,
                "url": url,
                "params": params,
                "data": data,
                "json": json_data,
                "headers": request_headers
            }
            self.logger.log_request(api_name, request_log)
            
            # Make request
            async with self.async_session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=config.timeout
            ) as response:
                # Log response
                response_log = {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "content": await response.text()
                }
                self.logger.log_response(api_name, response_log)
                
                # Handle response
                response.raise_for_status()
                return await response.json()
            
        except Exception as e:
            logger.error(f"Failed to make async request to API {api_name}: {str(e)}")
            return None
    
    async def close(self):
        """Close the async session."""
        if self.async_session:
            await self.async_session.close()

# Example usage
if __name__ == "__main__":
    integrator = APIIntegrator()
    
    # Create API configuration
    config = APIConfig(
        name="example_api",
        base_url="https://api.example.com",
        auth_type="api_key",
        auth_config={
            "api_key": "your_api_key"
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        description="Example API integration"
    )
    integrator.create_config(config)
    
    # Make request
    response = integrator.make_request(
        api_name="example_api",
        method="GET",
        endpoint="/users",
        params={"limit": 10}
    )
    print(response)
    
    # Make async request
    async def main():
        response = await integrator.make_async_request(
            api_name="example_api",
            method="GET",
            endpoint="/users",
            params={"limit": 10}
        )
        print(response)
        await integrator.close()
    
    asyncio.run(main()) 