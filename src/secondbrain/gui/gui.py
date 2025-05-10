"""
GUI implementation for SecondBrain
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class GUI:
    """GUI interface for SecondBrain."""
    
    def __init__(self):
        """Initialize the GUI."""
        self.root: Optional[tk.Tk] = None
        self.running = False
        
    def start(self):
        """Start the GUI."""
        logger.info("Starting GUI...")
        self.running = True
        self.root = tk.Tk()
        self.root.title("SecondBrain")
        
        # Configure main window
        self.root.geometry("800x600")
        self.root.configure(bg='#2E2E2E')
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add title label
        title_label = ttk.Label(
            main_frame,
            text="SecondBrain Control Panel",
            font=("Helvetica", 24)
        )
        title_label.pack(pady=20)
        
        # Add status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add status indicators
        self._add_status_indicator(status_frame, "AI Agent", "Running")
        self._add_status_indicator(status_frame, "Memory Core", "Active")
        self._add_status_indicator(status_frame, "Voice Control", "Ready")
        
        # Start the main loop
        self.root.mainloop()
        
    def stop(self):
        """Stop the GUI."""
        logger.info("Stopping GUI...")
        self.running = False
        if self.root:
            self.root.quit()
            
    def _add_status_indicator(self, parent: ttk.Frame, label: str, status: str):
        """Add a status indicator to the parent frame."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        label = ttk.Label(frame, text=f"{label}:")
        label.pack(side=tk.LEFT)
        
        status_label = ttk.Label(frame, text=status)
        status_label.pack(side=tk.RIGHT) 