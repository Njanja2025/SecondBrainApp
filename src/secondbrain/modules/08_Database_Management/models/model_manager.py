"""
Model manager for handling database schema and ORM models.
Manages model definitions, relationships, and schema validation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

logger = logging.getLogger(__name__)
Base = declarative_base()

@dataclass
class ModelConfig:
    """Configuration for database models."""
    name: str
    fields: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]] = None
    indexes: List[Dict[str, Any]] = None
    constraints: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

class ModelManager:
    """Manages database models and schema."""
    
    def __init__(self, db_url: str = "sqlite:///secondbrain.db", config_dir: str = "config/models"):
        """Initialize the model manager.
        
        Args:
            db_url: Database connection URL
            config_dir: Directory to store model configurations
        """
        self.db_url = db_url
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._setup_database()
        self._load_configs()
    
    def _setup_logging(self):
        """Set up logging for the model manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_database(self):
        """Set up database connection and session."""
        try:
            self.engine = create_engine(self.db_url)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to set up database: {str(e)}")
            raise
    
    def _load_configs(self):
        """Load model configurations."""
        try:
            config_file = self.config_dir / "model_configs.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.configs = {name: ModelConfig(**config)
                                  for name, config in json.load(f).items()}
            else:
                self.configs = {}
                self._save_configs()
            
            logger.info("Model configurations loaded")
            
        except Exception as e:
            logger.error(f"Failed to load model configurations: {str(e)}")
            raise
    
    def _save_configs(self):
        """Save model configurations."""
        try:
            config_file = self.config_dir / "model_configs.json"
            
            with open(config_file, 'w') as f:
                json.dump({name: vars(config) for name, config in self.configs.items()},
                         f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save model configurations: {str(e)}")
    
    def create_config(self, config: ModelConfig) -> bool:
        """Create a new model configuration.
        
        Args:
            config: Model configuration
            
        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False
            
            self.configs[config.name] = config
            self._save_configs()
            
            logger.info(f"Created model configuration {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create model configuration {config.name}: {str(e)}")
            return False
    
    def update_config(self, name: str, config: ModelConfig) -> bool:
        """Update an existing model configuration.
        
        Args:
            name: Configuration name
            config: New model configuration
            
        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False
            
            self.configs[name] = config
            self._save_configs()
            
            logger.info(f"Updated model configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update model configuration {name}: {str(e)}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """Delete a model configuration.
        
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
            
            logger.info(f"Deleted model configuration {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model configuration {name}: {str(e)}")
            return False
    
    def get_config(self, name: str) -> Optional[ModelConfig]:
        """Get model configuration.
        
        Args:
            name: Configuration name
            
        Returns:
            Model configuration if found
        """
        return self.configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all model configurations.
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())
    
    def create_model(self, config_name: str) -> Optional[Type]:
        """Create a database model from configuration.
        
        Args:
            config_name: Configuration name
            
        Returns:
            Model class if created successfully
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None
            
            # Create model class
            model_class = type(
                config.name,
                (Base,),
                {
                    "__tablename__": config.name.lower(),
                    "id": Column(Integer, primary_key=True),
                    "created_at": Column(DateTime, default=datetime.utcnow),
                    "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
                }
            )
            
            # Add fields
            for field in config.fields:
                field_type = self._get_field_type(field["type"])
                if field_type:
                    setattr(model_class, field["name"], Column(field_type, **field.get("options", {})))
            
            # Add relationships
            if config.relationships:
                for rel in config.relationships:
                    relationship_type = self._get_relationship_type(rel["type"])
                    if relationship_type:
                        setattr(model_class, rel["name"], relationship_type(**rel.get("options", {})))
            
            # Create table
            Base.metadata.create_all(self.engine)
            
            logger.info(f"Created model {config_name}")
            return model_class
            
        except Exception as e:
            logger.error(f"Failed to create model {config_name}: {str(e)}")
            return None
    
    def _get_field_type(self, field_type: str) -> Optional[Type]:
        """Get SQLAlchemy field type from string.
        
        Args:
            field_type: Field type string
            
        Returns:
            SQLAlchemy field type
        """
        type_map = {
            "string": String,
            "integer": Integer,
            "datetime": DateTime,
            "boolean": Boolean,
            "json": JSON
        }
        return type_map.get(field_type.lower())
    
    def _get_relationship_type(self, rel_type: str) -> Optional[Type]:
        """Get SQLAlchemy relationship type from string.
        
        Args:
            rel_type: Relationship type string
            
        Returns:
            SQLAlchemy relationship type
        """
        return relationship if rel_type.lower() == "relationship" else None
    
    def validate_schema(self, model_class: Type) -> bool:
        """Validate model schema.
        
        Args:
            model_class: Model class to validate
            
        Returns:
            bool: True if schema is valid
        """
        try:
            # Check required fields
            required_fields = ["id", "created_at", "updated_at"]
            for field in required_fields:
                if not hasattr(model_class, field):
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Check field types
            for column in model_class.__table__.columns:
                if not isinstance(column.type, (String, Integer, DateTime, Boolean, JSON)):
                    logger.error(f"Invalid field type for {column.name}")
                    return False
            
            logger.info(f"Schema validation passed for {model_class.__name__}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate schema: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    manager = ModelManager()
    
    # Create model configuration
    config = ModelConfig(
        name="User",
        fields=[
            {
                "name": "username",
                "type": "string",
                "options": {"unique": True, "nullable": False}
            },
            {
                "name": "email",
                "type": "string",
                "options": {"unique": True, "nullable": False}
            },
            {
                "name": "is_active",
                "type": "boolean",
                "options": {"default": True}
            }
        ],
        relationships=[
            {
                "name": "notes",
                "type": "relationship",
                "options": {"backref": "user", "lazy": "dynamic"}
            }
        ]
    )
    manager.create_config(config)
    
    # Create model
    User = manager.create_model("User")
    if User:
        print("Model created successfully") 