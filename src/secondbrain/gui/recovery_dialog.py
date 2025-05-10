"""
Recovery dialog for SecondBrain application.
Provides a GUI interface for managing backups and rollbacks.
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal

from ..monitoring.rollback_manager import rollback_manager

class RecoveryDialog(QDialog):
    """Dialog for managing application backups and rollbacks."""
    
    # Signal emitted when a rollback is performed
    rollback_performed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the recovery dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Recovery Manager")
        self.setMinimumSize(600, 400)
        
        self._init_ui()
        self._load_backups()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Backup and Recovery")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Backup table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Version", "Timestamp", "Status", "Notes", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_backups)
        button_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _load_backups(self):
        """Load and display available backups."""
        self.table.setRowCount(0)
        backups = rollback_manager.list_backups()
        
        for row, backup in enumerate(backups):
            self.table.insertRow(row)
            
            # Version
            version_item = QTableWidgetItem(backup['version'])
            self.table.setItem(row, 0, version_item)
            
            # Timestamp
            timestamp = datetime.strptime(
                backup['timestamp'],
                "%Y%m%d_%H%M%S"
            ).strftime("%Y-%m-%d %H:%M:%S")
            timestamp_item = QTableWidgetItem(timestamp)
            self.table.setItem(row, 1, timestamp_item)
            
            # Status
            status_item = QTableWidgetItem(backup['status'])
            self.table.setItem(row, 2, status_item)
            
            # Notes
            notes_item = QTableWidgetItem(backup['notes'])
            self.table.setItem(row, 3, notes_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            restore_button = QPushButton("Restore")
            restore_button.clicked.connect(
                lambda checked, v=backup['version']: self._restore_backup(v)
            )
            actions_layout.addWidget(restore_button)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 4, actions_widget)
    
    def _restore_backup(self, version: str):
        """Restore a backup version.
        
        Args:
            version: Version to restore
        """
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore version {version}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = rollback_manager.rollback(version)
            
            if success:
                QMessageBox.information(
                    self,
                    "Restore Successful",
                    f"Successfully restored version {version}."
                )
                self.rollback_performed.emit(version)
                self.close()
            else:
                QMessageBox.critical(
                    self,
                    "Restore Failed",
                    f"Failed to restore version {version}."
                )

# Example usage
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = RecoveryDialog()
    dialog.show()
    sys.exit(app.exec_()) 