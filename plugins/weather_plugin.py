"""
Weather Plugin - Weather Information System
Provides weather information through voice commands and API integration.
"""

import logging
import requests
import os
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather data structure."""

    temperature: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    wind_direction: str
    pressure: int
    visibility: int
    cloudiness: int
    timestamp: datetime
    location: str


class WeatherPlugin:
    """Weather information plugin with voice command support."""

    is_plugin = True

    def __init__(self):
        """Initialize the weather plugin."""
        self.name = "Weather Plugin"
        self.version = "1.0.0"
        self.description = "Provides weather information and forecasts"
        self.api_key = None
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self._setup()

    def _setup(self) -> None:
        """Set up the plugin."""
        try:
            load_dotenv()
            self.api_key = os.getenv("OPENWEATHER_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenWeather API key not found in environment variables"
                )
            logger.info(f"Initializing {self.name} v{self.version}")
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {e}")
            raise

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
        }

    def register_commands(self, voice_assistant: Any) -> None:
        """Register voice commands for this plugin."""
        try:
            voice_assistant.register_command("weather", self._handle_weather_command)
            voice_assistant.register_command("forecast", self._handle_forecast_command)
            voice_assistant.register_command(
                "temperature", self._handle_temperature_command
            )
            voice_assistant.register_command("humidity", self._handle_humidity_command)
            voice_assistant.register_command("wind", self._handle_wind_command)
            voice_assistant.register_command("pressure", self._handle_pressure_command)
            voice_assistant.register_command(
                "visibility", self._handle_visibility_command
            )
        except Exception as e:
            logger.error(f"Failed to register commands: {e}")

    def _handle_weather_command(self, location: str = "current") -> str:
        """Handle the 'weather' voice command."""
        try:
            weather_data = self._get_weather(location)
            if weather_data:
                return (
                    f"The weather in {weather_data.location} is {weather_data.description}. "
                    f"Temperature is {weather_data.temperature}°C, feels like {weather_data.feels_like}°C. "
                    f"Humidity is {weather_data.humidity}%, wind speed is {weather_data.wind_speed} m/s "
                    f"from the {weather_data.wind_direction}."
                )
            return f"Sorry, I couldn't get the weather for {location}"
        except Exception as e:
            logger.error(f"Failed to handle weather command: {e}")
            return "Sorry, I encountered an error getting the weather"

    def _handle_forecast_command(self, location: str = "current", days: int = 5) -> str:
        """Handle the 'forecast' voice command."""
        try:
            forecast = self._get_forecast(location, days)
            if forecast:
                response = f"Forecast for {location}:\n"
                for day in forecast:
                    response += (
                        f"{day['date']}: {day['description']}, "
                        f"Temperature: {day['temp']}°C, "
                        f"Humidity: {day['humidity']}%\n"
                    )
                return response
            return f"Sorry, I couldn't get the forecast for {location}"
        except Exception as e:
            logger.error(f"Failed to handle forecast command: {e}")
            return "Sorry, I encountered an error getting the forecast"

    def _handle_temperature_command(self, location: str = "current") -> str:
        """Handle the 'temperature' voice command."""
        try:
            weather_data = self._get_weather(location)
            if weather_data:
                return (
                    f"The temperature in {weather_data.location} is {weather_data.temperature}°C, "
                    f"feels like {weather_data.feels_like}°C"
                )
            return f"Sorry, I couldn't get the temperature for {location}"
        except Exception as e:
            logger.error(f"Failed to handle temperature command: {e}")
            return "Sorry, I encountered an error getting the temperature"

    def _handle_humidity_command(self, location: str = "current") -> str:
        """Handle the 'humidity' voice command."""
        try:
            weather_data = self._get_weather(location)
            if weather_data:
                return f"The humidity in {weather_data.location} is {weather_data.humidity}%"
            return f"Sorry, I couldn't get the humidity for {location}"
        except Exception as e:
            logger.error(f"Failed to handle humidity command: {e}")
            return "Sorry, I encountered an error getting the humidity"

    def _handle_wind_command(self, location: str = "current") -> str:
        """Handle the 'wind' voice command."""
        try:
            weather_data = self._get_weather(location)
            if weather_data:
                return (
                    f"The wind in {weather_data.location} is {weather_data.wind_speed} m/s "
                    f"from the {weather_data.wind_direction}"
                )
            return f"Sorry, I couldn't get the wind information for {location}"
        except Exception as e:
            logger.error(f"Failed to handle wind command: {e}")
            return "Sorry, I encountered an error getting the wind information"

    def _handle_pressure_command(self, location: str = "current") -> str:
        """Handle the 'pressure' voice command."""
        try:
            weather_data = self._get_weather(location)
            if weather_data:
                return f"The atmospheric pressure in {weather_data.location} is {weather_data.pressure} hPa"
            return f"Sorry, I couldn't get the pressure for {location}"
        except Exception as e:
            logger.error(f"Failed to handle pressure command: {e}")
            return "Sorry, I encountered an error getting the pressure"

    def _handle_visibility_command(self, location: str = "current") -> str:
        """Handle the 'visibility' voice command."""
        try:
            weather_data = self._get_weather(location)
            if weather_data:
                return f"The visibility in {weather_data.location} is {weather_data.visibility} meters"
            return f"Sorry, I couldn't get the visibility for {location}"
        except Exception as e:
            logger.error(f"Failed to handle visibility command: {e}")
            return "Sorry, I encountered an error getting the visibility"

    def _get_weather(self, location: str) -> Optional[WeatherData]:
        """Get current weather data."""
        try:
            params = {"q": location, "appid": self.api_key, "units": "metric"}
            response = requests.get(f"{self.base_url}/weather", params=params)
            response.raise_for_status()
            data = response.json()

            return WeatherData(
                temperature=data["main"]["temp"],
                feels_like=data["main"]["feels_like"],
                description=data["weather"][0]["description"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"],
                wind_direction=self._get_wind_direction(data["wind"]["deg"]),
                pressure=data["main"]["pressure"],
                visibility=data["visibility"],
                cloudiness=data["clouds"]["all"],
                timestamp=datetime.fromtimestamp(data["dt"]),
                location=data["name"],
            )
        except Exception as e:
            logger.error(f"Failed to get weather data: {e}")
            return None

    def _get_forecast(
        self, location: str, days: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """Get weather forecast."""
        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8,  # 8 readings per day
            }
            response = requests.get(f"{self.base_url}/forecast", params=params)
            response.raise_for_status()
            data = response.json()

            forecast = []
            for item in data["list"]:
                date = datetime.fromtimestamp(item["dt"])
                if date.hour == 12:  # Get noon forecast for each day
                    forecast.append(
                        {
                            "date": date.strftime("%Y-%m-%d"),
                            "temp": item["main"]["temp"],
                            "description": item["weather"][0]["description"],
                            "humidity": item["main"]["humidity"],
                        }
                    )

            return forecast[:days]
        except Exception as e:
            logger.error(f"Failed to get forecast: {e}")
            return None

    def _get_wind_direction(self, degrees: float) -> str:
        """Convert wind degrees to cardinal direction."""
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]
