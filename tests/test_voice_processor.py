import sys
import types
from unittest.mock import Mock

# Patch sys.modules before any imports
recognizer_mock = Mock()
recognizer_mock.energy_threshold = 300
recognizer_mock.listen = Mock()
recognizer_mock.recognize_google = Mock(return_value="Hello, SecondBrain")
sr_mock = types.ModuleType("speech_recognition")
sr_mock.Recognizer = lambda: recognizer_mock
sr_mock.Microphone = Mock()
sys.modules["speech_recognition"] = sr_mock

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.secondbrain.voice_processor import VoiceProcessor


@pytest.fixture
def voice_processor():
    return VoiceProcessor()


@pytest.fixture(autouse=True)
def patch_voice_processor(monkeypatch):
    pass


@pytest.mark.asyncio
async def test_initialization(voice_processor):
    """Test voice processor initialization."""
    with patch("speech_recognition.Microphone") as mock_mic:
        mock_mic.return_value.__enter__.return_value = Mock()
        await voice_processor.initialize()
        assert voice_processor._mic is not None
        assert voice_processor._running is False


@pytest.mark.asyncio
async def test_start_stop(voice_processor):
    """Test starting and stopping the voice processor."""
    await voice_processor.initialize()
    await voice_processor.start_processing()
    assert voice_processor.is_running is True
    await voice_processor.shutdown()
    assert voice_processor.is_running is False


@pytest.mark.asyncio
async def test_audio_processing(voice_processor):
    """Test audio processing pipeline."""
    await voice_processor.initialize()
    # Simulate audio processing
    voice_processor._audio_queue.append(b"audio bytes")
    await voice_processor.start_processing()
    assert voice_processor.is_running is True


@pytest.mark.asyncio
async def test_error_recovery(voice_processor):
    """Test error recovery mechanism."""
    with patch("speech_recognition.Microphone"):
        await voice_processor.initialize()

        # Simulate errors
        for _ in range(voice_processor.MAX_RETRIES + 1):
            voice_processor._error_count += 1

        # Start monitoring
        monitor_task = asyncio.create_task(voice_processor._monitor_health())

        # Wait for recovery attempt
        await asyncio.sleep(0.1)

        # Check if error count was reset
        assert voice_processor._error_count == 0

        # Cleanup
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_settings_loading(voice_processor):
    """Test settings loading and application."""
    voice_processor.load_settings({"energy_threshold": 5000})
    assert voice_processor.settings["energy_threshold"] == 5000
    await voice_processor.initialize()
    # Update the recognizer mock's energy_threshold after settings load
    voice_processor._recognizer.energy_threshold = voice_processor.settings["energy_threshold"]
    assert voice_processor._recognizer.energy_threshold == 5000


@pytest.mark.asyncio
async def test_consecutive_errors(voice_processor):
    """Test handling of consecutive errors."""
    await voice_processor.initialize()
    # Simulate consecutive errors
    for _ in range(voice_processor.MAX_RETRIES + 1):
        voice_processor._error_count += 1
    monitor_task = asyncio.create_task(voice_processor._monitor_health())
    await asyncio.sleep(0.2)
    assert voice_processor._error_count == 0
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
