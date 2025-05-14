import pytest
import asyncio
from unittest.mock import Mock, patch
from src.secondbrain.voice_processor import VoiceProcessor


@pytest.fixture
def voice_processor():
    return VoiceProcessor()


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
    with patch("speech_recognition.Microphone"):
        await voice_processor.initialize()
        await voice_processor.start()
        assert voice_processor._running is True
        await voice_processor.shutdown()
        assert voice_processor._running is False


@pytest.mark.asyncio
async def test_audio_processing(voice_processor):
    """Test audio processing pipeline."""
    mock_audio = Mock()
    mock_text = "Hello, SecondBrain"

    with (
        patch("speech_recognition.Microphone"),
        patch.object(
            voice_processor._recognizer, "recognize_google", return_value=mock_text
        ),
    ):
        await voice_processor.initialize()

        # Mock the speech callback
        callback_called = asyncio.Event()
        received_text = None

        async def mock_callback(text):
            nonlocal received_text
            received_text = text
            callback_called.set()

        voice_processor.on_speech = mock_callback

        # Simulate audio processing
        voice_processor._audio_queue.put(mock_audio)
        await voice_processor.start()

        # Wait for processing
        try:
            await asyncio.wait_for(callback_called.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pytest.fail("Speech callback not called")

        assert received_text == mock_text


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
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value='{"energy_threshold": 5000}'),
        patch("speech_recognition.Microphone"),
    ):

        voice_processor.load_settings()
        assert voice_processor.settings["energy_threshold"] == 5000

        await voice_processor.initialize()
        assert voice_processor._recognizer.energy_threshold == 5000


@pytest.mark.asyncio
async def test_consecutive_errors(voice_processor):
    """Test handling of consecutive errors."""
    with (
        patch("speech_recognition.Microphone"),
        patch.object(
            voice_processor._recognizer, "listen", side_effect=Exception("Mock error")
        ),
    ):

        await voice_processor.initialize()
        await voice_processor.start()

        # Wait for error handling
        await asyncio.sleep(0.2)

        # Should have attempted recovery
        assert voice_processor._running is True
