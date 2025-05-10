"""
SecondBrainApp - Your AI-Powered Personal Assistant
"""
import os
import logging
from pathlib import Path

# Configure base paths
BASE_DIR = Path(os.getenv('SECONDBRAIN_BASE_DIR', str(Path.home() / '.secondbrain')))
REPORTS_DIR = BASE_DIR / 'reports'
DOCS_DIR = BASE_DIR / 'docs'
LOGS_DIR = BASE_DIR / 'logs'

# Create necessary directories
for directory in [BASE_DIR, REPORTS_DIR, DOCS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'secondbrain.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("SecondBrainApp initialized")

__version__ = '2025.1.0'

from .brain_controller import BrainController
from .ai_agent import AIAgent
from .gui import GUI
from .memory.diagnostic_memory_core import DiagnosticMemoryCore
from .persona.adaptive_learning import PersonaLearningModule
from .core.strategic_planner import StrategicPlanner

__all__ = [
    'BrainController',
    'AIAgent',
    'GUI',
    'DiagnosticMemoryCore',
    'PersonaLearningModule',
    'StrategicPlanner'
] 