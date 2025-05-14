import unittest
import sys
import os
import logging
from unittest.mock import patch, MagicMock
from voice_trigger import VoiceController


class TestVoiceController(unittest.TestCase):
    def setUp(self):
        # Suppress actual voice output during tests
        self.voice_patcher = patch("pyttsx3.init")
        self.mock_voice = self.voice_patcher.start()
        self.mock_engine = MagicMock()
        self.mock_voice.return_value = self.mock_engine

        # Create test instance
        self.controller = VoiceController()

    def tearDown(self):
        self.voice_patcher.stop()

    def test_initialization(self):
        """Test voice controller initialization"""
        self.mock_voice.assert_called_once_with(driverName="nsss")
        self.mock_engine.setProperty.assert_any_call("rate", 180)
        self.mock_engine.setProperty.assert_any_call(
            "voice", "com.apple.speech.synthesis.voice.samantha"
        )

    def test_speak(self):
        """Test basic speech functionality"""
        test_message = "Test message"
        self.controller.speak(test_message)
        self.mock_engine.say.assert_called_with(test_message)
        self.mock_engine.runAndWait.assert_called_once()

    def test_system_status(self):
        """Test system status announcement"""
        with (
            patch("psutil.cpu_percent", return_value=50),
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
        ):

            mock_memory.return_value.percent = 60
            mock_disk.return_value.percent = 70

            self.controller.announce_system_status()
            self.mock_engine.say.assert_called()
            self.mock_engine.runAndWait.assert_called()

    def test_backup_announcements(self):
        """Test backup-related announcements"""
        self.controller.backup_started()
        self.mock_engine.say.assert_called()

        self.controller.backup_progress(50)
        self.mock_engine.say.assert_called_with("Backup progress: 50% complete")

        self.controller.backup_completed()
        self.mock_engine.say.assert_called()

    def test_sync_announcements(self):
        """Test sync-related announcements"""
        self.controller.sync_started()
        self.mock_engine.say.assert_called()

        self.controller.sync_progress(75)
        self.mock_engine.say.assert_called_with("Sync progress: 75% complete")

        self.controller.sync_completed()
        self.mock_engine.say.assert_called()

    def test_error_handling(self):
        """Test error handling and announcements"""
        test_error = "Test error message"
        self.controller.system_error(test_error)
        self.mock_engine.say.assert_called_with(f"Error: {test_error}")

    def test_warning_handling(self):
        """Test warning handling and announcements"""
        test_warning = "Test warning message"
        self.controller.system_warning(test_warning)
        self.mock_engine.say.assert_called_with(f"Warning: {test_warning}")


def run_tests():
    """Run the test suite"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
