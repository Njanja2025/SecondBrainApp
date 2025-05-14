"""
System startup manager for SecondBrain.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class StartupManager:
    def __init__(self):
        self.components = {}
        self.startup_order = []
        self.status = {}
        self.config_path = Path("config/startup.json")
        self.is_initialized = False

    async def register_component(
        self, name: str, component: Any, dependencies: List[str] = None
    ):
        """Register a component for startup management."""
        self.components[name] = {
            "instance": component,
            "dependencies": dependencies or [],
            "status": "pending",
        }

    async def initialize_system(self):
        """Initialize all system components in correct order."""
        try:
            logger.info("Starting system initialization...")

            # Load startup configuration
            await self._load_config()

            # Calculate startup order
            self.startup_order = self._calculate_startup_order()

            # Initialize components
            for component_name in self.startup_order:
                await self._initialize_component(component_name)

            self.is_initialized = True
            logger.info("System initialization complete")

            # Save successful startup
            await self._save_startup_state()

        except Exception as e:
            logger.error(f"Error during system initialization: {e}")
            raise

    async def _initialize_component(self, component_name: str):
        """Initialize a single component."""
        try:
            component = self.components[component_name]

            # Check dependencies
            for dep in component["dependencies"]:
                if self.components[dep]["status"] != "running":
                    raise RuntimeError(
                        f"Dependency {dep} not running for {component_name}"
                    )

            # Initialize component
            logger.info(f"Initializing component: {component_name}")
            await component["instance"].initialize()

            # Update status
            component["status"] = "running"
            self.status[component_name] = {
                "status": "running",
                "initialized_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error initializing {component_name}: {e}")
            component["status"] = "failed"
            self.status[component_name] = {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat(),
            }
            raise

    def _calculate_startup_order(self) -> List[str]:
        """Calculate correct startup order based on dependencies."""
        visited = set()
        startup_order = []

        def visit(name):
            if name in visited:
                return
            visited.add(name)
            for dep in self.components[name]["dependencies"]:
                visit(dep)
            startup_order.append(name)

        for name in self.components:
            visit(name)

        return startup_order

    async def _load_config(self):
        """Load startup configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    config = json.load(f)

                # Apply configuration
                for name, settings in config.get("components", {}).items():
                    if name in self.components:
                        self.components[name].update(settings)

        except Exception as e:
            logger.error(f"Error loading startup config: {e}")

    async def _save_startup_state(self):
        """Save current startup state."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(
                    {
                        "last_startup": datetime.now().isoformat(),
                        "components": self.status,
                        "startup_order": self.startup_order,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Error saving startup state: {e}")

    async def shutdown_system(self):
        """Shutdown all components in reverse order."""
        try:
            logger.info("Starting system shutdown...")

            # Shutdown in reverse order
            for component_name in reversed(self.startup_order):
                await self._shutdown_component(component_name)

            self.is_initialized = False
            logger.info("System shutdown complete")

        except Exception as e:
            logger.error(f"Error during system shutdown: {e}")
            raise

    async def _shutdown_component(self, component_name: str):
        """Shutdown a single component."""
        try:
            component = self.components[component_name]

            if hasattr(component["instance"], "stop"):
                await component["instance"].stop()

            component["status"] = "stopped"
            self.status[component_name] = {
                "status": "stopped",
                "stopped_at": datetime.now().isoformat(),
            }

            logger.info(f"Component {component_name} stopped")

        except Exception as e:
            logger.error(f"Error stopping {component_name}: {e}")
            self.status[component_name] = {
                "status": "error",
                "error": str(e),
                "error_at": datetime.now().isoformat(),
            }

    def get_system_status(self) -> Dict[str, Any]:
        """Get current status of all components."""
        return {
            "initialized": self.is_initialized,
            "components": self.status,
            "startup_order": self.startup_order,
        }

    async def restart_component(self, component_name: str):
        """Restart a specific component."""
        try:
            logger.info(f"Restarting component: {component_name}")

            # Shutdown
            await self._shutdown_component(component_name)

            # Initialize
            await self._initialize_component(component_name)

            logger.info(f"Component {component_name} restarted successfully")

        except Exception as e:
            logger.error(f"Error restarting {component_name}: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        health_status = {}

        for name, component in self.components.items():
            try:
                if hasattr(component["instance"], "health_check"):
                    status = await component["instance"].health_check()
                else:
                    status = "unknown"

                health_status[name] = {
                    "status": status,
                    "last_checked": datetime.now().isoformat(),
                }

            except Exception as e:
                health_status[name] = {
                    "status": "error",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat(),
                }

        return health_status
