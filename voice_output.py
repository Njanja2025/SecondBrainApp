import os
import platform
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import time
from datetime import datetime
import json

# Configuration
CONFIG_FILE = "voice_config.json"
LOG_FILE = "phantom_logs/voice_output.log"

class VoiceSystem:
    def __init__(self):
        self.load_config()
        self.setup_gui()
    
    def load_config(self):
        """Load or create default configuration."""
        default_config = {
            "muted": False,
            "voice_rate": 175,
            "selected_voice": "Alex"  # Default macOS voice
        }
        
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    # Ensure all default keys exist
                    self.config = default_config.copy()
                    self.config.update(loaded_config)
            else:
                self.config = default_config
                self.save_config()
        except:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save current configuration."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def log_voice(self, text, status):
        """Log voice output attempts with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as log:
            log.write(f"{timestamp} | {status} | {text}\n")

    def get_available_voices(self):
        """Get list of available macOS voices."""
        try:
            result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
            voices = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    voice_name = line.split()[0]
                    voices.append(voice_name)
            return voices if voices else ["Alex"]
        except:
            return ["Alex"]  # Default fallback

    def speak(self, text):
        """Voice output system using macOS say."""
        if self.config["muted"]:
            self.log_voice(text, "muted")
            return

        if platform.system() != "Darwin":
            self.log_voice(text, "error: not macOS")
            messagebox.showwarning("Voice Output Failed", "This system only works on macOS")
            return

        try:
            cmd = ['say']
            if self.config["selected_voice"]:
                cmd.extend(['-v', self.config["selected_voice"]])
            if self.config["voice_rate"]:
                cmd.extend(['-r', str(self.config["voice_rate"])])
            cmd.append(text)
            
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                self.log_voice(text, f"macOS say ({self.config['selected_voice']})")
                return
        except Exception as e:
            print(f"[Voice Error] {e}")

        # Fallback: beep and alert box
        try:
            print('\a')  # System beep
            messagebox.showwarning("Voice Output Failed", f"Assistant says: {text}")
            self.log_voice(text, "popup alert")
        except Exception as e:
            print(f"[Popup alert failed] {e}")
            self.log_voice(text, "no output")

    def setup_gui(self):
        """Create control GUI window."""
        self.window = tk.Tk()
        self.window.title("Voice Control Panel")
        self.window.geometry("300x500")
        
        # Mute toggle
        self.mute_var = tk.BooleanVar(value=self.config["muted"])
        ttk.Checkbutton(
            self.window, 
            text="Mute Voice Output", 
            variable=self.mute_var,
            command=self.toggle_mute
        ).pack(pady=10)

        # Voice selection
        ttk.Label(self.window, text="Select Voice").pack(pady=5)
        self.voices = self.get_available_voices()
        self.voice_var = tk.StringVar(value=self.config["selected_voice"])
        voice_combo = ttk.Combobox(
            self.window,
            textvariable=self.voice_var,
            values=self.voices,
            state="readonly"
        )
        voice_combo.pack(pady=5)
        voice_combo.bind('<<ComboboxSelected>>', lambda e: self.update_voice())

        # Voice rate slider
        ttk.Label(self.window, text="Voice Speed").pack(pady=5)
        self.rate_var = tk.IntVar(value=self.config["voice_rate"])
        ttk.Scale(
            self.window,
            from_=100,
            to=250,
            variable=self.rate_var,
            command=self.update_rate
        ).pack(pady=5)

        # Test voice button
        ttk.Button(
            self.window,
            text="Test Voice",
            command=lambda: self.speak("Voice system test successful")
        ).pack(pady=10)

        # Save settings button
        ttk.Button(
            self.window,
            text="Save Settings",
            command=self.save_settings
        ).pack(pady=10)

        # Status display
        self.status_text = tk.Text(self.window, height=5, width=35)
        self.status_text.pack(pady=10)
        self.update_status()

    def toggle_mute(self):
        """Toggle mute state."""
        self.config["muted"] = self.mute_var.get()
        self.save_config()
        self.update_status()

    def update_voice(self):
        """Update selected voice."""
        self.config["selected_voice"] = self.voice_var.get()
        self.save_config()
        self.update_status()

    def update_rate(self, value):
        """Update voice rate."""
        self.config["voice_rate"] = int(float(value))
        self.save_config()
        self.update_status()

    def save_settings(self):
        """Save current GUI settings."""
        self.save_config()
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.update_status()

    def update_status(self):
        """Update status display."""
        self.status_text.delete(1.0, tk.END)
        status = f"Status:\n"
        status += f"Muted: {'Yes' if self.config['muted'] else 'No'}\n"
        status += f"Selected Voice: {self.config['selected_voice']}\n"
        status += f"Voice Speed: {self.config['voice_rate']}"
        self.status_text.insert(tk.END, status)

def get_voice_system():
    """Get or create the voice system instance."""
    if not hasattr(get_voice_system, "instance"):
        get_voice_system.instance = VoiceSystem()
    return get_voice_system.instance

# Global speak function for backwards compatibility
def speak(text):
    get_voice_system().speak(text)

# Test block
if __name__ == "__main__":
    voice_system = get_voice_system()
    voice_system.speak("Second Brain voice system is fully active.")
    voice_system.window.mainloop() 