"""
Dashboard for viewing cloud operation reports.
"""
import os
import logging
import webbrowser
from pathlib import Path
from typing import Optional
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

logger = logging.getLogger(__name__)

class ReportDashboard:
    """Dashboard for viewing cloud operation reports."""
    
    def __init__(self, report_dir: str = "phantom_reports"):
        """Initialize dashboard."""
        self.report_dir = Path(report_dir)
        self.root = tk.Tk()
        self.root.title("SecondBrain Cloud Operations Dashboard")
        self.root.geometry("800x600")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dashboard UI."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(
            main_frame,
            text="Cloud Operations Dashboard",
            font=("Arial", 20)
        )
        title.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Report list
        self.report_list = tk.Listbox(
            main_frame,
            width=70,
            height=20
        )
        self.report_list.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Buttons
        refresh_btn = ttk.Button(
            main_frame,
            text="Refresh Reports",
            command=self.refresh_reports
        )
        refresh_btn.grid(row=2, column=0, pady=10, padx=5)
        
        view_btn = ttk.Button(
            main_frame,
            text="View Selected Report",
            command=self.view_selected_report
        )
        view_btn.grid(row=2, column=1, pady=10, padx=5)
        
        # Load initial reports
        self.refresh_reports()
    
    def refresh_reports(self):
        """Refresh the list of available reports."""
        try:
            self.report_list.delete(0, tk.END)
            
            if not self.report_dir.exists():
                logger.warning(f"Report directory not found: {self.report_dir}")
                return
            
            reports = sorted(
                [f for f in self.report_dir.glob("*.pdf")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for report in reports:
                timestamp = datetime.fromtimestamp(report.stat().st_mtime)
                display_name = f"{report.name} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                self.report_list.insert(tk.END, display_name)
            
        except Exception as e:
            logger.error(f"Failed to refresh reports: {e}")
            messagebox.showerror("Error", f"Failed to refresh reports: {e}")
    
    def view_selected_report(self):
        """Open the selected report in the default PDF viewer."""
        try:
            selection = self.report_list.curselection()
            if not selection:
                messagebox.showinfo("Info", "Please select a report to view")
                return
            
            report_name = self.report_list.get(selection[0]).split(" - ")[0]
            report_path = self.report_dir / report_name
            
            if not report_path.exists():
                messagebox.showerror("Error", f"Report file not found: {report_path}")
                return
            
            webbrowser.open(str(report_path))
            
        except Exception as e:
            logger.error(f"Failed to open report: {e}")
            messagebox.showerror("Error", f"Failed to open report: {e}")
    
    def run(self):
        """Run the dashboard."""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            raise

def launch_dashboard():
    """Launch the report dashboard."""
    dashboard = ReportDashboard()
    dashboard.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    launch_dashboard() 