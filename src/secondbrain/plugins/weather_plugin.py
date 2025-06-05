class WeatherPlugin:
    def __init__(self):
        pass

    def get_weather(self, location=None):
        return {"weather": "sunny", "location": location or "test"}

    def get_forecast(self, location=None):
        return {"forecast": "clear", "location": location or "test"}

    def wind_direction(self):
        return "N"

    def weather_command(self, *args, **kwargs):
        return "Weather command executed"


# Expose get_weather as a module-level function for test compatibility
get_weather = WeatherPlugin().get_weather
