import rumps
import subprocess
import os
import sys
from pathlib import Path
import json
from datetime import datetime

class BaddyAgentTray(rumps.App):
    def __init__(self):
        super(BaddyAgentTray, self).__init__("🤖", "Baddy Agent")
        self.menu = [
            rumps.MenuItem("Start Voice Trigger", callback=self.start_voice_trigger),
            rumps.MenuItem("Stop Voice Trigger", callback=self.stop_voice_trigger),
            rumps.MenuItem("Show Status", callback=self.show_status),
            rumps.MenuItem("View Logs", callback=self.view_logs),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        self.voice_process = None
        self.status = "Idle"
        self.last_command = None
        self.command_count = 0
        
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
    
    def show_status(self, _):
        status_info = {
            "Status": self.status,
            "Last Command": self.last_command or "None",
            "Commands Processed": self.command_count,
            "Uptime": self.get_uptime()
        }
        
        message = "\n".join(f"{k}: {v}" for k, v in status_info.items())
        rumps.notification(
            title="Baddy Agent Status",
            subtitle="Current Status",
            message=message
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
    
    def get_uptime(self):
        if self.voice_process is None:
            return "N/A"
        # Calculate uptime based on process start time
        return "Running"
    
    def quit_app(self, _):
        if self.voice_process is not None:
            self.stop_voice_trigger(None)
        rumps.quit_application()

if __name__ == "__main__":
    BaddyAgentTray().run() 