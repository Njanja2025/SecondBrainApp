"""
Input/Output manager for handling user interactions and display.
Manages text input, voice input, and output display.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class IOConfig:
    """Configuration for input/output handling."""
    input_type: str  # text, voice, file
    output_type: str  # text, voice, file
    input_format: str = "plain"
    output_format: str = "plain"
    voice_language: str = "en-US"
    voice_rate: float = 1.0
    voice_volume: float = 1.0
    max_input_length: int = 1000
    max_output_length: int = 1000

class IOManager:
    """Manages user input and output display."""
    
    def __init__(self, config_dir: str = "config/io"):
        """Initialize the I/O manager.
        
        Args:
            config_dir: Directory to store I/O configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
    
    def _setup_logging(self):
        """Set up logging for the I/O manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load I/O configurations."""
        try:
            config_file = self.config_dir / "io_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: IOConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("I/O configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load I/O configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save I/O configurations."""
        try:
            config_file = self.config_dir / "io_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save I/O configurations: {str(e)}")
    
    def create_config(self, name: str, config: IOConfig) -> bool:
        """Create a new I/O configuration.
        
        Args:
            name: Configuration name
            config: I/O configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if name in self.configs:
                logger.error(f"Configuration {name} already exists")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Created I/O configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create I/O configuration {name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: IOConfig) -> bool:
        """Update an existing I/O configuration.
        
        Args:
            name: Configuration name
            config: New I/O configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated I/O configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update I/O configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete an I/O configuration.
        
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
            
            logger.info(f"Deleted I/O configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete I/O configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[IOConfig]:
        """Get I/O configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            I/O configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all I/O configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def process_input(self, config_name: str, input_data: Union[str, bytes]) -> Optional[Any]:
        """Process user input.
        
        Args:
            config_name: Configuration name
            input_data: Input data
            
        Returns:
            Processed input if successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None
            
            if config.input_type == "text":
                return self._process_text_input(input_data, config)
            elif config.input_type == "voice":
                return self._process_voice_input(input_data, config)
            elif config.input_type == "file":
                return self._process_file_input(input_data, config)
            else:
                logger.error(f"Unsupported input type: {config.input_type}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to process input: {str(e)}")
            return None
    
    def _process_text_input(self, input_data: str, config: IOConfig) -> Optional[str]:
        """Process text input.
        
        Args:
            input_data: Text input
            config: I/O configuration
            
        Returns:
            Processed text if successful
        """
        try:
            if len(input_data) > config.max_input_length:
                logger.error("Input exceeds maximum length")
                return None
            
            # Process text based on format
            if config.input_format == "plain":
                return input_data.strip()
            elif config.input_format == "markdown":
                # Add markdown processing
                return input_data.strip()
            else:
                logger.error(f"Unsupported input format: {config.input_format}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to process text input: {str(e)}")
            return None
    
    def _process_voice_input(self, input_data: bytes, config: IOConfig) -> Optional[str]:
        """Process voice input.
        
        Args:
            input_data: Voice input
            config: I/O configuration
            
        Returns:
            Transcribed text if successful
        """
        try:
            # Add voice processing logic
            return "Transcribed text"
            
        except Exception as e:
            logger.error(f"Failed to process voice input: {str(e)}")
            return None
    
    def _process_file_input(self, input_data: bytes, config: IOConfig) -> Optional[Any]:
        """Process file input.
        
        Args:
            input_data: File input
            config: I/O configuration
            
        Returns:
            Processed file content if successful
        """
        try:
            # Add file processing logic
            return "File content"
            
        except Exception as e:
            logger.error(f"Failed to process file input: {str(e)}")
            return None
    
    def format_output(self, config_name: str, output_data: Any) -> Optional[Union[str, bytes]]:
        """Format output for display.
        
        Args:
            config_name: Configuration name
            output_data: Output data
            
        Returns:
            Formatted output if successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None
            
            if config.output_type == "text":
                return self._format_text_output(output_data, config)
            elif config.output_type == "voice":
                return self._format_voice_output(output_data, config)
            elif config.output_type == "file":
                return self._format_file_output(output_data, config)
            else:
                logger.error(f"Unsupported output type: {config.output_type}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to format output: {str(e)}")
            return None
    
    def _format_text_output(self, output_data: Any, config: IOConfig) -> Optional[str]:
        """Format text output.
        
        Args:
            output_data: Output data
            config: I/O configuration
            
        Returns:
            Formatted text if successful
        """
        try:
            output_str = str(output_data)
            
            if len(output_str) > config.max_output_length:
                logger.error("Output exceeds maximum length")
                return None
            
            # Format text based on format
            if config.output_format == "plain":
                return output_str
            elif config.output_format == "markdown":
                # Add markdown formatting
                return output_str
            else:
                logger.error(f"Unsupported output format: {config.output_format}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to format text output: {str(e)}")
            return None
    
    def _format_voice_output(self, output_data: Any, config: IOConfig) -> Optional[bytes]:
        """Format voice output.
        
        Args:
            output_data: Output data
            config: I/O configuration
            
        Returns:
            Formatted voice data if successful
        """
        try:
            # Add voice formatting logic
            return b"Voice data"
            
        except Exception as e:
            logger.error(f"Failed to format voice output: {str(e)}")
            return None
    
    def _format_file_output(self, output_data: Any, config: IOConfig) -> Optional[bytes]:
        """Format file output.
        
        Args:
            output_data: Output data
            config: I/O configuration
            
        Returns:
            Formatted file data if successful
        """
        try:
            # Add file formatting logic
            return b"File data"
            
        except Exception as e:
            logger.error(f"Failed to format file output: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    manager = IOManager()
    
    # Create I/O configuration
    config = IOConfig(
        input_type="text",
        output_type="text",
        input_format="markdown",
        output_format="markdown"
    )
    manager.create_config("default", config)
    
    # Process input
    input_data = "# Hello, World!"
    processed_input = manager.process_input("default", input_data)
    
    # Format output
    output_data = "## Response"
    formatted_output = manager.format_output("default", output_data) 