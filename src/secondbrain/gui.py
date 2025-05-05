import logging
import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Any, Callable
import json
import os
from datetime import datetime
import platform

logger = logging.getLogger(__name__)

class Hotkey:
    """Hotkey configuration for different platforms."""
    def __init__(self, windows: str, mac: str, linux: str, description: str):
        self.windows = windows
        self.mac = mac
        self.linux = linux
        self.description = description
        
    def get_for_platform(self) -> str:
        """Get the appropriate hotkey for the current platform."""
        if platform.system() == "Darwin":
            return self.mac
        elif platform.system() == "Windows":
            return self.windows
        return self.linux

class GUI:
    """Handles the graphical user interface for SecondBrain."""
    
    # Define hotkeys
    HOTKEYS = {
        "toggle_voice": Hotkey("Ctrl+Shift+V", "Command+Shift+V", "Ctrl+Shift+V", "Toggle voice input"),
        "clear": Hotkey("Ctrl+L", "Command+L", "Ctrl+L", "Clear conversation"),
        "save": Hotkey("Ctrl+S", "Command+S", "Ctrl+S", "Save conversation"),
        "theme": Hotkey("Ctrl+T", "Command+T", "Ctrl+T", "Toggle theme"),
        "quit": Hotkey("Ctrl+Q", "Command+Q", "Ctrl+Q", "Quit application"),
        "help": Hotkey("F1", "F1", "F1", "Show help"),
    }
    
    def __init__(self):
        self._running = False
        self.root = None
        self.text_area = None
        self.status_label = None
        self.input_entry = None
        self.conversation_history = []
        self.voice_enabled = True
        self.load_settings()
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        self.root.bind(self.HOTKEYS["toggle_voice"].get_for_platform(), self.toggle_voice)
        self.root.bind(self.HOTKEYS["clear"].get_for_platform(), lambda e: self.clear_conversation())
        self.root.bind(self.HOTKEYS["save"].get_for_platform(), lambda e: self.save_conversation())
        self.root.bind(self.HOTKEYS["theme"].get_for_platform(), lambda e: self.toggle_theme())
        self.root.bind(self.HOTKEYS["quit"].get_for_platform(), lambda e: self.root.quit())
        self.root.bind(self.HOTKEYS["help"].get_for_platform(), lambda e: self.show_help())
        
        # Bind Enter key to send message
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        
    def toggle_voice(self, event=None):
        """Toggle voice input on/off."""
        self.voice_enabled = not self.voice_enabled
        status = "enabled" if self.voice_enabled else "disabled"
        self.mic_status.config(text=f"🎤 {'Listening' if self.voice_enabled else 'Muted'}")
        self.show_notification(f"Voice input {status}")
        
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        new_theme = "dark" if self.settings["theme"] == "light" else "light"
        self.change_theme(new_theme)
        
    def show_help(self):
        """Show help dialog with keyboard shortcuts."""
        help_text = "Keyboard Shortcuts:\n\n"
        for name, hotkey in self.HOTKEYS.items():
            help_text += f"{hotkey.get_for_platform()}: {hotkey.description}\n"
        
        messagebox.showinfo("Keyboard Shortcuts", help_text)
        
    def show_notification(self, message: str):
        """Show a temporary notification in the status bar."""
        original_text = self.status_label.cget("text")
        self.status_label.config(text=message)
        self.root.after(2000, lambda: self.status_label.config(text=original_text))
        
    def load_settings(self):
        """Load GUI settings from file."""
        self.settings = {
            "theme": "light",
            "font_size": 10,
            "max_history": 100
        }
        try:
            if os.path.exists("gui_settings.json"):
                with open("gui_settings.json", "r") as f:
                    self.settings.update(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            
    def save_settings(self):
        """Save GUI settings to file."""
        try:
            with open("gui_settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
        
    async def initialize(self):
        """Initialize the GUI components."""
        logger.info("Initializing GUI...")
        self.root = tk.Tk()
        self.root.title("SecondBrain Assistant")
        self.root.geometry("800x600")
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create menu bar with shortcut hints
        self.create_menu()
        
        # Create conversation display
        self.create_conversation_display()
        
        # Create input area
        self.create_input_area()
        
        # Create status bar
        self.create_status_bar()
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Apply theme
        self.apply_theme()
        
    def create_menu(self):
        """Create menu bar with options and shortcut hints."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Save Conversation",
            command=self.save_conversation,
            accelerator=self.HOTKEYS["save"].get_for_platform()
        )
        file_menu.add_command(
            label="Clear Conversation",
            command=self.clear_conversation,
            accelerator=self.HOTKEYS["clear"].get_for_platform()
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self.root.quit,
            accelerator=self.HOTKEYS["quit"].get_for_platform()
        )
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Toggle Theme",
            command=self.toggle_theme,
            accelerator=self.HOTKEYS["theme"].get_for_platform()
        )
        view_menu.add_separator()
        view_menu.add_command(
            label="Toggle Voice",
            command=self.toggle_voice,
            accelerator=self.HOTKEYS["toggle_voice"].get_for_platform()
        )
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="Keyboard Shortcuts",
            command=self.show_help,
            accelerator=self.HOTKEYS["help"].get_for_platform()
        )
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_conversation_display(self):
        """Create the conversation display area."""
        # Create conversation frame
        conv_frame = ttk.LabelFrame(self.main_frame, text="Conversation", padding="5")
        conv_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Create scrolled text area
        self.text_area = scrolledtext.ScrolledText(
            conv_frame, 
            wrap=tk.WORD, 
            height=20,
            font=("TkDefaultFont", self.settings["font_size"])
        )
        self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.text_area.config(state='disabled')
        
    def create_input_area(self):
        """Create the input area for manual text entry."""
        input_frame = ttk.Frame(self.main_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        send_button = ttk.Button(
            input_frame, 
            text="Send", 
            command=self.send_message
        )
        send_button.grid(row=0, column=1, padx=5)
        
        input_frame.columnconfigure(0, weight=1)
        
    def create_status_bar(self):
        """Create the status bar."""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Status: Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.mic_status = ttk.Label(status_frame, text="🎤 Listening")
        self.mic_status.grid(row=0, column=1, sticky=tk.E)
        
    def apply_theme(self):
        """Apply the current theme."""
        if self.settings["theme"] == "dark":
            self.root.configure(bg='#2b2b2b')
            style = ttk.Style()
            style.configure("TFrame", background='#2b2b2b')
            style.configure("TLabel", background='#2b2b2b', foreground='#ffffff')
            self.text_area.configure(
                bg='#1e1e1e',
                fg='#ffffff',
                insertbackground='#ffffff'
            )
        else:
            self.root.configure(bg='#ffffff')
            style = ttk.Style()
            style.configure("TFrame", background='#ffffff')
            style.configure("TLabel", background='#ffffff', foreground='#000000')
            self.text_area.configure(
                bg='#ffffff',
                fg='#000000',
                insertbackground='#000000'
            )
            
    def change_theme(self, theme):
        """Change the GUI theme."""
        self.settings["theme"] = theme
        self.apply_theme()
        self.save_settings()
        
    def save_conversation(self):
        """Save the conversation history to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.txt"
        try:
            with open(filename, "w") as f:
                f.write(self.text_area.get("1.0", tk.END))
            messagebox.showinfo("Success", f"Conversation saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save conversation: {e}")
            
    def clear_conversation(self):
        """Clear the conversation history."""
        if messagebox.askyesno("Confirm", "Clear entire conversation?"):
            self.text_area.config(state='normal')
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(state='disabled')
            self.conversation_history.clear()
            
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About SecondBrain",
            "SecondBrain Assistant\n\n"
            "An AI-powered voice assistant that helps you think and work better.\n\n"
            "Version: 1.0.0"
        )
        
    def send_message(self):
        """Handle manual message sending."""
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, tk.END)
            self.display_response(f"You: {text}", is_user=True)
            
    async def start(self):
        """Start the GUI event loop."""
        logger.info("Starting GUI...")
        self._running = True
        self.status_label.config(text="Status: Running")
        
        # Schedule GUI update in the event loop
        asyncio.create_task(self._update_gui())
        
    async def shutdown(self):
        """Shutdown the GUI cleanly."""
        logger.info("Shutting down GUI...")
        self._running = False
        self.status_label.config(text="Status: Shutting down...")
        if self.root:
            self.save_settings()
            self.root.quit()
            
    async def _update_gui(self):
        """Update the GUI in the background."""
        while self._running:
            self.root.update()
            await asyncio.sleep(0.1)
            
    def display_response(self, response: str, is_user: bool = False):
        """Display a response in the GUI."""
        if self._running and self.text_area:
            logger.info(f"Displaying response: {response}")
            
            # Format timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Format message
            if is_user:
                formatted_msg = f"[{timestamp}] 👤 {response}\n"
            else:
                formatted_msg = f"[{timestamp}] 🤖 Assistant: {response}\n"
            
            # Add to conversation history
            self.conversation_history.append({
                'timestamp': timestamp,
                'text': response,
                'is_user': is_user
            })
            
            # Trim history if needed
            if len(self.conversation_history) > self.settings["max_history"]:
                self.conversation_history.pop(0)
            
            # Update display
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, formatted_msg)
            self.text_area.see(tk.END)
            self.text_area.config(state='disabled')
        else:
            logger.warning("Attempted to display response while GUI is not running") 