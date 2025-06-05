import pytest
from src.secondbrain.system_monitor_plugin import SystemMonitorPlugin
from src.secondbrain.plugins.weather_plugin import WeatherPlugin

# Remove global patching fixture for decrypt_api_key

@pytest.fixture(scope="session")
def system_monitor_plugin():
    return SystemMonitorPlugin()

@pytest.fixture(scope="session")
def weather_plugin():
    return WeatherPlugin()
