"""
Report generator for handling test reports.
Manages report generation, formatting, and export.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import jinja2
import markdown
import pdfkit

logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    """Configuration for test reports."""
    name: str
    format: str = "html"
    template: str = "default"
    include_metrics: bool = True
    include_summary: bool = True
    include_details: bool = True
    export_path: str = "reports"

class ReportGenerator:
    """Manages test report generation and export."""
    
    def __init__(self, config_dir: str = "config/test_reports"):
        """Initialize the report generator.
        
        Args:
            config_dir: Directory to store report configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_configs()
        self._setup_templates()
    
    def _setup_logging(self):
        """Set up logging for the report generator."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configs(self):
        """Load report configurations."""
        try:
            config_file = self.config_dir / "report_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: ReportConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Report configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load report configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save report configurations."""
        try:
            config_file = self.config_dir / "report_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save report configurations: {str(e)}")
    
    def _setup_templates(self):
        """Set up Jinja2 templates."""
        try:
            template_dir = Path(__file__).parent / "templates"
            self.env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(template_dir)),
                autoescape=True
            )
            
        except Exception as e:
            logger.error(f"Failed to set up templates: {str(e)}")
            raise
    
    def create_config(self, config: ReportConfig) -> bool:
        """Create a new report configuration.
        
        Args:
            config: Report configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created report configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create report configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: ReportConfig) -> bool:
        """Update an existing report configuration.
        
        Args:
            name: Configuration name
            config: New report configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated report configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update report configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete a report configuration.
        
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
            
            logger.info(f"Deleted report configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete report configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[ReportConfig]:
        """Get report configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Report configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all report configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def generate_report(self, config_name: str, test_results: Dict[str, Any]) -> Optional[str]:
        """Generate a test report.
        
        Args:
            config_name: Configuration name
            test_results: Test results to include in the report
            
        Returns:
            Path to the generated report if successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None
            
            # Prepare report data
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "config": config_name,
                "test_results": test_results,
                "summary": test_results.get("summary", {}),
                "metrics": test_results.get("metrics", {}),
                "benchmarks": test_results.get("benchmarks", [])
            }
            
            # Generate report content
            template = self.env.get_template(f"{config.template}.{config.format}")
            content = template.render(**report_data)
            
            # Create export directory
            export_dir = Path(config.export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate report file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = export_dir / f"report_{config_name}_{timestamp}.{config.format}"
            
            if config.format == "html":
                with open(report_file, 'w') as f:
                    f.write(content)
            elif config.format == "md":
                with open(report_file, 'w') as f:
                    f.write(content)
            elif config.format == "pdf":
                html_content = markdown.markdown(content)
                pdfkit.from_string(html_content, str(report_file))
            else:
                logger.error(f"Unsupported report format: {config.format}")
                return None
            
            logger.info(f"Generated report for configuration {config_name}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"Failed to generate report for configuration {config_name}: {str(e)}")
            return None
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Format metrics for report display.
        
        Args:
            metrics: Raw metrics data
            
        Returns:
            Formatted metrics data
        """
        try:
            formatted = {}
            for metric, values in metrics.items():
                if isinstance(values, list):
                    formatted[metric] = {
                        "min": min(v["value"] for v in values),
                        "max": max(v["value"] for v in values),
                        "avg": sum(v["value"] for v in values) / len(values)
                    }
                else:
                    formatted[metric] = values
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to format metrics: {str(e)}")
            return metrics
    
    def _format_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Format summary for report display.
        
        Args:
            summary: Raw summary data
            
        Returns:
            Formatted summary data
        """
        try:
            return {
                "total": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "success_rate": (summary.get("passed", 0) / summary.get("total", 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Failed to format summary: {str(e)}")
            return summary

# Example usage
if __name__ == "__main__":
    generator = ReportGenerator()
    
    # Create report configuration
    config = ReportConfig(
        name="basic_report",
        format="html",
        template="default",
        include_metrics=True,
        include_summary=True,
        include_details=True
    )
    generator.create_config(config)
    
    # Generate report
    test_results = {
        "summary": {
            "total": 10,
            "passed": 8,
            "failed": 2
        },
        "metrics": {
            "cpu_percent": [{"value": 50.0}, {"value": 60.0}],
            "memory_percent": [{"value": 40.0}, {"value": 45.0}]
        },
        "benchmarks": [
            {
                "name": "test_1",
                "status": "passed",
                "start_time": "2024-01-01T00:00:00",
                "end_time": "2024-01-01T00:00:01"
            }
        ]
    }
    
    report_path = generator.generate_report("basic_report", test_results)
    print("Report generated at:", report_path) 