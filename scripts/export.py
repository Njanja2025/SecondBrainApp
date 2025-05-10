"""
Data export functionality for SecondBrain Dashboard
"""
import json
import csv
import logging
import shutil
import gzip
import bz2
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from config import EXPORT_SETTINGS, EXPORT_DIR

logger = logging.getLogger(__name__)

class DataExporter:
    def __init__(self):
        """Initialize the data exporter."""
        self.export_dir = EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup_old_exports()
        self.compression_level = 9  # Maximum compression

    def _export_single_format(self, data: Dict[str, Any], format: str, 
                            timestamp: str, parent_dir: Optional[Path] = None) -> Path:
        """Export data in a single format with compression."""
        if parent_dir is None:
            parent_dir = self.export_dir

        base_filename = f"dashboard_data_{timestamp}"
        
        if format == 'json':
            export_path = parent_dir / f"{base_filename}.json.gz"
            with gzip.open(export_path, 'wt', compresslevel=self.compression_level) as f:
                json.dump(data, f, indent=4)
        elif format == 'csv':
            export_path = parent_dir / f"{base_filename}.csv.bz2"
            flat_data = self._flatten_dict(data)
            with bz2.open(export_path, 'wt', compresslevel=self.compression_level) as f:
                writer = csv.writer(f)
                writer.writerow(['Key', 'Value'])
                for key, value in flat_data.items():
                    writer.writerow([key, value])
        elif format == 'xlsx':
            # Excel files are already compressed, no need for additional compression
            export_path = parent_dir / f"{base_filename}.xlsx"
            self._export_to_excel(data, export_path)

        return export_path

    def cleanup_old_exports(self) -> None:
        """Clean up old export files with support for compressed files."""
        try:
            retention_date = datetime.now() - timedelta(days=EXPORT_SETTINGS['retention_days'])
            
            # Clean up individual export files
            compressed_patterns = [
                "dashboard_data_*.json.gz",
                "dashboard_data_*.csv.bz2",
                "dashboard_data_*.xlsx"
            ]
            
            for pattern in compressed_patterns:
                for file in self.export_dir.glob(pattern):
                    if file.stat().st_mtime < retention_date.timestamp():
                        file.unlink()

            # Clean up compressed exports
            for file in self.export_dir.glob("export_*.zip"):
                if file.stat().st_mtime < retention_date.timestamp():
                    file.unlink()

            # Enforce maximum number of exports
            all_exports = sorted(
                [f for f in self.export_dir.glob("*.*") 
                 if f.suffix in ['.gz', '.bz2', '.xlsx', '.zip']],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if len(all_exports) > EXPORT_SETTINGS['max_exports']:
                for export in all_exports[EXPORT_SETTINGS['max_exports']:]:
                    export.unlink()

        except Exception as e:
            logger.error(f"Failed to cleanup old exports: {e}")