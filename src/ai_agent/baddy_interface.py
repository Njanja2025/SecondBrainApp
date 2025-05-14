import tkinter as tk
import threading
import time
import os
import webbrowser
import platform

def monitor_tasks(task_file="src/ai_agent/agent_tasks.txt"):
    with open(task_file, "r") as file:
        lines = file.readlines()

    new_tasks = [line.strip() for line in lines if line.strip()]

    for command in new_tasks:
        if command.lower() == "status":
            print("[Baddy] System is stable. All agents online.")
        elif command.lower() == "stealth scan":
            print("[Baddy] Initiating stealth scan...")
            from stealth_scanner import scan_system
            logs = scan_system()
            for log in logs:
                print(log)
        elif command.lower() == "launch njax market":
            print("[Baddy] Syncing Njax Market module...")
            webbrowser.open("https://njanja.net/njax-market")
        else:
            print(f"[Baddy] Unrecognized command: {command}")

    # Clear the task file after processing
    with open(task_file, "w") as file:
        file.write("")

def execute_task(task):
    print(f"[Baddy] Task received: {task}")
    if "njax" in task.lower():
        print("[Baddy] Syncing Njax Market module...")
        os.system("open https://njanja.net/njaxmarket")
    elif "status" in task.lower():
        print("[Baddy] System is stable. All agents online.")
    elif "stealth" in task.lower():
        print("[Baddy] Initiating stealth scan...")
        os.system("python3 src/ai_agent/stealth_scanner.py")
    else:
        print(f"[Baddy] Unknown command: {task}")

class BaddyInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Baddy Agent Console")
        
        # Create text widget with scrollbar
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = tk.Scrollbar(self.frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.textbox = tk.Text(self.frame, height=25, width=80, bg="black", fg="lime",
                             yscrollcommand=self.scrollbar.set)
        self.textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.textbox.yview)
        
        self.start_interface()

    def start_interface(self):
        self.print_to_console("[BADDY] Agent interface online. Listening for tasks...")
        threading.Thread(target=self.task_listener, daemon=True).start()

    def print_to_console(self, text):
        self.textbox.insert(tk.END, text + "\n")
        self.textbox.see(tk.END)

    def task_listener(self):
        while True:
            try:
                with open("src/ai_agent/agent_tasks.txt", "r+") as f:
                    lines = f.readlines()
                    f.seek(0)
                    f.truncate()
                for line in lines:
                    task = line.strip()
                    if task:
                        self.print_to_console(f"[BADDY] Received task: {task}")
                        if task.lower() == "stealth scan":
                            from stealth_scanner import scan_system
                            for log in scan_system():
                                self.print_to_console(log)
                        elif task.lower() == "launch njax market":
                            self.print_to_console("[BADDY] Launching Njax Market...")
                            webbrowser.open("https://njanja.net/njax-market")
                        elif task.lower() == "status":
                            self.print_to_console("[BADDY] System is stable. All agents online.")
                        else:
                            self.print_to_console(f"[BADDY] Task '{task}' sent to core.")
            except Exception as e:
                self.print_to_console(f"[ERROR] {e}")
            finally:
                time.sleep(3)

def launch_gui():
    if platform.system() == "Darwin":  # macOS
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
    root = tk.Tk()
    app = BaddyInterface(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui() 