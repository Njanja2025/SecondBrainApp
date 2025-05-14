"""
Query manager for handling database queries and access layers.
Manages database queries, caching, and query optimization.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, select, update, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import expression
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


@dataclass
class QueryConfig:
    """Configuration for database queries."""

    name: str
    query_type: str  # select, insert, update, delete
    table: str
    conditions: List[Dict[str, Any]] = None
    fields: List[str] = None
    joins: List[Dict[str, Any]] = None
    order_by: List[Dict[str, str]] = None
    limit: int = None
    offset: int = None
    cache_ttl: int = None  # Time to live in seconds
    description: str = None


class QueryManager:
    """Manages database queries and access layers."""

    def __init__(
        self,
        db_url: str = "sqlite:///secondbrain.db",
        config_dir: str = "config/queries",
    ):
        """Initialize the query manager.

        Args:
            db_url: Database connection URL
            config_dir: Directory to store query configurations
        """
        self.db_url = db_url
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._setup_database()
        self._load_configs()
        self._setup_cache()

    def _setup_logging(self):
        """Set up logging for the query manager."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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

    def _setup_cache(self):
        """Set up query cache."""
        self.cache = {}
        self.cache_timestamps = {}

    def _load_configs(self):
        """Load query configurations."""
        try:
            config_file = self.config_dir / "query_configs.json"

            if config_file.exists():
                with open(config_file, "r") as f:
                    self.configs = {
                        name: QueryConfig(**config)
                        for name, config in json.load(f).items()
                    }
            else:
                self.configs = {}
                self._save_configs()

            logger.info("Query configurations loaded")

        except Exception as e:
            logger.error(f"Failed to load query configurations: {str(e)}")
            raise

    def _save_configs(self):
        """Save query configurations."""
        try:
            config_file = self.config_dir / "query_configs.json"

            with open(config_file, "w") as f:
                json.dump(
                    {name: vars(config) for name, config in self.configs.items()},
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Failed to save query configurations: {str(e)}")

    def create_config(self, config: QueryConfig) -> bool:
        """Create a new query configuration.

        Args:
            config: Query configuration

        Returns:
            bool: True if configuration was created successfully
        """
        try:
            if config.name in self.configs:
                logger.error(f"Configuration {config.name} already exists")
                return False

            self.configs[config.name] = config
            self._save_configs()

            logger.info(f"Created query configuration {config.name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to create query configuration {config.name}: {str(e)}"
            )
            return False

    def update_config(self, name: str, config: QueryConfig) -> bool:
        """Update an existing query configuration.

        Args:
            name: Configuration name
            config: New query configuration

        Returns:
            bool: True if configuration was updated successfully
        """
        try:
            if name not in self.configs:
                logger.error(f"Configuration {name} not found")
                return False

            self.configs[name] = config
            self._save_configs()

            logger.info(f"Updated query configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update query configuration {name}: {str(e)}")
            return False

    def delete_config(self, name: str) -> bool:
        """Delete a query configuration.

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

            logger.info(f"Deleted query configuration {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete query configuration {name}: {str(e)}")
            return False

    def get_config(self, name: str) -> Optional[QueryConfig]:
        """Get query configuration.

        Args:
            name: Configuration name

        Returns:
            Query configuration if found
        """
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all query configurations.

        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

    def execute_query(
        self, config_name: str, params: Dict[str, Any] = None
    ) -> Union[List[Dict[str, Any]], int, bool]:
        """Execute a query.

        Args:
            config_name: Configuration name
            params: Query parameters

        Returns:
            Query results or number of affected rows
        """
        try:
            config = self.get_config(config_name)
            if not config:
                logger.error(f"Configuration {config_name} not found")
                return None

            # Check cache
            if config.cache_ttl:
                cache_key = f"{config_name}:{str(params)}"
                if cache_key in self.cache:
                    timestamp = self.cache_timestamps.get(cache_key, 0)
                    if time.time() - timestamp < config.cache_ttl:
                        logger.info(f"Using cached results for {config_name}")
                        return self.cache[cache_key]

            # Build query
            query = self._build_query(config, params)

            # Execute query
            with self.Session() as session:
                if config.query_type == "select":
                    result = session.execute(query).fetchall()
                    result = [dict(row) for row in result]
                else:
                    result = session.execute(query).rowcount
                    session.commit()

            # Update cache
            if config.cache_ttl:
                self.cache[cache_key] = result
                self.cache_timestamps[cache_key] = time.time()

            logger.info(f"Executed query {config_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute query {config_name}: {str(e)}")
            return None

    def _build_query(
        self, config: QueryConfig, params: Dict[str, Any] = None
    ) -> expression:
        """Build a query from configuration.

        Args:
            config: Query configuration
            params: Query parameters

        Returns:
            SQLAlchemy query expression
        """
        try:
            table = Table(config.table, self.metadata, autoload_with=self.engine)

            if config.query_type == "select":
                query = select(table)

                # Add fields
                if config.fields:
                    query = select(*[table.c[field] for field in config.fields])

                # Add joins
                if config.joins:
                    for join in config.joins:
                        join_table = Table(
                            join["table"], self.metadata, autoload_with=self.engine
                        )
                        query = query.join(join_table, join["condition"])

                # Add conditions
                if config.conditions:
                    conditions = []
                    for condition in config.conditions:
                        field = condition["field"]
                        operator = condition["operator"]
                        value = (
                            params.get(condition.get("param", field))
                            if params
                            else condition["value"]
                        )

                        if operator == "eq":
                            conditions.append(table.c[field] == value)
                        elif operator == "ne":
                            conditions.append(table.c[field] != value)
                        elif operator == "gt":
                            conditions.append(table.c[field] > value)
                        elif operator == "lt":
                            conditions.append(table.c[field] < value)
                        elif operator == "ge":
                            conditions.append(table.c[field] >= value)
                        elif operator == "le":
                            conditions.append(table.c[field] <= value)
                        elif operator == "like":
                            conditions.append(table.c[field].like(value))
                        elif operator == "in":
                            conditions.append(table.c[field].in_(value))

                    query = query.where(*conditions)

                # Add order by
                if config.order_by:
                    for order in config.order_by:
                        field = order["field"]
                        direction = order["direction"]

                        if direction == "asc":
                            query = query.order_by(table.c[field].asc())
                        else:
                            query = query.order_by(table.c[field].desc())

                # Add limit and offset
                if config.limit:
                    query = query.limit(config.limit)
                if config.offset:
                    query = query.offset(config.offset)

                return query

            elif config.query_type == "insert":
                values = {}
                for field in config.fields:
                    values[field] = params.get(field)
                return table.insert().values(**values)

            elif config.query_type == "update":
                query = update(table)

                # Add conditions
                if config.conditions:
                    conditions = []
                    for condition in config.conditions:
                        field = condition["field"]
                        operator = condition["operator"]
                        value = (
                            params.get(condition.get("param", field))
                            if params
                            else condition["value"]
                        )

                        if operator == "eq":
                            conditions.append(table.c[field] == value)
                        elif operator == "ne":
                            conditions.append(table.c[field] != value)
                        elif operator == "gt":
                            conditions.append(table.c[field] > value)
                        elif operator == "lt":
                            conditions.append(table.c[field] < value)
                        elif operator == "ge":
                            conditions.append(table.c[field] >= value)
                        elif operator == "le":
                            conditions.append(table.c[field] <= value)
                        elif operator == "like":
                            conditions.append(table.c[field].like(value))
                        elif operator == "in":
                            conditions.append(table.c[field].in_(value))

                    query = query.where(*conditions)

                # Add values
                values = {}
                for field in config.fields:
                    values[field] = params.get(field)
                query = query.values(**values)

                return query

            elif config.query_type == "delete":
                query = delete(table)

                # Add conditions
                if config.conditions:
                    conditions = []
                    for condition in config.conditions:
                        field = condition["field"]
                        operator = condition["operator"]
                        value = (
                            params.get(condition.get("param", field))
                            if params
                            else condition["value"]
                        )

                        if operator == "eq":
                            conditions.append(table.c[field] == value)
                        elif operator == "ne":
                            conditions.append(table.c[field] != value)
                        elif operator == "gt":
                            conditions.append(table.c[field] > value)
                        elif operator == "lt":
                            conditions.append(table.c[field] < value)
                        elif operator == "ge":
                            conditions.append(table.c[field] >= value)
                        elif operator == "le":
                            conditions.append(table.c[field] <= value)
                        elif operator == "like":
                            conditions.append(table.c[field].like(value))
                        elif operator == "in":
                            conditions.append(table.c[field].in_(value))

                    query = query.where(*conditions)

                return query

        except Exception as e:
            logger.error(f"Failed to build query: {str(e)}")
            raise

    def clear_cache(self, config_name: str = None):
        """Clear query cache.

        Args:
            config_name: Configuration name to clear cache for, or None to clear all
        """
        try:
            if config_name:
                # Clear cache for specific configuration
                keys_to_remove = [
                    k for k in self.cache.keys() if k.startswith(f"{config_name}:")
                ]
                for key in keys_to_remove:
                    del self.cache[key]
                    del self.cache_timestamps[key]
            else:
                # Clear all cache
                self.cache.clear()
                self.cache_timestamps.clear()

            logger.info(
                f"Cleared cache for {config_name if config_name else 'all configurations'}"
            )

        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")


# Example usage
if __name__ == "__main__":
    manager = QueryManager()

    # Create query configuration
    config = QueryConfig(
        name="get_user_by_username",
        query_type="select",
        table="users",
        fields=["id", "username", "email"],
        conditions=[{"field": "username", "operator": "eq", "param": "username"}],
        cache_ttl=300,  # 5 minutes
        description="Get user by username",
    )
    manager.create_config(config)

    # Execute query
    result = manager.execute_query("get_user_by_username", {"username": "john_doe"})
    print(result)
