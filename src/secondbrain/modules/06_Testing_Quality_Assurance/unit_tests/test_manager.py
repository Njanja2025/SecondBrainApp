"""
Test manager for handling unit tests.
Manages test execution, assertions, and test reporting.
"""

import os
import json
import logging
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Configuration for unit tests."""
    name: str
    test_cases: List[Dict[str, Any]]
    timeout: int = 30
    retry_count: int = 3
    parallel: bool = False
    coverage_threshold: float = 80.0

class TestManager:
    """Manages unit test execution and reporting."""
    
    def __init__(self, config_dir: str = "config/tests"):
        """Initialize the test manager.
        
        Args:
            config_dir: Directory to store test configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
    
    def _setup_logging(self):
        """Set up logging for the test manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load test configurations."""
        try:
            config_file = self.config_dir / "test_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: TestConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Test configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load test configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save test configurations."""
        try:
            config_file = self.config_dir / "test_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save test configurations: {str(e)}")
    
    def create_config(self, config: TestConfig) -> bool:
        """Create a new test configuration.
        
        Args:
            config: Test configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created test configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create test configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: TestConfig) -> bool:
        """Update an existing test configuration.
        
        Args:
            name: Configuration name
            config: New test configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated test configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update test configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete a test configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            bool: True if configuration was deleted successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            del self.configs[name]
            self._save_configs()
            
            logger.info(f"Deleted test configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete test configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[TestConfig]:
        """Get test configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Test configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all test configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def run_tests(self, config_name: str) -> Dict[str, Any]:
        """Run unit tests.
        
        Args:
            config_name: Configuration name
            
        Returns:
            Test results
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return {"success": False, "error": "Configuration not found"}
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "config": config_name,
                "test_cases": [],
                "summary": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0
                }
            }
            
            # Create test suite
            suite = unittest.TestSuite()
            
            # Add test cases
            for test_case in config.test_cases:
                test_class = self._create_test_class(test_case)
                suite.addTest(test_class())
            
            # Run tests
            runner = unittest.TextTestRunner()
            test_results = runner.run(suite)
            
            # Process results
            results["summary"]["total"] = test_results.testsRun
            results["summary"]["failed"] = len(test_results.failures) + len(test_results.errors)
            results["summary"]["skipped"] = len(test_results.skipped)
            results["summary"]["passed"] = results["summary"]["total"] - results["summary"]["failed"] - results["summary"]["skipped"]
            
            # Add detailed results
            for failure in test_results.failures:
                results["test_cases"].append({
                    "name": failure[0]._testMethodName,
                    "status": "failed",
                    "error": failure[1]
                })
            
            for error in test_results.errors:
                results["test_cases"].append({
                    "name": error[0]._testMethodName,
                    "status": "error",
                    "error": error[1]
                })
            
            for test in test_results.testsRun:
                if test not in [f[0] for f in test_results.failures] and test not in [e[0] for e in test_results.errors]:
                    results["test_cases"].append({
                        "name": test._testMethodName,
                        "status": "passed"
                    })
            
            logger.info(f"Ran tests for configuration {config_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to run tests for configuration {config_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_test_class(self, test_case: Dict[str, Any]) -> type:
        """Create a test class from test case configuration.
        
        Args:
            test_case: Test case configuration
            
        Returns:
            Test class
        """
        class TestCase(unittest.TestCase):
            def setUp(self):
                if "setup" in test_case:
                    self.setup_func = test_case["setup"]
                    self.setup_func()
            
            def tearDown(self):
                if "teardown" in test_case:
                    self.teardown_func = test_case["teardown"]
                    self.teardown_func()
            
            def test_case(self):
                if "test" in test_case:
                    self.test_func = test_case["test"]
                    self.test_func()
        
        TestCase.__name__ = f"Test_{test_case['name']}"
        return TestCase
    
    def add_test_case(self, config_name: str, test_case: Dict[str, Any]) -> bool:
        """Add a test case to a configuration.
        
        Args:
            config_name: Configuration name
            test_case: Test case configuration
            
        Returns:
            bool: True if test case was added successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False
            
            config.test_cases.append(test_case)
            self._save_configs()
            
            logger.info(f"Added test case to configuration {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add test case to configuration {config_name}: {str(e)}")
            return False
    
    def remove_test_case(self, config_name: str, test_case_name: str) -> bool:
        """Remove a test case from a configuration.
        
        Args:
            config_name: Configuration name
            test_case_name: Test case name
            
        Returns:
            bool: True if test case was removed successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False
            
            config.test_cases = [tc for tc in config.test_cases if tc.get("name") != test_case_name]
            self._save_configs()
            
            logger.info(f"Removed test case from configuration {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove test case from configuration {config_name}: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    manager = TestManager()
    
    # Create test configuration
    config = TestConfig(
        name="basic_tests",
        test_cases=[
            {
                "name": "test_addition",
                "test": lambda: assertEqual(1 + 1, 2)
            },
            {
                "name": "test_subtraction",
                "test": lambda: assertEqual(2 - 1, 1)
            }
        ]
    )
    manager.create_config(config)
    
    # Run tests
    results = manager.run_tests("basic_tests")
    print("Test results:", results) 