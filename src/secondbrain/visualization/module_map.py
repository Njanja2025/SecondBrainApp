"""
Module for generating visual maps of SecondBrainApp modules
"""

from graphviz import Digraph
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModuleType(Enum):
    """Types of modules in the system."""

    CORE = "core"
    ENGINE = "engine"
    MCP = "mcp"
    FEATURE = "feature"
    SECURITY = "security"


@dataclass
class ModuleConfig:
    """Configuration for module visualization."""

    name: str
    type: ModuleType
    color: str
    shape: str = "box"
    style: str = "filled"
    fontsize: str = "14"
    fontname: str = "Arial"
    description: Optional[str] = None
    dependencies: List[str] = None


class ModuleMapGenerator:
    """Generator for SecondBrainApp module maps."""

    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize the module map generator.

        Args:
            output_path: Optional path to save the visualization
        """
        self.output_path = output_path or str(
            Path.home() / ".secondbrain" / "visualizations" / "module_map"
        )
        self.dot = Digraph(comment="SecondBrainApp 2025 Modules")
        self._configure_graph()
        self._init_modules()

    def _configure_graph(self):
        """Configure the graph visualization settings."""
        self.dot.attr(rankdir="TB", size="11,8", dpi="300")
        self.dot.attr("node", fontname="Arial")
        self.dot.attr("edge", fontname="Arial")

    def _init_modules(self):
        """Initialize module configurations."""
        self.modules = {
            "App": ModuleConfig(
                name="SecondBrainApp 2025",
                type=ModuleType.CORE,
                color="lightblue",
                shape="box",
                fontsize="16",
                fontname="Arial Bold",
                description="Main application framework",
            ),
            "Evolver": ModuleConfig(
                name="Evolver Engine",
                type=ModuleType.ENGINE,
                color="lightgrey",
                shape="ellipse",
                description="Core evolution engine",
            ),
            "Phantom": ModuleConfig(
                name="Phantom AI Core",
                type=ModuleType.ENGINE,
                color="lightgrey",
                shape="ellipse",
                description="AI processing engine",
            ),
            "WealthMCP": ModuleConfig(
                name="Wealth MCP",
                type=ModuleType.MCP,
                color="lightgreen",
                description="Wealth management system",
            ),
            "CompanionMCP": ModuleConfig(
                name="Companion MCP",
                type=ModuleType.MCP,
                color="lightyellow",
                description="AI companion system",
            ),
            "EngineeringMCP": ModuleConfig(
                name="Engineering MCP",
                type=ModuleType.MCP,
                color="lightcoral",
                description="Engineering tools",
            ),
            "SecurityCore": ModuleConfig(
                name="Security Core",
                type=ModuleType.SECURITY,
                color="orange",
                description="Security framework",
            ),
        }

        # Add feature modules
        self.features = {
            "WealthMCP": [
                ModuleConfig(
                    "Digital Product Store", ModuleType.FEATURE, "lightgreen", "note"
                ),
                ModuleConfig(
                    "Affiliate Mall", ModuleType.FEATURE, "lightgreen", "note"
                ),
                ModuleConfig(
                    "Dropshipping Hub", ModuleType.FEATURE, "lightgreen", "note"
                ),
                ModuleConfig(
                    "Faceless Content", ModuleType.FEATURE, "lightgreen", "note"
                ),
                ModuleConfig(
                    "AI Content Services", ModuleType.FEATURE, "lightgreen", "note"
                ),
                ModuleConfig(
                    "Book Publishing", ModuleType.FEATURE, "lightgreen", "note"
                ),
                ModuleConfig(
                    "Email Funnel System", ModuleType.FEATURE, "lightgreen", "note"
                ),
                ModuleConfig(
                    "Ad Agent System", ModuleType.FEATURE, "lightgreen", "note"
                ),
            ],
            "CompanionMCP": [
                ModuleConfig(
                    "Voice Journaling", ModuleType.FEATURE, "lightyellow", "note"
                ),
                ModuleConfig(
                    "Samantha Voice Sync", ModuleType.FEATURE, "lightyellow", "note"
                ),
                ModuleConfig(
                    "Academic & Sermon Writer",
                    ModuleType.FEATURE,
                    "lightyellow",
                    "note",
                ),
                ModuleConfig(
                    "Emotional Intelligence Layer",
                    ModuleType.FEATURE,
                    "lightyellow",
                    "note",
                ),
            ],
            "EngineeringMCP": [
                ModuleConfig(
                    "Game Generation System", ModuleType.FEATURE, "lightcoral", "note"
                ),
                ModuleConfig(
                    "Music Drafting + Video Integration",
                    ModuleType.FEATURE,
                    "lightcoral",
                    "note",
                ),
                ModuleConfig(
                    "AI Blueprint & Terminal Studio",
                    ModuleType.FEATURE,
                    "lightcoral",
                    "note",
                ),
            ],
        }

    def _add_module(self, module_id: str, config: ModuleConfig):
        """Add a module to the graph."""
        self.dot.node(
            module_id,
            config.name,
            shape=config.shape,
            style=config.style,
            color=config.color,
            fontsize=config.fontsize,
            fontname=config.fontname,
            tooltip=config.description,
        )

    def _add_edge(self, source: str, target: str, penwidth: str = "2"):
        """Add an edge to the graph."""
        self.dot.edge(source, target, penwidth=penwidth)

    def generate(self) -> str:
        """
        Generate the module map.

        Returns:
            Path to the generated visualization
        """
        try:
            # Add main app node
            self._add_module("App", self.modules["App"])

            # Add core engines
            for engine_id in ["Evolver", "Phantom"]:
                self._add_module(engine_id, self.modules[engine_id])
                self._add_edge("App", engine_id)

            # Add MCP modules
            for mcp_id in ["WealthMCP", "CompanionMCP", "EngineeringMCP"]:
                self._add_module(mcp_id, self.modules[mcp_id])
                self._add_edge("App", mcp_id)

                # Add features for each MCP
                for feature in self.features[mcp_id]:
                    feature_id = feature.name.replace(" ", "_")
                    self._add_module(feature_id, feature)
                    self._add_edge(mcp_id, feature_id, penwidth="1")

            # Add security core
            self._add_module("SecurityCore", self.modules["SecurityCore"])
            self._add_edge("App", "SecurityCore")

            # Create output directory if it doesn't exist
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

            # Render the diagram
            self.dot.render(self.output_path, format="png", cleanup=True)

            logger.info(f"Module map generated: {self.output_path}.png")
            return f"{self.output_path}.png"

        except Exception as e:
            logger.error(f"Failed to generate module map: {e}")
            raise


def generate_module_map(output_path: Optional[str] = None) -> str:
    """
    Generate a visual map of SecondBrainApp 2025 modules.

    Args:
        output_path: Optional path to save the visualization

    Returns:
        Path to the generated visualization
    """
    generator = ModuleMapGenerator(output_path)
    return generator.generate()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Generate the module map
    output_path = generate_module_map()
    print(f"Module map generated: {output_path}")
