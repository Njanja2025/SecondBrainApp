import unittest
import sys
import os
import time
from app_core.voice import VoiceAssistant
from plugins.system_monitor_plugin import SystemMonitorPlugin
import logging
import json
from datetime import datetime

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('launch_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestVoiceAssistantLaunch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        logger.info("Setting up test environment...")
        try:
            cls.assistant = VoiceAssistant()
            cls.system_monitor = SystemMonitorPlugin()
            cls.assistant.register_plugin(cls.system_monitor)
            logger.info("Test environment setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to set up test environment: {str(e)}")
            raise

    def setUp(self):
        """Set up before each test."""
        self.start_time = time.time()
        logger.info(f"\nStarting test: {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test."""
        duration = time.time() - self.start_time
        logger.info(f"Completed test: {self._testMethodName} (Duration: {duration:.2f}s)")

    def test_1_initialization(self):
        """Test basic initialization."""
        logger.info("Testing initialization...")
        
        # Test VoiceAssistant initialization
        self.assertIsNotNone(self.assistant, "VoiceAssistant instance is None")
        self.assertIsNotNone(self.assistant.engine, "Text-to-speech engine is None")
        self.assertIsNotNone(self.assistant.recognizer, "Speech recognizer is None")
        
        # Test engine properties
        self.assertIsNotNone(self.assistant.engine.getProperty('rate'), "Speech rate is None")
        self.assertIsNotNone(self.assistant.engine.getProperty('volume'), "Volume is None")
        
        # Test recognizer properties
        self.assertIsNotNone(self.assistant.recognizer.energy_threshold, "Energy threshold is None")
        self.assertIsNotNone(self.assistant.recognizer.pause_threshold, "Pause threshold is None")
        
        logger.info("Initialization test passed")

    def test_2_voice_commands(self):
        """Test voice command handlers."""
        logger.info("Testing voice commands...")
        
        commands_to_test = {
            "system": "System information",
            "cpu": "CPU usage",
            "memory": "Memory usage",
            "disk": "Disk usage",
            "network": "Network I/O",
            "uptime": "System uptime",
            "metrics": "System metrics",
            "processes": "Running processes",
            "temperature": "System temperature",
            "battery": "Battery status",
            "gpu": "GPU usage"
        }
        
        for cmd, description in commands_to_test.items():
            logger.info(f"Testing {cmd} command ({description})...")
            response = self.assistant.process_command(cmd)
            self.assertIsNotNone(response, f"Response for {cmd} command is None")
            self.assertIsInstance(response, str, f"Response for {cmd} command is not a string")
            logger.info(f"{cmd} command response: {response}")

    def test_3_voice_control(self):
        """Test voice control commands."""
        logger.info("Testing voice control...")
        
        # Test volume control
        volume_levels = [0, 50, 100]
        for level in volume_levels:
            response = self.assistant.process_command("volume", {"number": level})
            self.assertIsNotNone(response)
            self.assertIn(str(level), response)
            logger.info(f"Volume {level}% response: {response}")
        
        # Test mute/unmute
        response = self.assistant.process_command("mute")
        self.assertIsNotNone(response)
        self.assertIn("muted", response.lower())
        logger.info(f"Mute command response: {response}")

        response = self.assistant.process_command("unmute")
        self.assertIsNotNone(response)
        self.assertIn("unmuted", response.lower())
        logger.info(f"Unmute command response: {response}")

        # Test speed control with various values
        speed_values = [0.5, 1.0, 1.5, 2.0]
        for speed in speed_values:
            response = self.assistant.process_command("speed", {"number": speed})
            self.assertIsNotNone(response)
            self.assertIn(str(speed), response)
            logger.info(f"Speed {speed}x response: {response}")

        # Test pitch control with various values
        pitch_values = [0.5, 1.0, 1.5, 2.0]
        for pitch in pitch_values:
            response = self.assistant.process_command("pitch", {"number": pitch})
            self.assertIsNotNone(response)
            self.assertIn(str(pitch), response)
            logger.info(f"Pitch {pitch}x response: {response}")

    def test_4_system_monitor_plugin(self):
        """Test system monitor plugin functionality."""
        logger.info("Testing system monitor plugin...")
        
        # Test plugin registration
        self.assertIn("system", self.assistant.plugins, "System monitor plugin not registered")
        
        # Test plugin info
        plugin_info = self.system_monitor.get_info()
        self.assertIsNotNone(plugin_info, "Plugin info is None")
        self.assertEqual(plugin_info['name'], "System Monitor", "Incorrect plugin name")
        self.assertEqual(plugin_info['version'], "1.0.0", "Incorrect plugin version")
        
        # Test all plugin commands
        commands = [
            "system", "cpu", "memory", "disk", "network",
            "uptime", "metrics", "processes", "temperature",
            "battery", "gpu"
        ]
        
        for cmd in commands:
            logger.info(f"Testing {cmd} command...")
            response = self.system_monitor.commands[cmd]([])
            self.assertIsNotNone(response, f"Response for {cmd} command is None")
            self.assertIsInstance(response, str, f"Response for {cmd} command is not a string")
            logger.info(f"{cmd} command response: {response}")

    def test_5_error_handling(self):
        """Test error handling."""
        logger.info("Testing error handling...")
        
        # Test invalid commands
        invalid_commands = ["invalid_command", "nonexistent", "wrong_command"]
        for cmd in invalid_commands:
            response = self.assistant.process_command(cmd)
            self.assertIsNone(response, f"Invalid command '{cmd}' should return None")
        
        # Test invalid arguments
        invalid_args = [
            ("speed", {"number": "invalid"}),
            ("volume", {"number": -1}),
            ("pitch", {"number": 3.0}),
            ("speed", {}),
            ("volume", None)
        ]
        
        for cmd, args in invalid_args:
            response = self.assistant.process_command(cmd, args)
            self.assertIsNotNone(response, f"Error response for {cmd} is None")
            self.assertIn("Error", response, f"Error message not found in response for {cmd}")
            logger.info(f"{cmd} with invalid args response: {response}")
        
        logger.info("Error handling test passed")

    def test_6_plugin_management(self):
        """Test plugin management."""
        logger.info("Testing plugin management...")
        
        # Test plugin info
        info = self.assistant.get_plugin_info()
        self.assertIsNotNone(info, "Plugin info is None")
        self.assertTrue(len(info) > 0, "No plugins found")
        
        # Test plugin commands
        commands = self.assistant.plugins["system"].get_commands()
        self.assertIsNotNone(commands, "Plugin commands are None")
        self.assertTrue(len(commands) > 0, "No commands found for system plugin")
        
        # Test plugin status
        status = self.assistant._handle_status_command()
        self.assertIsNotNone(status, "Status command response is None")
        self.assertIn("System Monitor", status, "System Monitor not found in status")
        
        logger.info("Plugin management test passed")

    def test_7_performance(self):
        """Test performance of critical operations."""
        logger.info("Testing performance...")
        
        # Test command processing speed
        start_time = time.time()
        for _ in range(10):
            self.assistant.process_command("system")
        duration = time.time() - start_time
        self.assertLess(duration, 5.0, "Command processing too slow")
        logger.info(f"Command processing speed: {duration/10:.3f}s per command")
        
        # Test plugin response time
        start_time = time.time()
        for _ in range(10):
            self.system_monitor.commands["cpu"]([])
        duration = time.time() - start_time
        self.assertLess(duration, 2.0, "Plugin response too slow")
        logger.info(f"Plugin response time: {duration/10:.3f}s per command")

def run_tests():
    """Run all tests and report results."""
    logger.info("Starting pre-launch tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVoiceAssistantLaunch)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "successful": result.wasSuccessful(),
        "failures_details": [str(f) for f in result.failures],
        "errors_details": [str(e) for e in result.errors]
    }
    
    # Save report to file
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Log summary
    logger.info("\nTest Results Summary:")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        logger.info("All tests passed! System is ready for launch.")
        return True
    else:
        logger.error("Some tests failed. Please check test_report.json for details.")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 