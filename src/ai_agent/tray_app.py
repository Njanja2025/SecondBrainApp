import rumps
import subprocess
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import psutil
import platform

class BaddyAgentTray(rumps.App):
    def __init__(self):
        super(BaddyAgentTray, self).__init__("🤖", "Baddy Agent")
        self.menu = [
            rumps.MenuItem("Start Voice Trigger", callback=self.start_voice_trigger),
            rumps.MenuItem("Stop Voice Trigger", callback=self.stop_voice_trigger),
            None,  # Separator
            rumps.MenuItem("Activate Phantom Mode", callback=self.toggle_phantom_mode),
            rumps.MenuItem("System Status", callback=self.show_system_status),
            rumps.MenuItem("View Logs", callback=self.view_logs),
            None,  # Separator
            rumps.MenuItem("Settings", callback=self.show_settings),
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        self.voice_process = None
        self.phantom_process = None
        self.status = "Idle"
        self.last_command = None
        self.command_count = 0
        self.phantom_mode = False
        
    def start_voice_trigger(self, _):
        if self.voice_process is None:
            try:
                # Get the path to baddy_agent.py
                script_dir = Path(__file__).parent
                agent_path = script_dir / "baddy_agent.py"
                
                # Start the voice trigger process
                self.voice_process = subprocess.Popen(
                    [sys.executable, str(agent_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.status = "Running"
                self.title = "🤖"
                rumps.notification(
                    title="Baddy Agent",
                    subtitle="Voice Trigger Started",
                    message="Listening for commands..."
                )
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Failed to start voice trigger",
                    message=str(e)
                )
    
    def stop_voice_trigger(self, _):
        if self.voice_process is not None:
            self.voice_process.terminate()
            self.voice_process = None
            self.status = "Stopped"
            self.title = "🤖"
            rumps.notification(
                title="Baddy Agent",
                subtitle="Voice Trigger Stopped",
                message="Voice recognition disabled"
            )
    
    def toggle_phantom_mode(self, _):
        if not self.phantom_mode:
            try:
                script_dir = Path(__file__).parent
                phantom_path = script_dir / "phantom_mode.py"
                
                self.phantom_process = subprocess.Popen(
                    [sys.executable, str(phantom_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.phantom_mode = True
                rumps.notification(
                    title="Baddy Agent",
                    subtitle="Phantom Mode Activated",
                    message="Enhanced security and monitoring enabled"
                )
            except Exception as e:
                rumps.notification(
                    title="Error",
                    subtitle="Failed to activate Phantom Mode",
                    message=str(e)
                )
        else:
            if self.phantom_process is not None:
                self.phantom_process.terminate()
                self.phantom_process = None
            self.phantom_mode = False
            rumps.notification(
                title="Baddy Agent",
                subtitle="Phantom Mode Deactivated",
                message="Returned to normal operation"
            )
    
    def show_system_status(self, _):
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get Baddy Agent status
            agent_status = "Running" if self.voice_process is not None else "Stopped"
            phantom_status = "Active" if self.phantom_mode else "Inactive"
            
            status_info = {
                "Baddy Agent": agent_status,
                "Phantom Mode": phantom_status,
                "CPU Usage": f"{cpu_percent}%",
                "Memory Usage": f"{memory.percent}%",
                "Disk Usage": f"{disk.percent}%",
                "Last Command": self.last_command or "None",
                "Commands Processed": self.command_count
            }
            
            message = "\n".join(f"{k}: {v}" for k, v in status_info.items())
            rumps.notification(
                title="System Status",
                subtitle="Baddy Agent Status",
                message=message
            )
        except Exception as e:
            rumps.notification(
                title="Error",
                subtitle="Failed to get system status",
                message=str(e)
            )
    
    def view_logs(self, _):
        log_path = Path(__file__).parent.parent.parent / "logs" / "baddy_agent.log"
        if log_path.exists():
            # Open log file with default text editor
            subprocess.run(["open", str(log_path)])
        else:
            rumps.notification(
                title="Error",
                subtitle="Log file not found",
                message="No log file available"
            )
    
    def show_settings(self, _):
        settings_path = Path(__file__).parent / "config.yaml"
        if settings_path.exists():
            subprocess.run(["open", str(settings_path)])
        else:
            rumps.notification(
                title="Error",
                subtitle="Settings file not found",
                message="Configuration file not available"
            )
    
    def quit_app(self, _):
        if self.voice_process is not None:
            self.stop_voice_trigger(None)
        if self.phantom_process is not None:
            self.phantom_process.terminate()
        rumps.quit_application()

if __name__ == "__main__":
    BaddyAgentTray().run() 