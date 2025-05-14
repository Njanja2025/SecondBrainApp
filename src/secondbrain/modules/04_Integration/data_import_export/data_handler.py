"""
Data handler for managing import/export operations.
Handles data conversion, validation, and secure transfer.
"""

import os
import json
import csv
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ImportExportConfig:
    """Configuration for data import/export operations."""

    format: str  # csv, json, excel
    encoding: str = "utf-8"
    delimiter: str = ","
    quotechar: str = '"'
    compression: Optional[str] = None
    encryption_key: Optional[str] = None


class DataHandler:
    """Handles data import and export operations."""

    def __init__(self, data_dir: str = "data/integration"):
        """Initialize the data handler.

        Args:
            data_dir: Directory to store imported/exported data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for the data handler."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def import_data(
        self, file_path: Union[str, Path], config: ImportExportConfig
    ) -> Optional[Any]:
        """Import data from a file.

        Args:
            file_path: Path to the input file
            config: Import configuration

        Returns:
            Imported data if successful
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            if config.format.lower() == "csv":
                return self._import_csv(file_path, config)
            elif config.format.lower() == "json":
                return self._import_json(file_path, config)
            elif config.format.lower() == "excel":
                return self._import_excel(file_path, config)
            else:
                logger.error(f"Unsupported format: {config.format}")
                return None

        except Exception as e:
            logger.error(f"Failed to import data from {file_path}: {str(e)}")
            return None

    def _import_csv(
        self, file_path: Path, config: ImportExportConfig
    ) -> Optional[pd.DataFrame]:
        """Import data from a CSV file.

        Args:
            file_path: Path to the CSV file
            config: Import configuration

        Returns:
            DataFrame containing the imported data
        """
        try:
            return pd.read_csv(
                file_path,
                encoding=config.encoding,
                delimiter=config.delimiter,
                quotechar=config.quotechar,
                compression=config.compression,
            )
        except Exception as e:
            logger.error(f"Failed to import CSV from {file_path}: {str(e)}")
            return None

    def _import_json(
        self, file_path: Path, config: ImportExportConfig
    ) -> Optional[Dict[str, Any]]:
        """Import data from a JSON file.

        Args:
            file_path: Path to the JSON file
            config: Import configuration

        Returns:
            Dictionary containing the imported data
        """
        try:
            with open(file_path, "r", encoding=config.encoding) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to import JSON from {file_path}: {str(e)}")
            return None

    def _import_excel(
        self, file_path: Path, config: ImportExportConfig
    ) -> Optional[pd.DataFrame]:
        """Import data from an Excel file.

        Args:
            file_path: Path to the Excel file
            config: Import configuration

        Returns:
            DataFrame containing the imported data
        """
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Failed to import Excel from {file_path}: {str(e)}")
            return None

    def export_data(
        self, data: Any, file_path: Union[str, Path], config: ImportExportConfig
    ) -> bool:
        """Export data to a file.

        Args:
            data: Data to export
            file_path: Path to the output file
            config: Export configuration

        Returns:
            bool: True if export was successful
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if config.format.lower() == "csv":
                return self._export_csv(data, file_path, config)
            elif config.format.lower() == "json":
                return self._export_json(data, file_path, config)
            elif config.format.lower() == "excel":
                return self._export_excel(data, file_path, config)
            else:
                logger.error(f"Unsupported format: {config.format}")
                return False

        except Exception as e:
            logger.error(f"Failed to export data to {file_path}: {str(e)}")
            return False

    def _export_csv(
        self, data: pd.DataFrame, file_path: Path, config: ImportExportConfig
    ) -> bool:
        """Export data to a CSV file.

        Args:
            data: DataFrame to export
            file_path: Path to the CSV file
            config: Export configuration

        Returns:
            bool: True if export was successful
        """
        try:
            data.to_csv(
                file_path,
                encoding=config.encoding,
                sep=config.delimiter,
                quotechar=config.quotechar,
                compression=config.compression,
                index=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV to {file_path}: {str(e)}")
            return False

    def _export_json(
        self, data: Dict[str, Any], file_path: Path, config: ImportExportConfig
    ) -> bool:
        """Export data to a JSON file.

        Args:
            data: Dictionary to export
            file_path: Path to the JSON file
            config: Export configuration

        Returns:
            bool: True if export was successful
        """
        try:
            with open(file_path, "w", encoding=config.encoding) as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to export JSON to {file_path}: {str(e)}")
            return False

    def _export_excel(
        self, data: pd.DataFrame, file_path: Path, config: ImportExportConfig
    ) -> bool:
        """Export data to an Excel file.

        Args:
            data: DataFrame to export
            file_path: Path to the Excel file
            config: Export configuration

        Returns:
            bool: True if export was successful
        """
        try:
            data.to_excel(file_path, index=False)
            return True
        except Exception as e:
            logger.error(f"Failed to export Excel to {file_path}: {str(e)}")
            return False

    def validate_data(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Validate data against a schema.

        Args:
            data: Data to validate
            schema: Validation schema

        Returns:
            bool: True if data is valid
        """
        try:
            if isinstance(data, pd.DataFrame):
                return self._validate_dataframe(data, schema)
            elif isinstance(data, dict):
                return self._validate_dict(data, schema)
            else:
                logger.error(f"Unsupported data type for validation: {type(data)}")
                return False

        except Exception as e:
            logger.error(f"Failed to validate data: {str(e)}")
            return False

    def _validate_dataframe(self, data: pd.DataFrame, schema: Dict[str, Any]) -> bool:
        """Validate DataFrame against a schema.

        Args:
            data: DataFrame to validate
            schema: Validation schema

        Returns:
            bool: True if DataFrame is valid
        """
        try:
            # Check required columns
            required_columns = schema.get("required_columns", [])
            missing_columns = set(required_columns) - set(data.columns)
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False

            # Check data types
            type_checks = schema.get("type_checks", {})
            for column, expected_type in type_checks.items():
                if column in data.columns:
                    if not all(isinstance(x, expected_type) for x in data[column]):
                        logger.error(f"Invalid data type in column {column}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate DataFrame: {str(e)}")
            return False

    def _validate_dict(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate dictionary against a schema.

        Args:
            data: Dictionary to validate
            schema: Validation schema

        Returns:
            bool: True if dictionary is valid
        """
        try:
            # Check required keys
            required_keys = schema.get("required_keys", [])
            missing_keys = set(required_keys) - set(data.keys())
            if missing_keys:
                logger.error(f"Missing required keys: {missing_keys}")
                return False

            # Check value types
            type_checks = schema.get("type_checks", {})
            for key, expected_type in type_checks.items():
                if key in data:
                    if not isinstance(data[key], expected_type):
                        logger.error(f"Invalid type for key {key}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate dictionary: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    handler = DataHandler()

    # Import data
    config = ImportExportConfig(format="csv")
    data = handler.import_data("data.csv", config)

    # Validate data
    schema = {
        "required_columns": ["id", "name", "value"],
        "type_checks": {"id": int, "name": str, "value": float},
    }
    is_valid = handler.validate_data(data, schema)

    # Export data
    if is_valid:
        handler.export_data(data, "output.json", ImportExportConfig(format="json"))
