"""
System map configuration for SecondBrain application.
Defines module structure, relationships, and dependencies.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModuleConfig:
    """Configuration for a system module."""

    name: str
    description: str
    dependencies: List[str]
    status: str = "active"
    last_updated: Optional[str] = None
    version: str = "1.0.0"


class SystemMap:
    """Manages the system module structure and relationships."""

    def __init__(self, base_dir: str = "/mnt/data/SecondBrainApp_SystemMap"):
        """Initialize the system map.

        Args:
            base_dir: Base directory for the system map
        """
        self.base_dir = Path(base_dir)
        self.modules: Dict[str, ModuleConfig] = {}
        self._initialize_modules()

    def _initialize_modules(self):
        """Initialize module configurations."""
        self.modules = {
            "01_Security": ModuleConfig(
                name="Security",
                description="Core security features including encryption, authentication, and access control",
                dependencies=[],
                last_updated=datetime.now().isoformat(),
            ),
            "02_Deployment": ModuleConfig(
                name="Deployment",
                description="Deployment automation and configuration management",
                dependencies=["01_Security"],
                last_updated=datetime.now().isoformat(),
            ),
            "03_Maintenance": ModuleConfig(
                name="Maintenance",
                description="System maintenance and update management",
                dependencies=["01_Security", "02_Deployment"],
                last_updated=datetime.now().isoformat(),
            ),
            "04_Integration": ModuleConfig(
                name="Integration",
                description="Third-party service integration and API management",
                dependencies=["01_Security"],
                last_updated=datetime.now().isoformat(),
            ),
            "05_User_Interface": ModuleConfig(
                name="User Interface",
                description="GUI and CLI interface components",
                dependencies=["01_Security", "04_Integration"],
                last_updated=datetime.now().isoformat(),
            ),
            "06_Testing_Quality_Assurance": ModuleConfig(
                name="Testing and QA",
                description="Testing frameworks and quality assurance tools",
                dependencies=["01_Security", "02_Deployment"],
                last_updated=datetime.now().isoformat(),
            ),
            "07_Documentation": ModuleConfig(
                name="Documentation",
                description="System documentation and user guides",
                dependencies=[],
                last_updated=datetime.now().isoformat(),
            ),
            "08_Database_Management": ModuleConfig(
                name="Database Management",
                description="Database operations and data management",
                dependencies=["01_Security"],
                last_updated=datetime.now().isoformat(),
            ),
            "09_Reporting_System": ModuleConfig(
                name="Reporting System",
                description="Analytics and reporting tools",
                dependencies=["08_Database_Management"],
                last_updated=datetime.now().isoformat(),
            ),
            "10_API_Integration": ModuleConfig(
                name="API Integration",
                description="External API integration and management",
                dependencies=["01_Security", "04_Integration"],
                last_updated=datetime.now().isoformat(),
            ),
            "11_Performance_Analysis": ModuleConfig(
                name="Performance Analysis",
                description="System performance monitoring and optimization",
                dependencies=["08_Database_Management"],
                last_updated=datetime.now().isoformat(),
            ),
            "12_Email_Analytics_Systems": ModuleConfig(
                name="Email Analytics",
                description="Email processing and analytics",
                dependencies=["09_Reporting_System"],
                last_updated=datetime.now().isoformat(),
            ),
            "13_Machine_Learning_Models": ModuleConfig(
                name="Machine Learning",
                description="ML models and predictive analytics",
                dependencies=["08_Database_Management", "11_Performance_Analysis"],
                last_updated=datetime.now().isoformat(),
            ),
            "14_System_Monitoring": ModuleConfig(
                name="System Monitoring",
                description="Real-time system monitoring and alerting",
                dependencies=["11_Performance_Analysis"],
                last_updated=datetime.now().isoformat(),
            ),
            "15_Anomaly_Detection": ModuleConfig(
                name="Anomaly Detection",
                description="Anomaly detection and security monitoring",
                dependencies=["13_Machine_Learning_Models", "14_System_Monitoring"],
                last_updated=datetime.now().isoformat(),
            ),
        }

    def get_module_path(self, module_id: str) -> Path:
        """Get the path for a specific module.

        Args:
            module_id: Module identifier

        Returns:
            Path object for the module directory
        """
        return self.base_dir / module_id

    def get_module_dependencies(self, module_id: str) -> List[str]:
        """Get dependencies for a specific module.

        Args:
            module_id: Module identifier

        Returns:
            List of dependency module IDs
        """
        if module_id not in self.modules:
            return []
        return self.modules[module_id].dependencies

    def update_module_status(self, module_id: str, status: str):
        """Update the status of a module.

        Args:
            module_id: Module identifier
            status: New status
        """
        if module_id in self.modules:
            self.modules[module_id].status = status
            self.modules[module_id].last_updated = datetime.now().isoformat()

    def get_module_info(self, module_id: str) -> Optional[Dict]:
        """Get detailed information about a module.

        Args:
            module_id: Module identifier

        Returns:
            Dictionary containing module information
        """
        if module_id not in self.modules:
            return None

        module = self.modules[module_id]
        return {
            "id": module_id,
            "name": module.name,
            "description": module.description,
            "dependencies": module.dependencies,
            "status": module.status,
            "last_updated": module.last_updated,
            "version": module.version,
        }

    def validate_dependencies(self) -> List[str]:
        """Validate module dependencies.

        Returns:
            List of any dependency issues found
        """
        issues = []

        for module_id, module in self.modules.items():
            for dep in module.dependencies:
                if dep not in self.modules:
                    issues.append(
                        f"Module {module_id} depends on non-existent module {dep}"
                    )

        return issues


# Example usage
if __name__ == "__main__":
    system_map = SystemMap()

    # Get module information
    security_info = system_map.get_module_info("01_Security")
    print("Security Module Info:", security_info)

    # Check dependencies
    issues = system_map.validate_dependencies()
    if issues:
        print("Dependency Issues:", issues)
    else:
        print("All dependencies are valid")
