# Expose the real WeatherPlugin for test compatibility
from plugins.weather_plugin import WeatherPlugin, WeatherData

__all__ = ["WeatherPlugin", "WeatherData"]
