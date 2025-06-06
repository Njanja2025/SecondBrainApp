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
        # Splash/boot screen for Phantom AI + Samantha intro
        splash = tk.Tk()
        splash.title("Phantom AI Boot")
        splash.geometry("400x300")
        splash.configure(bg="#111")
        splash_label = tk.Label(
            splash,
            text="Phantom AI\n+\nSamantha",
            font=("Helvetica", 28, "bold"),
            fg="#fff",
            bg="#111",
        )
        splash_label.pack(expand=True)
        splash.after(1800, splash.destroy)  # Show splash for 1.8 seconds
        splash.update()
        splash.mainloop()

        self.root = tk.Tk()
        self.root.title("SecondBrain")

        # Configure main window
        self.root.geometry("800x600")
        self.root.configure(bg="#2E2E2E")

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add title label
        title_label = ttk.Label(
            main_frame, text="SecondBrain Control Panel", font=("Helvetica", 24)
        )
        title_label.pack(pady=20)

        # Add status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add status indicators
        self._add_status_indicator(status_frame, "AI Agent", "Running")
        self._add_status_indicator(status_frame, "Memory Core", "Active")
        self._add_status_indicator(status_frame, "Voice Control", "Ready")

        # Add notebook for main panels
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Wealth MCP tab
        wealth_frame = ttk.Frame(notebook)
        ttk.Label(wealth_frame, text="Wealth MCP (Placeholder)").pack(padx=10, pady=10)
        notebook.add(wealth_frame, text="Wealth MCP")

        # Njax Studio/Vault tab
        studio_frame = ttk.Frame(notebook)
        ttk.Label(studio_frame, text="Njax Studio/Vault (Placeholder)").pack(padx=10, pady=10)
        notebook.add(studio_frame, text="Njax Studio/Vault")

        # Games tab
        games_frame = ttk.Frame(notebook)
        ttk.Label(games_frame, text="Games (Placeholder)").pack(padx=10, pady=10)
        notebook.add(games_frame, text="Games")

        # Njax Market tab with sidebar overview
        market_frame = ttk.Frame(notebook)
        sidebar = ttk.Frame(market_frame)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        ttk.Label(sidebar, text="Njax Market Overview (Sidebar Widget)").pack(padx=5, pady=5)
        main_market = ttk.Frame(market_frame)
        main_market.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        ttk.Label(main_market, text="Njax Market Homepage (Placeholder)").pack(padx=10, pady=10)
        notebook.add(market_frame, text="Njax Market")

        # Fire Base Studio (Blueprint Editor) tab
        fire_base_frame = ttk.Frame(notebook)
        ttk.Label(fire_base_frame, text="Fire Base Studio / Blueprint Editor (Placeholder)").pack(padx=10, pady=10)
        notebook.add(fire_base_frame, text="Fire Base Studio")

        # Agent Console (formerly BaddyAgent Integration)
        agent_panel = ttk.LabelFrame(main_frame, text="Agent Console")
        agent_panel.pack(fill=tk.X, padx=5, pady=10)
        # Status LED
        status_frame = ttk.Frame(agent_panel)
        status_frame.pack(anchor=tk.W, padx=5, pady=2)
        tk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        led_canvas = tk.Canvas(status_frame, width=18, height=18, highlightthickness=0)
        led = led_canvas.create_oval(2, 2, 16, 16, fill="green", outline="black")  # Default: green
        led_canvas.pack(side=tk.LEFT, padx=4)
        ttk.Label(agent_panel, text="Logs:").pack(anchor=tk.W, padx=5, pady=2)
        log_box = tk.Text(agent_panel, height=4, width=80)
        log_box.insert(tk.END, "[Log output will appear here]")
        log_box.config(state=tk.DISABLED)
        log_box.pack(padx=5, pady=2)
        ttk.Label(agent_panel, text="Command Queue:").pack(anchor=tk.W, padx=5, pady=2)
        queue_box = tk.Listbox(agent_panel, height=3, width=80)
        queue_box.insert(tk.END, "[Command queue placeholder]")
        queue_box.pack(padx=5, pady=2)
        # Manual/Auto toggles
        toggle_frame = ttk.Frame(agent_panel)
        toggle_frame.pack(anchor=tk.W, padx=5, pady=2)
        manual_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toggle_frame, text="Manual Override", variable=manual_var).pack(side=tk.LEFT)
        auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toggle_frame, text="Auto Mode", variable=auto_var).pack(side=tk.LEFT)

        # Theme toggle (Dark/Light) with stub logic
        theme_frame = ttk.Frame(main_frame)
        theme_frame.pack(fill=tk.X, pady=5)
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT, padx=5)
        theme_var = tk.StringVar(value="Dark")

        def apply_theme(*_):
            # Stub: implement real theme switching here
            if theme_var.get() == "Dark":
                self.root.configure(bg="#2E2E2E")
            else:
                self.root.configure(bg="#F0F0F0")

        ttk.Radiobutton(theme_frame, text="Dark", variable=theme_var, value="Dark", command=apply_theme).pack(side=tk.LEFT)
        ttk.Radiobutton(theme_frame, text="Light", variable=theme_var, value="Light", command=apply_theme).pack(side=tk.LEFT)

        # Emergency Controls Sidebar
        sidebar_panel = ttk.LabelFrame(main_frame, text="⚠️ Emergency Controls")
        sidebar_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, anchor=tk.N)
        pause_btn = ttk.Button(sidebar_panel, text="Pause Automations", command=lambda: self._set_emergency(True))
        pause_btn.pack(fill=tk.X, pady=2)
        export_btn = ttk.Button(sidebar_panel, text="Export System Snapshot", command=self._export_snapshot)
        export_btn.pack(fill=tk.X, pady=2)
        lockdown_var = tk.BooleanVar(value=False)
        lockdown_btn = ttk.Checkbutton(sidebar_panel, text="Agent Lockdown", variable=lockdown_var, command=lambda: self._set_emergency(lockdown_var.get()))
        lockdown_btn.pack(fill=tk.X, pady=2)

        # Red status bar (hidden unless emergency)
        self.status_bar = tk.Label(self.root, text="EMERGENCY MODE ACTIVE", bg="#B22222", fg="white", font=("Helvetica", 12, "bold"))
        self.status_bar.pack_forget()

        # Monetization Overlay Widget
        monet_panel = ttk.LabelFrame(main_frame, text="Monetization Dashboard")
        monet_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5, anchor=tk.N)
        ttk.Label(monet_panel, text="Daily Earnings: $123.45").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(monet_panel, text="Click-through Rate: 4.2%").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(monet_panel, text="Income Growth:").pack(anchor=tk.W, padx=5, pady=2)
        # Placeholder for income growth graph
        graph_canvas = tk.Canvas(monet_panel, width=120, height=40, bg="#f0f0f0")
        graph_canvas.create_line(10, 30, 30, 20, 50, 25, 70, 10, 110, 15, fill="#4CAF50", width=2, smooth=True)
        graph_canvas.pack(padx=5, pady=2)
        ttk.Label(monet_panel, text="(Njax product logs: placeholder)").pack(anchor=tk.W, padx=5, pady=2)

        # Add a section to embed Njax Market Overview PDF and Fire Base export PDF/PNGs
        embed_frame = ttk.LabelFrame(main_frame, text="Visual Blueprints & Market Overview")
        embed_frame.pack(fill=tk.X, padx=5, pady=10)
        ttk.Label(embed_frame, text="Njax Market Overview PDF: admin_dashboard_blueprint.pdf").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Button(embed_frame, text="Open PDF", command=lambda: self._open_file("admin_dashboard_blueprint.pdf")).pack(side=tk.LEFT, padx=5)
        ttk.Label(embed_frame, text="Fire Base Export PNG: admin_dashboard_blueprint.png").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Button(embed_frame, text="Open PNG", command=lambda: self._open_file("admin_dashboard_blueprint.png")).pack(side=tk.LEFT, padx=5)
        ttk.Label(embed_frame, text="Embed-ready Widget: admin_dashboard_widget.html").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Button(embed_frame, text="Open Widget", command=lambda: self._open_file("admin_dashboard_widget.html")).pack(side=tk.LEFT, padx=5)

        # Agent Console Sidebar
        agent_sidebar = ttk.LabelFrame(self.root, text="Agent Console", padding=8)
        agent_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8, anchor=tk.N)
        # Status LED
        led_frame = ttk.Frame(agent_sidebar)
        led_frame.pack(anchor=tk.W, pady=4)
        tk.Label(led_frame, text="Status:").pack(side=tk.LEFT)
        self.agent_status = tk.StringVar(value="green")
        self.led_canvas = tk.Canvas(led_frame, width=18, height=18, highlightthickness=0)
        self.led_oval = self.led_canvas.create_oval(2, 2, 16, 16, fill="green", outline="black")
        self.led_canvas.pack(side=tk.LEFT, padx=4)
        # Control toggles
        self.auto_mode = tk.BooleanVar(value=False)
        self.manual_override = tk.BooleanVar(value=True)
        auto_toggle = ttk.Checkbutton(agent_sidebar, text="Auto Mode", variable=self.auto_mode, command=self._on_agent_toggle)
        manual_toggle = ttk.Checkbutton(agent_sidebar, text="Manual Override", variable=self.manual_override, command=self._on_agent_toggle)
        auto_toggle.pack(anchor=tk.W, pady=2)
        manual_toggle.pack(anchor=tk.W, pady=2)
        # Logs preview
        ttk.Label(agent_sidebar, text="Logs (last 10 events):").pack(anchor=tk.W, pady=2)
        self.agent_log_box = tk.Text(agent_sidebar, height=6, width=28, state=tk.DISABLED)
        self.agent_log_box.pack(padx=2, pady=2)

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

    def _set_emergency(self, active):
        self.emergency_active.set(active)
        if active:
            self.status_bar.pack(fill=tk.X, side=tk.TOP)
        else:
            self.status_bar.pack_forget()

    def _export_snapshot(self):
        # Placeholder for export logic
        import tkinter.messagebox as mb
        mb.showinfo("Export", "System snapshot exported (placeholder)")

    def _open_file(self, filename):
        import os
        import subprocess
        if os.path.exists(filename):
            if filename.endswith('.pdf') or filename.endswith('.png'):
                subprocess.Popen(["open", filename])  # macOS; use 'xdg-open' for Linux, 'start' for Windows
            else:
                subprocess.Popen(["open", filename])
        else:
            import tkinter.messagebox as mb
            mb.showerror("File Not Found", f"{filename} not found.")

    def _on_agent_toggle(self):
        # Update LED color based on toggles
        color = "green" if self.auto_mode.get() else ("yellow" if self.manual_override.get() else "red")
        self.led_canvas.itemconfig(self.led_oval, fill=color)
        # Log the event
        self._append_agent_log(f"Toggles changed: Auto={self.auto_mode.get()}, Manual={self.manual_override.get()}")
        # Voice sync with Samantha (placeholder)
        self._voice_sync_with_samantha()

    def _append_agent_log(self, msg):
        self.agent_log_box.config(state=tk.NORMAL)
        self.agent_log_box.insert(tk.END, msg + "\n")
        lines = self.agent_log_box.get("1.0", tk.END).splitlines()
        if len(lines) > 10:
            self.agent_log_box.delete("1.0", f"{len(lines)-10}.0")
        self.agent_log_box.config(state=tk.DISABLED)

    def _voice_sync_with_samantha(self):
        # Placeholder for voice sync logic
        import threading
        import os
        def speak():
            os.system('say "Agent Console toggles updated. Samantha synced."')
        threading.Thread(target=speak, daemon=True).start()
