"""
Memory Dashboard for visualizing Samantha's memory and interaction history.
"""
import tkinter as tk
from tkinter import ttk
import json
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryDashboard:
    def __init__(self, root: tk.Tk = None):
        self.root = root or tk.Tk()
        self.root.title("Samantha's Memory Dashboard")
        self.root.geometry("800x600")
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize the dashboard UI components."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Create tabs
        self.memory_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        self.emotion_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.memory_tab, text="Memory Log")
        self.notebook.add(self.stats_tab, text="Statistics")
        self.notebook.add(self.emotion_tab, text="Emotional State")
        
        self._setup_memory_tab()
        self._setup_stats_tab()
        self._setup_emotion_tab()
        
    def _setup_memory_tab(self):
        """Set up the memory log tab."""
        # Create memory log text area
        self.memory_text = tk.Text(self.memory_tab, wrap=tk.WORD)
        self.memory_text.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.memory_tab, command=self.memory_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.memory_text.config(yscrollcommand=scrollbar.set)
        
        # Add filter frame
        filter_frame = ttk.Frame(self.memory_tab)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_entry = ttk.Entry(filter_frame)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(filter_frame, text="Apply Filter", 
                  command=self._apply_filter).pack(side=tk.LEFT)
        
    def _setup_stats_tab(self):
        """Set up the statistics tab."""
        # Create stats frame
        stats_frame = ttk.Frame(self.stats_tab)
        stats_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Add stats labels
        self.stats_labels = {}
        stats = [
            "Total Interactions",
            "Average Response Time",
            "Successful Commands",
            "Memory Usage",
            "Active Learning Rate"
        ]
        
        for i, stat in enumerate(stats):
            ttk.Label(stats_frame, text=f"{stat}:").grid(row=i, column=0, 
                                                        sticky=tk.W, pady=5)
            value_label = ttk.Label(stats_frame, text="0")
            value_label.grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
            self.stats_labels[stat] = value_label
            
    def _setup_emotion_tab(self):
        """Set up the emotional state visualization tab."""
        # Create emotion frame
        emotion_frame = ttk.Frame(self.emotion_tab)
        emotion_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Add emotion state visualization
        self.emotion_canvas = tk.Canvas(emotion_frame, width=400, height=300)
        self.emotion_canvas.pack(expand=True, fill="both")
        
        # Add emotion history
        self.emotion_history = ttk.Treeview(emotion_frame, columns=("Time", "Emotion", "Intensity"))
        self.emotion_history.heading("Time", text="Time")
        self.emotion_history.heading("Emotion", text="Emotion")
        self.emotion_history.heading("Intensity", text="Intensity")
        self.emotion_history.pack(expand=True, fill="both", pady=10)
        
    def update_memory_log(self, memory_data: Dict[str, Any]):
        """Update the memory log with new data."""
        try:
            # Clear existing text
            self.memory_text.delete(1.0, tk.END)
            
            # Format and insert memory data
            formatted_data = json.dumps(memory_data, indent=2)
            self.memory_text.insert(tk.END, formatted_data)
            
        except Exception as e:
            logger.error(f"Failed to update memory log: {str(e)}")
            
    def update_stats(self, stats_data: Dict[str, Any]):
        """Update statistics display."""
        try:
            for stat, value in stats_data.items():
                if stat in self.stats_labels:
                    self.stats_labels[stat].config(text=str(value))
                    
        except Exception as e:
            logger.error(f"Failed to update stats: {str(e)}")
            
    def update_emotion_state(self, emotion_data: Dict[str, Any]):
        """Update emotional state visualization."""
        try:
            # Clear canvas
            self.emotion_canvas.delete("all")
            
            # Draw emotion wheel
            self._draw_emotion_wheel(emotion_data)
            
            # Update emotion history
            self._update_emotion_history(emotion_data)
            
        except Exception as e:
            logger.error(f"Failed to update emotion state: {str(e)}")
            
    def _draw_emotion_wheel(self, emotion_data: Dict[str, Any]):
        """Draw the emotion wheel visualization."""
        # Implementation of emotion wheel visualization
        # This would show the current emotional state in a circular visualization
        center_x = 200
        center_y = 150
        radius = 100
        
        # Draw base circle
        self.emotion_canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="black"
        )
        
        # Draw emotion indicators
        if "current_emotion" in emotion_data:
            emotion = emotion_data["current_emotion"]
            intensity = emotion_data.get("intensity", 1.0)
            
            # Calculate position based on emotion
            angle = self._get_emotion_angle(emotion)
            distance = radius * intensity
            x = center_x + distance * cos(angle)
            y = center_y + distance * sin(angle)
            
            # Draw indicator
            self.emotion_canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill="red", outline="red"
            )
            
    def _update_emotion_history(self, emotion_data: Dict[str, Any]):
        """Update the emotion history treeview."""
        if "history" in emotion_data:
            # Clear existing items
            for item in self.emotion_history.get_children():
                self.emotion_history.delete(item)
                
            # Add new items
            for entry in emotion_data["history"]:
                self.emotion_history.insert("", "end", values=(
                    entry.get("time", ""),
                    entry.get("emotion", ""),
                    entry.get("intensity", "")
                ))
                
    def _apply_filter(self):
        """Apply filter to memory log."""
        filter_text = self.filter_entry.get().lower()
        
        # Get all text
        all_text = self.memory_text.get(1.0, tk.END)
        
        try:
            # Parse JSON
            data = json.loads(all_text)
            
            # Filter data
            filtered_data = self._filter_data(data, filter_text)
            
            # Update display
            self.memory_text.delete(1.0, tk.END)
            self.memory_text.insert(tk.END, json.dumps(filtered_data, indent=2))
            
        except json.JSONDecodeError:
            logger.error("Failed to parse memory data as JSON")
            
    def _filter_data(self, data: Any, filter_text: str) -> Any:
        """Recursively filter data structure."""
        if isinstance(data, dict):
            return {k: self._filter_data(v, filter_text) 
                   for k, v in data.items() 
                   if filter_text in str(k).lower() or 
                      filter_text in str(v).lower()}
        elif isinstance(data, list):
            return [item for item in data 
                   if filter_text in str(item).lower()]
        else:
            return data
            
    def run(self):
        """Start the dashboard."""
        self.root.mainloop()

def launch_memory_dashboard(memory_data: Dict[str, Any]) -> None:
    """Launch the memory dashboard with initial data."""
    try:
        dashboard = MemoryDashboard()
        dashboard.update_memory_log(memory_data)
        dashboard.run()
        
    except Exception as e:
        logger.error(f"Failed to launch memory dashboard: {str(e)}")
        raise 