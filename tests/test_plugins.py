"""
Unit tests for plugins.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from plugins.weather_plugin import WeatherPlugin, WeatherData
from plugins.task_plugin import TaskPlugin, Task


@pytest.fixture
def weather_plugin():
    """Create a weather plugin instance for testing."""
    with patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test_key"}):
        return WeatherPlugin()


@pytest.fixture
def task_plugin():
    """Create a task plugin instance for testing."""
    return TaskPlugin()


@pytest.fixture
def mock_weather_data():
    """Create mock weather data for testing."""
    return {
        "main": {"temp": 22.5, "feels_like": 23.0, "humidity": 65, "pressure": 1015},
        "weather": [{"description": "clear sky"}],
        "wind": {"speed": 5.0, "deg": 180},
        "visibility": 10000,
        "clouds": {"all": 0},
        "dt": int(datetime.now().timestamp()),
        "name": "Test City",
    }


@pytest.fixture
def mock_forecast_data():
    """Create mock forecast data for testing."""
    return {
        "list": [
            {
                "dt": int((datetime.now() + timedelta(days=i)).timestamp()),
                "main": {"temp": 22.0 + i, "humidity": 65},
                "weather": [{"description": "clear sky"}],
            }
            for i in range(5)
        ]
    }


class TestWeatherPlugin:
    """Test cases for the weather plugin."""

    def test_initialization(self, weather_plugin):
        """Test plugin initialization."""
        assert weather_plugin.name == "Weather Plugin"
        assert weather_plugin.version == "1.0.0"
        assert weather_plugin.api_key == "test_key"

    @patch("requests.get")
    def test_get_weather(self, mock_get, weather_plugin, mock_weather_data):
        """Test getting weather data."""
        mock_get.return_value.json.return_value = mock_weather_data
        mock_get.return_value.raise_for_status = Mock()

        weather_data = weather_plugin._get_weather("Test City")

        assert isinstance(weather_data, WeatherData)
        assert weather_data.temperature == 22.5
        assert weather_data.feels_like == 23.0
        assert weather_data.description == "clear sky"
        assert weather_data.humidity == 65
        assert weather_data.wind_speed == 5.0
        assert weather_data.location == "Test City"

    @patch("requests.get")
    def test_get_forecast(self, mock_get, weather_plugin, mock_forecast_data):
        """Test getting weather forecast."""
        mock_get.return_value.json.return_value = mock_forecast_data
        mock_get.return_value.raise_for_status = Mock()

        forecast = weather_plugin._get_forecast("Test City", days=3)

        assert len(forecast) == 3
        assert all(isinstance(day, dict) for day in forecast)
        assert all("date" in day for day in forecast)
        assert all("temp" in day for day in forecast)
        assert all("description" in day for day in forecast)

    def test_wind_direction(self, weather_plugin):
        """Test wind direction conversion."""
        assert weather_plugin._get_wind_direction(0) == "N"
        assert weather_plugin._get_wind_direction(90) == "E"
        assert weather_plugin._get_wind_direction(180) == "S"
        assert weather_plugin._get_wind_direction(270) == "W"

    def test_weather_command(self, weather_plugin, mock_weather_data):
        """Test weather command handler."""
        with patch.object(
            weather_plugin,
            "_get_weather",
            return_value=WeatherData(
                temperature=22.5,
                feels_like=23.0,
                description="clear sky",
                humidity=65,
                wind_speed=5.0,
                wind_direction="S",
                pressure=1015,
                visibility=10000,
                cloudiness=0,
                timestamp=datetime.now(),
                location="Test City",
            ),
        ):
            response = weather_plugin._handle_weather_command("Test City")
            assert "Test City" in response
            assert "clear sky" in response
            assert "22.5" in response
            assert "23.0" in response


class TestTaskPlugin:
    """Test cases for the task plugin."""

    def test_initialization(self, task_plugin):
        """Test plugin initialization."""
        assert task_plugin.name == "Task Plugin"
        assert task_plugin.version == "1.0.0"
        assert isinstance(task_plugin.tasks, dict)

    def test_add_task(self, task_plugin):
        """Test adding a task."""
        response = task_plugin._handle_add_task_command(
            title="Test Task",
            description="Test Description",
            priority="high",
            tags=["test", "important"],
        )

        assert "Added task: Test Task" in response
        assert len(task_plugin.tasks) == 1

        task = list(task_plugin.tasks.values())[0]
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == "high"
        assert task.status == "pending"
        assert "test" in task.tags
        assert "important" in task.tags

    def test_list_tasks(self, task_plugin):
        """Test listing tasks."""
        # Add some test tasks
        task_plugin._handle_add_task_command("Task 1", priority="high")
        task_plugin._handle_add_task_command("Task 2", priority="low")

        response = task_plugin._handle_list_tasks_command(status="pending")
        assert "Task 1" in response
        assert "Task 2" in response
        assert "high" in response
        assert "low" in response

    def test_complete_task(self, task_plugin):
        """Test completing a task."""
        # Add a task
        task_plugin._handle_add_task_command("Test Task")
        task_id = list(task_plugin.tasks.keys())[0]

        response = task_plugin._handle_complete_task_command(task_id)
        assert "Completed task: Test Task" in response

        task = task_plugin.tasks[task_id]
        assert task.status == "completed"

    def test_delete_task(self, task_plugin):
        """Test deleting a task."""
        # Add a task
        task_plugin._handle_add_task_command("Test Task")
        task_id = list(task_plugin.tasks.keys())[0]

        response = task_plugin._handle_delete_task_command(task_id)
        assert "Deleted task: Test Task" in response
        assert task_id not in task_plugin.tasks

    def test_update_task(self, task_plugin):
        """Test updating a task."""
        # Add a task
        task_plugin._handle_add_task_command("Test Task")
        task_id = list(task_plugin.tasks.keys())[0]

        response = task_plugin._handle_update_task_command(
            task_id, title="Updated Task", priority="high"
        )
        assert "Updated task: Updated Task" in response

        task = task_plugin.tasks[task_id]
        assert task.title == "Updated Task"
        assert task.priority == "high"

    def test_search_tasks(self, task_plugin):
        """Test searching tasks."""
        # Add some test tasks
        task_plugin._handle_add_task_command("Important Task", tags=["important"])
        task_plugin._handle_add_task_command("Regular Task")

        response = task_plugin._handle_search_tasks_command("important")
        assert "Important Task" in response
        assert "Regular Task" not in response
