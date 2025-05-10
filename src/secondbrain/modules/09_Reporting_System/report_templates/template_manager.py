"""
Template manager for handling report templates.
Manages template definitions, layouts, and formatting.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
import markdown
import pdfkit

logger = logging.getLogger(__name__)

@dataclass
class TemplateConfig:
    """Configuration for report templates."""
    name: str
    format: str  # html, pdf, markdown, json
    template_file: str
    sections: List[Dict[str, Any]]
    styles: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    description: str = None

class TemplateManager:
    """Manages report templates and formatting."""
    
    def __init__(self, config_dir: str = "config/templates"):
        """Initialize the template manager.
        
        Args:
            config_dir: Directory to store template configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._setup_templates()
        self._load_configs()
    
    def _setup_logging(self):
        """Set up logging for the template manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_templates(self):
        """Set up template environment."""
        try:
            template_dir = Path("templates")
            template_dir.mkdir(exist_ok=True)
            
            self.env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True
            )
            
            logger.info("Template environment setup completed")
            
        except Exception as e:
            logger.error(f"Failed to set up template environment: {str(e)}")
            raise
    
    def _load_configs(self):
        """Load template configurations."""
        try:
            config_file = self.config_dir / "template_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: TemplateConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Template configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load template configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save template configurations."""
        try:
            config_file = self.config_dir / "template_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save template configurations: {str(e)}")
    
    def create_config(self, config: TemplateConfig) -> bool:
        """Create a new template configuration.
        
        Args:
            config: Template configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created template configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create template configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: TemplateConfig) -> bool:
        """Update an existing template configuration.
        
        Args:
            name: Configuration name
            config: New template configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated template configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update template configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete a template configuration.
        
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
            
            logger.info(f"Deleted template configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete template configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[TemplateConfig]:
        """Get template configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Template configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all template configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def render_template(self, config_name: str, data: Dict[str, Any]) -> Optional[str]:
        """Render a template with data.
        
        Args:
            config_name: Configuration name
            data: Template data
            
        Returns:
            Rendered template if successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None
            
            # Load template
            template = self.env.get_template(config.template_file)
            
            # Add styles and metadata to data
            data["styles"] = config.styles or {}
            data["metadata"] = config.metadata or {}
            
            # Render template
            rendered = template.render(**data)
            
            # Convert format if needed
            if config.format == "pdf":
                rendered = self._convert_to_pdf(rendered)
            elif config.format == "markdown":
                rendered = self._convert_to_markdown(rendered)
            elif config.format == "json":
                rendered = self._convert_to_json(rendered)
            
            logger.info(f"Rendered template {config_name}")
            return rendered
            
        except Exception as e:
            logger.error(f"Failed to render template {config_name}: {str(e)}")
            return None
    
    def _convert_to_pdf(self, html: str) -> str:
        """Convert HTML to PDF.
        
        Args:
            html: HTML content
            
        Returns:
            PDF content
        """
        try:
            return pdfkit.from_string(html, False)
            
        except Exception as e:
            logger.error(f"Failed to convert to PDF: {str(e)}")
            return html
    
    def _convert_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown.
        
        Args:
            html: HTML content
            
        Returns:
            Markdown content
        """
        try:
            return markdown.markdown(html)
            
        except Exception as e:
            logger.error(f"Failed to convert to Markdown: {str(e)}")
            return html
    
    def _convert_to_json(self, content: str) -> str:
        """Convert content to JSON.
        
        Args:
            content: Content to convert
            
        Returns:
            JSON content
        """
        try:
            return json.dumps({"content": content})
            
        except Exception as e:
            logger.error(f"Failed to convert to JSON: {str(e)}")
            return content

# Example usage
if __name__ == "__main__":
    manager = TemplateManager()
    
    # Create template configuration
    config = TemplateConfig(
        name="user_report",
        format="html",
        template_file="user_report.html",
        sections=[
            {
                "name": "header",
                "type": "text",
                "content": "User Report"
            },
            {
                "name": "user_info",
                "type": "table",
                "fields": ["username", "email", "created_at"]
            },
            {
                "name": "activity_summary",
                "type": "chart",
                "chart_type": "bar"
            }
        ],
        styles={
            "header": {
                "font_size": "24px",
                "color": "#333"
            },
            "table": {
                "border": "1px solid #ddd",
                "padding": "8px"
            }
        },
        description="User activity report template"
    )
    manager.create_config(config)
    
    # Render template
    data = {
        "user": {
            "username": "john_doe",
            "email": "john@example.com",
            "created_at": "2024-01-01"
        },
        "activity": {
            "logins": 10,
            "notes": 5,
            "tasks": 3
        }
    }
    rendered = manager.render_template("user_report", data)
    print(rendered) 