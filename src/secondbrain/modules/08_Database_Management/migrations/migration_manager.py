"""
Migration manager for handling schema version control and updates.
Manages database migrations, version tracking, and rollback operations.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker
from alembic import op
from alembic.script import ScriptDirectory
from alembic.config import Config
from alembic.migration import MigrationContext

logger = logging.getLogger(__name__)

@dataclass
class MigrationConfig:
    """Configuration for database migrations."""
    name: str
    version: str
    up_operations: List[Dict[str, Any]]
    down_operations: List[Dict[str, Any]]
    dependencies: List[str] = None
    description: str = None
    author: str = None

class MigrationManager:
    """Manages database migrations and version control."""
    
    def __init__(self, db_url: str = "sqlite:///secondbrain.db", config_dir: str = "config/migrations"):
        """Initialize the migration manager.
        
        Args:
            db_url: Database connection URL
            config_dir: Directory to store migration configurations
        """
        self.db_url = db_url
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._setup_database()
        self._setup_alembic()
        self._load_configs()
    
    def _setup_logging(self):
        """Set up logging for the migration manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_database(self):
        """Set up database connection and session."""
        try:
            self.engine = create_engine(self.db_url)
            self.Session = sessionmaker(bind=self.engine)
            self.metadata = MetaData()
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to set up database: {str(e)}")
            raise
    
    def _setup_alembic(self):
        """Set up Alembic for migrations."""
        try:
            # Create Alembic directory
            alembic_dir = Path("alembic")
            alembic_dir.mkdir(exist_ok=True)
            
            # Create alembic.ini
            alembic_ini = alembic_dir / "alembic.ini"
            if not alembic_ini.exists():
                with open(alembic_ini, 'w') as f:
                    f.write(f"""[alembic]
script_location = alembic
sqlalchemy.url = {self.db_url}
""")
            
            # Create versions directory
            versions_dir = alembic_dir / "versions"
            versions_dir.mkdir(exist_ok=True)
            
            # Create env.py
            env_py = alembic_dir / "env.py"
            if not env_py.exists():
                with open(env_py, 'w') as f:
                    f.write("""from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

config = context.config
fileConfig(config.config_file_name)
target_metadata = None

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""")
            
            self.alembic_cfg = Config(str(alembic_ini))
            self.script = ScriptDirectory.from_config(self.alembic_cfg)
            logger.info("Alembic setup completed")
            
        except Exception as e:
            logger.error(f"Failed to set up Alembic: {str(e)}")
            raise
    
    def _load_configs(self):
        """Load migration configurations."""
        try:
            config_file = self.config_dir / "migration_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: MigrationConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Migration configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load migration configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save migration configurations."""
        try:
            config_file = self.config_dir / "migration_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save migration configurations: {str(e)}")
    
    def create_config(self, config: MigrationConfig) -> bool:
        """Create a new migration configuration.
        
        Args:
            config: Migration configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created migration configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create migration configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: MigrationConfig) -> bool:
        """Update an existing migration configuration.
        
        Args:
            name: Configuration name
            config: New migration configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated migration configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update migration configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete a migration configuration.
        
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
            
            logger.info(f"Deleted migration configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete migration configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[MigrationConfig]:
        """Get migration configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Migration configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all migration configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def create_migration(self, config_name: str) -> bool:
        """Create a new migration.
        
        Args:
            config_name: Configuration name
            
        Returns:
            bool: True if migration was created successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False
            
            # Create migration file
            migration_file = self.script.get_revision(config.version)
            if not migration_file:
                migration_file = self.script.generate_revision(
                    config.version,
                    config.description or "",
                    config.author or ""
                )
            
            # Write migration operations
            with open(migration_file.path, 'w') as f:
                f.write(f"""\"\"\"
{config.description or ""}

Revision ID: {config.version}
Revises: {', '.join(config.dependencies) if config.dependencies else ''}
Create Date: {datetime.now().isoformat()}

\"\"\"

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '{config.version}'
down_revision = {config.dependencies[0] if config.dependencies else 'None'}
branch_labels = None
depends_on = None

def upgrade():
    {self._format_operations(config.up_operations)}

def downgrade():
    {self._format_operations(config.down_operations)}
""")
            
            logger.info(f"Created migration {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create migration {config_name}: {str(e)}")
            return False
    
    def _format_operations(self, operations: List[Dict[str, Any]]) -> str:
        """Format migration operations.
        
        Args:
            operations: List of operations
            
        Returns:
            Formatted operations string
        """
        try:
            formatted = []
            for op in operations:
                if op["type"] == "create_table":
                    formatted.append(f"""op.create_table(
    '{op["name"]}',
    sa.Column('id', sa.Integer(), nullable=False),
    {', '.join(f"sa.Column('{col['name']}', {col['type']}, {col.get('options', {})})" for col in op["columns"])}
)""")
                elif op["type"] == "drop_table":
                    formatted.append(f"op.drop_table('{op['name']}')")
                elif op["type"] == "add_column":
                    formatted.append(f"""op.add_column('{op["table"]}', sa.Column('{op["column"]["name"]}', {op["column"]["type"]}, {op["column"].get("options", {})}))""")
                elif op["type"] == "drop_column":
                    formatted.append(f"op.drop_column('{op['table']}', '{op['column']}')")
                elif op["type"] == "create_index":
                    formatted.append(f"""op.create_index('{op["name"]}', '{op["table"]}', [{', '.join(f"'{col}'" for col in op["columns"])}], {op.get("options", {})})""")
                elif op["type"] == "drop_index":
                    formatted.append(f"op.drop_index('{op['name']}', table_name='{op['table']}')")
            
            return "\n    ".join(formatted)
            
        except Exception as e:
            logger.error(f"Failed to format operations: {str(e)}")
            return ""
    
    def run_migration(self, config_name: str) -> bool:
        """Run a migration.
        
        Args:
            config_name: Configuration name
            
        Returns:
            bool: True if migration was run successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False
            
            # Check dependencies
            if config.dependencies:
                for dependency in config.dependencies:
                    if not self._check_dependency(dependency):
                        logger.error(f"Dependency {dependency} not satisfied")
                        return False
            
            # Run migration
            with self.engine.begin() as connection:
                context = MigrationContext.configure(connection)
                context.run_migrations()
            
            logger.info(f"Ran migration {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run migration {config_name}: {str(e)}")
            return False
    
    def _check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is satisfied.
        
        Args:
            dependency: Dependency to check
            
        Returns:
            bool: True if dependency is satisfied
        """
        try:
            # Add dependency checking logic
            return True
            
        except Exception as e:
            logger.error(f"Failed to check dependency {dependency}: {str(e)}")
            return False
    
    def rollback_migration(self, config_name: str) -> bool:
        """Rollback a migration.
        
        Args:
            config_name: Configuration name
            
        Returns:
            bool: True if migration was rolled back successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return False
            
            # Rollback migration
            with self.engine.begin() as connection:
                context = MigrationContext.configure(connection)
                context.run_migrations(downgrade=True)
            
            logger.info(f"Rolled back migration {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {config_name}: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    manager = MigrationManager()
    
    # Create migration configuration
    config = MigrationConfig(
        name="add_user_table",
        version="001",
        description="Add user table",
        author="System",
        up_operations=[
            {
                "type": "create_table",
                "name": "users",
                "columns": [
                    {
                        "name": "username",
                        "type": "sa.String(50)",
                        "options": {"unique": True, "nullable": False}
                    },
                    {
                        "name": "email",
                        "type": "sa.String(100)",
                        "options": {"unique": True, "nullable": False}
                    }
                ]
            }
        ],
        down_operations=[
            {
                "type": "drop_table",
                "name": "users"
            }
        ]
    )
    manager.create_config(config)
    
    # Create and run migration
    if manager.create_migration("add_user_table"):
        manager.run_migration("add_user_table") 