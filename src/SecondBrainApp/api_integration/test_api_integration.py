"""
Test cases for API integration module.
Tests API configuration, requests, and responses.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
import aiohttp
import asyncio

from .integrator import APIIntegrator, APIConfig, APILogger

@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary configuration directory."""
    return tmp_path / "config"

@pytest.fixture
def log_dir(tmp_path):
    """Create a temporary log directory."""
    return tmp_path / "logs"

@pytest.fixture
def api_config():
    """Create a sample API configuration."""
    return APIConfig(
        name="test_api",
        base_url="https://api.test.com",
        auth_type="api_key",
        auth_config={
            "api_key": "test_key"
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        description="Test API configuration"
    )

@pytest.fixture
def integrator(config_dir, log_dir):
    """Create an API integrator instance."""
    return APIIntegrator(config_dir=str(config_dir))

class TestAPILogger:
    """Test cases for API logger."""
    
    def test_init(self, log_dir):
        """Test logger initialization."""
        logger = APILogger(log_dir=str(log_dir))
        assert logger.log_dir.exists()
    
    def test_log_request(self, log_dir):
        """Test request logging."""
        logger = APILogger(log_dir=str(log_dir))
        request = {
            "method": "GET",
            "url": "https://api.test.com/users",
            "params": {"limit": 10}
        }
        logger.log_request("test_api", request)
        
        log_file = log_dir / "test_api_requests.json"
        assert log_file.exists()
        
        with open(log_file) as f:
            log_entry = json.loads(f.readline())
            assert "timestamp" in log_entry
            assert log_entry["request"] == request
    
    def test_log_response(self, log_dir):
        """Test response logging."""
        logger = APILogger(log_dir=str(log_dir))
        response = {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "content": {"users": []}
        }
        logger.log_response("test_api", response)
        
        log_file = log_dir / "test_api_responses.json"
        assert log_file.exists()
        
        with open(log_file) as f:
            log_entry = json.loads(f.readline())
            assert "timestamp" in log_entry
            assert log_entry["response"] == response

class TestAPIIntegrator:
    """Test cases for API integrator."""
    
    def test_init(self, integrator, config_dir):
        """Test integrator initialization."""
        assert integrator.config_dir.exists()
        assert integrator.configs == {}
    
    def test_create_config(self, integrator, api_config):
        """Test configuration creation."""
        assert integrator.create_config(api_config)
        assert "test_api" in integrator.configs
        assert integrator.configs["test_api"] == api_config
    
    def test_update_config(self, integrator, api_config):
        """Test configuration update."""
        integrator.create_config(api_config)
        
        updated_config = APIConfig(
            name="test_api",
            base_url="https://api.test.com/v2",
            auth_type="api_key",
            auth_config={"api_key": "new_key"},
            description="Updated test API configuration"
        )
        
        assert integrator.update_config("test_api", updated_config)
        assert integrator.configs["test_api"] == updated_config
    
    def test_delete_config(self, integrator, api_config):
        """Test configuration deletion."""
        integrator.create_config(api_config)
        assert integrator.delete_config("test_api")
        assert "test_api" not in integrator.configs
    
    def test_get_config(self, integrator, api_config):
        """Test configuration retrieval."""
        integrator.create_config(api_config)
        assert integrator.get_config("test_api") == api_config
        assert integrator.get_config("nonexistent") is None
    
    def test_list_configs(self, integrator, api_config):
        """Test configuration listing."""
        integrator.create_config(api_config)
        assert "test_api" in integrator.list_configs()
    
    @patch("requests.Session.request")
    def test_make_request(self, mock_request, integrator, api_config):
        """Test API request."""
        integrator.create_config(api_config)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"users": []}
        mock_request.return_value = mock_response
        
        response = integrator.make_request(
            api_name="test_api",
            method="GET",
            endpoint="/users",
            params={"limit": 10}
        )
        
        assert response == {"users": []}
        mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_async_request(self, integrator, api_config):
        """Test asynchronous API request."""
        integrator.create_config(api_config)
        
        async def mock_request(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = asyncio.coroutine(lambda: {"users": []})
            mock_response.text = asyncio.coroutine(lambda: '{"users": []}')
            mock_response.headers = {}
            return mock_response
        
        with patch("aiohttp.ClientSession.request", side_effect=mock_request):
            response = await integrator.make_async_request(
                api_name="test_api",
                method="GET",
                endpoint="/users",
                params={"limit": 10}
            )
            
            assert response == {"users": []}
    
    @pytest.mark.asyncio
    async def test_close(self, integrator):
        """Test async session closure."""
        integrator.async_session = MagicMock()
        await integrator.close()
        integrator.async_session.close.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__]) 