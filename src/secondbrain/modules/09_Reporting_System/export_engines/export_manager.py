"""
Export manager for handling report exports.
Manages report export formats, templates, and delivery.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import jinja2
import pdfkit
import markdown
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)

@dataclass
class ExportConfig:
    """Configuration for report exports."""
    name: str
    format: str  # pdf, html, markdown, csv, excel, json
    template: Optional[str] = None
    options: Dict[str, Any] = None
    delivery: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    description: str = None

class ExportManager:
    """Manages report exports and delivery."""
    
    def __init__(self, config_dir: str = "config/exports"):
        """Initialize the export manager.
        
        Args:
            config_dir: Directory to store export configurations
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._setup_templates()
        self._load_configs()
    
    def _setup_logging(self):
        """Set up logging for the export manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_templates(self):
        """Set up Jinja2 template environment."""
        try:
            template_dir = self.config_dir / "templates"
            template_dir.mkdir(parents=True, exist_ok=True)
            
            self.template_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(template_dir)),
                autoescape=True
            )
            
            logger.info("Template environment set up")
            
        except Exception as e:
            logger.error(f"Failed to set up template environment: {str(e)}")
            raise
    
    def _load_configs(self):
        """Load export configurations."""
        try:
            config_file = self.config_dir / "export_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: ExportConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Export configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load export configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save export configurations."""
        try:
            config_file = self.config_dir / "export_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save export configurations: {str(e)}")
    
    def create_config(self, config: ExportConfig) -> bool:
        """Create a new export configuration.
        
        Args:
            config: Export configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created export configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create export configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: ExportConfig) -> bool:
        """Update an existing export configuration.
        
        Args:
            name: Configuration name
            config: New export configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated export configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update export configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete an export configuration.
        
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
            
            logger.info(f"Deleted export configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete export configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[ExportConfig]:
        """Get export configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Export configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all export configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def export_report(self, config_name: str, data: Dict[str, Any],
                     output_path: Optional[str] = None) -> Optional[str]:
        """Export a report using the specified configuration.
        
        Args:
            config_name: Configuration name
            data: Report data
            output_path: Path to save the exported report
            
        Returns:
            Path to the exported report if successful
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None
            
            # Generate report content
            content = self._generate_content(config, data)
            if not content:
                return None
            
            # Export to specified format
            output_file = self._export_to_format(config, content, output_path)
            if not output_file:
                return None
            
            # Handle delivery if configured
            if config.delivery:
                self._deliver_report(config, output_file)
            
            logger.info(f"Exported report using configuration {config_name}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export report using configuration {config_name}: {str(e)}")
            return None
    
    def _generate_content(self, config: ExportConfig, data: Dict[str, Any]) -> Optional[str]:
        """Generate report content using template.
        
        Args:
            config: Export configuration
            data: Report data
            
        Returns:
            Generated content if successful
        """
        try:
            if config.template:
                template = self.template_env.get_template(config.template)
                content = template.render(**data)
            else:
                content = json.dumps(data, indent=2)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate content: {str(e)}")
            return None
    
    def _export_to_format(self, config: ExportConfig, content: str,
                         output_path: Optional[str] = None) -> Optional[str]:
        """Export content to specified format.
        
        Args:
            config: Export configuration
            content: Report content
            output_path: Path to save the exported report
            
        Returns:
            Path to the exported report if successful
        """
        try:
            if not output_path:
                output_path = f"exports/{config.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if config.format == "pdf":
                return self._export_to_pdf(content, output_path, config.options)
            elif config.format == "html":
                return self._export_to_html(content, output_path)
            elif config.format == "markdown":
                return self._export_to_markdown(content, output_path)
            elif config.format == "csv":
                return self._export_to_csv(content, output_path)
            elif config.format == "excel":
                return self._export_to_excel(content, output_path)
            elif config.format == "json":
                return self._export_to_json(content, output_path)
            else:
                logger.error(f"Unsupported export format: {config.format}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to export to format {config.format}: {str(e)}")
            return None
    
    def _export_to_pdf(self, content: str, output_path: str,
                      options: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Export content to PDF.
        
        Args:
            content: Report content
            output_path: Path to save the PDF
            options: PDF export options
            
        Returns:
            Path to the PDF file if successful
        """
        try:
            output_file = f"{output_path}.pdf"
            pdf_options = options or {}
            
            pdfkit.from_string(content, output_file, options=pdf_options)
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export to PDF: {str(e)}")
            return None
    
    def _export_to_html(self, content: str, output_path: str) -> Optional[str]:
        """Export content to HTML.
        
        Args:
            content: Report content
            output_path: Path to save the HTML
            
        Returns:
            Path to the HTML file if successful
        """
        try:
            output_file = f"{output_path}.html"
            
            with open(output_file, 'w') as f:
                f.write(content)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export to HTML: {str(e)}")
            return None
    
    def _export_to_markdown(self, content: str, output_path: str) -> Optional[str]:
        """Export content to Markdown.
        
        Args:
            content: Report content
            output_path: Path to save the Markdown
            
        Returns:
            Path to the Markdown file if successful
        """
        try:
            output_file = f"{output_path}.md"
            
            with open(output_file, 'w') as f:
                f.write(content)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export to Markdown: {str(e)}")
            return None
    
    def _export_to_csv(self, content: str, output_path: str) -> Optional[str]:
        """Export content to CSV.
        
        Args:
            content: Report content
            output_path: Path to save the CSV
            
        Returns:
            Path to the CSV file if successful
        """
        try:
            output_file = f"{output_path}.csv"
            data = json.loads(content)
            
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {str(e)}")
            return None
    
    def _export_to_excel(self, content: str, output_path: str) -> Optional[str]:
        """Export content to Excel.
        
        Args:
            content: Report content
            output_path: Path to save the Excel file
            
        Returns:
            Path to the Excel file if successful
        """
        try:
            output_file = f"{output_path}.xlsx"
            data = json.loads(content)
            
            df = pd.DataFrame(data)
            df.to_excel(output_file, index=False)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export to Excel: {str(e)}")
            return None
    
    def _export_to_json(self, content: str, output_path: str) -> Optional[str]:
        """Export content to JSON.
        
        Args:
            content: Report content
            output_path: Path to save the JSON
            
        Returns:
            Path to the JSON file if successful
        """
        try:
            output_file = f"{output_path}.json"
            
            with open(output_file, 'w') as f:
                f.write(content)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export to JSON: {str(e)}")
            return None
    
    def _deliver_report(self, config: ExportConfig, file_path: str) -> bool:
        """Deliver exported report.
        
        Args:
            config: Export configuration
            file_path: Path to the exported report
            
        Returns:
            bool: True if delivery was successful
        """
        try:
            delivery_type = config.delivery.get("type")
            
            if delivery_type == "email":
                return self._deliver_via_email(config, file_path)
            elif delivery_type == "s3":
                return self._deliver_via_s3(config, file_path)
            else:
                logger.error(f"Unsupported delivery type: {delivery_type}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to deliver report: {str(e)}")
            return False
    
    def _deliver_via_email(self, config: ExportConfig, file_path: str) -> bool:
        """Deliver report via email.
        
        Args:
            config: Export configuration
            file_path: Path to the exported report
            
        Returns:
            bool: True if delivery was successful
        """
        try:
            delivery_config = config.delivery
            smtp_config = delivery_config.get("smtp", {})
            
            msg = MIMEMultipart()
            msg["Subject"] = delivery_config.get("subject", "Report")
            msg["From"] = smtp_config.get("from")
            msg["To"] = ", ".join(delivery_config.get("recipients", []))
            
            # Add body
            body = delivery_config.get("body", "")
            msg.attach(MIMEText(body, "plain"))
            
            # Add attachment
            with open(file_path, "rb") as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(file_path)}"
                )
                msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(smtp_config.get("host"), smtp_config.get("port")) as server:
                if smtp_config.get("use_tls"):
                    server.starttls()
                if smtp_config.get("username"):
                    server.login(smtp_config["username"], smtp_config["password"])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deliver via email: {str(e)}")
            return False
    
    def _deliver_via_s3(self, config: ExportConfig, file_path: str) -> bool:
        """Deliver report via S3.
        
        Args:
            config: Export configuration
            file_path: Path to the exported report
            
        Returns:
            bool: True if delivery was successful
        """
        try:
            # Implement S3 delivery
            logger.info("S3 delivery not implemented")
            return False
            
        except Exception as e:
            logger.error(f"Failed to deliver via S3: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    manager = ExportManager()
    
    # Create export configuration
    config = ExportConfig(
        name="user_report",
        format="pdf",
        template="user_report.html",
        options={
            "page-size": "A4",
            "margin-top": "20mm",
            "margin-right": "20mm",
            "margin-bottom": "20mm",
            "margin-left": "20mm"
        },
        delivery={
            "type": "email",
            "subject": "User Report",
            "recipients": ["user@example.com"],
            "body": "Please find attached the user report.",
            "smtp": {
                "host": "smtp.example.com",
                "port": 587,
                "use_tls": True,
                "username": "user",
                "password": "password",
                "from": "reports@example.com"
            }
        },
        description="User report export configuration"
    )
    manager.create_config(config)
    
    # Export report
    data = {
        "title": "User Report",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "users": [
            {
                "username": "john_doe",
                "email": "john@example.com",
                "created_at": "2024-01-01"
            },
            {
                "username": "jane_doe",
                "email": "jane@example.com",
                "created_at": "2024-01-02"
            }
        ]
    }
    output_file = manager.export_report("user_report", data)
    print(f"Exported report to: {output_file}") 