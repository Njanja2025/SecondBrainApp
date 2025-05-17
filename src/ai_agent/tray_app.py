import rumps
import psutil
import platform
import subprocess
import json
from pathlib import Path
import webbrowser
from datetime import datetime
import os

class BaddyAgentTray(rumps.App):
    def __init__(self):
        super(BaddyAgentTray, self).__init__("🤖", "Baddy Agent")
        self.voice_active = False
        self.phantom_mode = False
        self.setup_menu()
        self.load_config()
        
    def setup_menu(self):
        """Setup the tray menu structure"""
        self.menu = [
            rumps.MenuItem("Start Voice", callback=self.toggle_voice),
            rumps.MenuItem("Activate Phantom Mode", callback=self.toggle_phantom),
            rumps.MenuItem("System Status", callback=self.show_status),
            None,  # Separator
            rumps.MenuItem("Quick Access", [
                rumps.MenuItem("Open Logs", callback=self.open_logs),
                rumps.MenuItem("Run Diagnostics", callback=self.run_diagnostics),
                rumps.MenuItem("Launch Dashboard", callback=self.launch_dashboard),
                rumps.MenuItem("GitHub Repository", callback=self.open_github),
                rumps.MenuItem("Web Console", callback=self.open_web_console)
            ]),
            rumps.MenuItem("Actions", [
                rumps.MenuItem("Sync Now", callback=self.sync_now),
                rumps.MenuItem("Recovery Mode", callback=self.recovery_mode),
                rumps.MenuItem("Shutdown", callback=self.shutdown)
            ]),
            None,  # Separator
            rumps.MenuItem("Settings", callback=self.open_settings),
            rumps.MenuItem("About", callback=self.show_about)
        ]
        
    def load_config(self):
        """Load configuration from JSON file"""
        config_path = Path(__file__).parent / "baddy_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "github_repo": "https://github.com/Njanja2025/SecondBrainApp",
                "web_console": "http://localhost:8080",
                "log_path": str(Path(__file__).parent.parent.parent / "logs"),
                "dashboard_port": 8080
            }
            
    def toggle_voice(self, _):
        """Toggle voice activation"""
        if not self.voice_active:
            subprocess.Popen(["python3", "src/ai_agent/voice_trigger.py"])
            self.voice_active = True
            self.menu["Start Voice"].title = "Stop Voice"
            rumps.notification("Baddy Agent", "", "Voice activation started")
        else:
            subprocess.run(["pkill", "-f", "voice_trigger.py"])
            self.voice_active = False
            self.menu["Start Voice"].title = "Start Voice"
            rumps.notification("Baddy Agent", "", "Voice activation stopped")
            
    def toggle_phantom(self, _):
        """Toggle Phantom Mode"""
        self.phantom_mode = not self.phantom_mode
        if self.phantom_mode:
            self.menu["Activate Phantom Mode"].title = "Deactivate Phantom Mode"
            rumps.notification("Baddy Agent", "", "Phantom Mode activated")
        else:
            self.menu["Activate Phantom Mode"].title = "Activate Phantom Mode"
            rumps.notification("Baddy Agent", "", "Phantom Mode deactivated")
            
    def show_status(self, _):
        """Show system status"""
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status = f"""
System Status:
CPU Usage: {cpu}%
Memory Usage: {memory.percent}%
Disk Usage: {disk.percent}%
Voice Active: {'Yes' if self.voice_active else 'No'}
Phantom Mode: {'Active' if self.phantom_mode else 'Inactive'}
        """
        rumps.notification("Baddy Agent Status", "", status)
        
    def open_logs(self, _):
        """Open log directory"""
        log_path = Path(self.config["log_path"])
        if log_path.exists():
            subprocess.run(["open", str(log_path)])
            
    def run_diagnostics(self, _):
        """Run system diagnostics"""
        try:
            # Run diagnostics script
            subprocess.run(["python3", "src/ai_agent/diagnostics.py"])
            rumps.notification("Baddy Agent", "", "Diagnostics completed")
        except Exception as e:
            rumps.notification("Baddy Agent", "Error", str(e))
            
    def launch_dashboard(self, _):
        """Launch web dashboard"""
        try:
            subprocess.Popen(["python3", "src/ai_agent/dashboard.py"])
            webbrowser.open(f"http://localhost:{self.config['dashboard_port']}")
        except Exception as e:
            rumps.notification("Baddy Agent", "Error", str(e))
            
    def open_github(self, _):
        """Open GitHub repository"""
        webbrowser.open(self.config["github_repo"])
        
    def open_web_console(self, _):
        """Open web console"""
        webbrowser.open(self.config["web_console"])
        
    def sync_now(self, _):
        """Trigger immediate sync"""
        try:
            subprocess.run(["python3", "src/ai_agent/sync.py"])
            rumps.notification("Baddy Agent", "", "Sync completed")
        except Exception as e:
            rumps.notification("Baddy Agent", "Error", str(e))
            
    def recovery_mode(self, _):
        """Enter recovery mode"""
        try:
            subprocess.run(["python3", "src/ai_agent/recovery.py"])
            rumps.notification("Baddy Agent", "", "Recovery mode activated")
        except Exception as e:
            rumps.notification("Baddy Agent", "Error", str(e))
            
    def shutdown(self, _):
        """Graceful shutdown"""
        if rumps.alert("Confirm Shutdown", "Are you sure you want to shutdown Baddy Agent?", "Yes", "No"):
            try:
                # Stop voice trigger if running
                if self.voice_active:
                    subprocess.run(["pkill", "-f", "voice_trigger.py"])
                    
                # Run cleanup
                subprocess.run(["python3", "src/ai_agent/cleanup.py"])
                
                # Quit the app
                rumps.quit_application()
            except Exception as e:
                rumps.notification("Baddy Agent", "Error", str(e))
                
    def open_settings(self, _):
        """Open settings"""
        settings_path = Path(__file__).parent / "baddy_config.json"
        if settings_path.exists():
            subprocess.run(["open", str(settings_path)])
            
    def show_about(self, _):
        """Show about information"""
        about = """
Baddy Agent v1.0
Launch-Ready Edition

© 2024 Njanja2025
All rights reserved
        """
        rumps.notification("About Baddy Agent", "", about)

if __name__ == "__main__":
    BaddyAgentTray().run() 