import time
import os
import traceback
import re
import platform
import yaml
import threading
from contextlib import contextmanager
import smtplib
import ssl
import json
from email.message import EmailMessage
try:
    import psutil
except ImportError:
    psutil = None
try:
    import requests
except ImportError:
    requests = None
import openai
import importlib.util
import glob
import subprocess
import sys
import logging

# Try to import plugins, but don't fail if they don't exist
try:
    from plugins import load_plugins
except ImportError:
    def load_plugins():
        """Placeholder for plugin loading when plugins module is not available."""
        log("[PLUGINS] No plugins module found. Running without plugins.")

# Constants
TASK_FILE = "src/ai_agent/agent_tasks.txt"
LOG_FILE = "logs/baddy_agent.log"
VERSION = "1.1.0"
CLAUD_SYNC_FILE = "logs/claud_last_sync.txt"
REMOTE_VERSION = "1.2.0"  # Simulated remote version
CONFIG_FILE = "src/ai_agent/config.yaml"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def log(message):
    """Log a message to both file and console."""
    logging.info(message)

# File locking context manager
@contextmanager
def locked_file(filename, mode):
    lock = threading.Lock()
    with lock:
        with open(filename, mode) as f:
            yield f

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            log(f"[Baddy] Failed to load config: {e}")
    return config

config = load_config()
CLAUD_SYNC_ENDPOINT = os.environ.get("CLAUD_SYNC_ENDPOINT", config.get("claud_sync_endpoint", "https://example.com/api/sync"))
CLAUD_UPGRADE_ENDPOINT = os.environ.get("CLAUD_UPGRADE_ENDPOINT", config.get("claud_upgrade_endpoint", "https://example.com/api/version"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", config.get("openai_api_key", ""))
openai.api_key = OPENAI_API_KEY

# Command registry for extensibility
def handle_status():
    log("[Baddy] System is stable. All agents online.")

def handle_stealth_scan():
    log("[Stealth] Scanning system files for anomalies.")

def handle_launch_njax_market():
    log("[Baddy] Syncing Njax Market module...")

def handle_build_drone():
    log("[Drone] Generating drone blueprint now...")

def handle_defend():
    log("[Phantom] Activating defense protocols!")
    phantom_protocol()

def handle_launch_njax_engineering():
    log("[Baddy] Syncing Njax Engineering module...")

def handle_phantom_lockdown():
    log("[Phantom] Lockdown initiated. Securing all systems.")
    phantom_protocol(lockdown=True)

def handle_system_health():
    # Stub: Replace with real system health check
    log("[Health] System health is optimal. No issues detected.")

def handle_version():
    log(f"[Baddy] Agent version: {VERSION}")

def handle_claud_analyze():
    error_count = 0
    warning_count = 0
    sys_snapshot = ""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                for line in f:
                    if re.search(r"error", line, re.IGNORECASE):
                        error_count += 1
                    if re.search(r"warn", line, re.IGNORECASE):
                        warning_count += 1
        # System resource snapshot
        if psutil:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory().percent
            sys_snapshot = f"CPU: {cpu}%, MEM: {mem}%"
        else:
            sys_snapshot = "psutil not installed"
        log(f"[CLAUD] Log analysis: {error_count} errors, {warning_count} warnings. {sys_snapshot}")
    except Exception as e:
        log(f"[CLAUD] Analyze failed: {e}")

def handle_claud_summarize():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-10:]
            summary = " | ".join(line.strip() for line in lines)
            log(f"[CLAUD] Last 10 log entries: {summary}")
        else:
            log("[CLAUD] No log entries to summarize.")
    except Exception as e:
        log(f"[CLAUD] Summarize failed: {e}")

def handle_claud_sync():
    try:
        os.makedirs(os.path.dirname(CLAUD_SYNC_FILE), exist_ok=True)
        sync_time = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(CLAUD_SYNC_FILE, "w") as f:
            f.write(f"Last sync: {sync_time}\n")
        # Cloud sync stub
        if requests:
            try:
                resp = requests.post(CLAUD_SYNC_ENDPOINT, json={"timestamp": sync_time, "host": platform.node()})
                log(f"[CLAUD] Cloud sync response: {resp.status_code}")
            except Exception as e:
                log(f"[CLAUD] Cloud sync failed: {e}")
        else:
            log("[CLAUD] requests not installed, skipping real cloud sync.")
        log(f"[CLAUD] Synced with cloud at {sync_time}.")
    except Exception as e:
        log(f"[CLAUD] Sync failed: {e}")

def handle_claud_secure():
    # Simulate a security scan (could be extended with real checks)
    suspicious_files = []
    try:
        # Example: look for .pyc files in agent dir as 'suspicious'
        agent_dir = os.path.dirname(__file__)
        for fname in os.listdir(agent_dir):
            if fname.endswith(".pyc"):
                suspicious_files.append(fname)
        if suspicious_files:
            log(f"[CLAUD] Security scan: suspicious files found: {', '.join(suspicious_files)}")
        else:
            log("[CLAUD] Security scan: no suspicious files detected.")
    except Exception as e:
        log(f"[CLAUD] Security scan failed: {e}")

def handle_claud_upgrade():
    try:
        remote_version = REMOTE_VERSION
        if requests:
            try:
                resp = requests.get(CLAUD_UPGRADE_ENDPOINT)
                if resp.ok:
                    remote_version = resp.text.strip()
            except Exception as e:
                log(f"[CLAUD] Remote version check failed: {e}")
        if VERSION != remote_version:
            log(f"[CLAUD] Upgrade available! Local version: {VERSION}, Remote version: {remote_version}")
        else:
            log(f"[CLAUD] System is up to date. Version: {VERSION}")
    except Exception as e:
        log(f"[CLAUD] Upgrade check failed: {e}")

def handle_claud_help():
    log("[CLAUD] Advanced features:\n"
        "- claud analyze: Scan logs for errors/warnings and summarize.\n"
        "- claud summarize: Summarize last 10 log entries.\n"
        "- claud sync: Simulate cloud sync and record last sync time.\n"
        "- claud secure: Simulate security scan for suspicious files.\n"
        "- claud upgrade: Simulate version check against remote version.\n"
        "- claud help: List all advanced CLAUD features.")

def handle_help():
    log("[Baddy] Available commands: status, stealth scan, launch njax market, build drone, defend, launch njax engineering, phantom lockdown, system health, version, help, claud analyze, claud summarize, claud sync, claud secure, claud upgrade, claud help. For advanced features, use 'claud help'.")

def handle_unrecognized(task):
    log(f"[Baddy] Unrecognized command: {task}")

def phantom_protocol(lockdown=False):
    # Stub for Phantom defense protocol
    if lockdown:
        log("[Phantom] All systems locked down. Awaiting further instructions.")
    else:
        log("[Phantom] Defense protocol active. Monitoring for threats.")

def send_email(subject, body):
    email = config.get("notify_email")
    if not email:
        return
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = email
        msg["To"] = email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.get("smtp_server", "smtp.gmail.com"), config.get("smtp_port", 465), context=context) as server:
            server.login(email, config.get("smtp_password", ""))
            server.send_message(msg)
        log(f"[NOTIFY] Email sent: {subject}")
    except Exception as e:
        log(f"[NOTIFY] Email send failed: {e}")

def send_slack(message):
    webhook = config.get("notify_slack_webhook")
    if not webhook:
        return
    try:
        if requests:
            resp = requests.post(webhook, json={"text": message})
            log(f"[NOTIFY] Slack response: {resp.status_code}")
        else:
            log("[NOTIFY] requests not installed, cannot send Slack notification.")
    except Exception as e:
        log(f"[NOTIFY] Slack send failed: {e}")

def notify_critical(message):
    log(f"[NOTIFY] {message}")
    send_email("Baddy Agent Critical Alert", message)
    send_slack(message)

# Input validation for tasks
def validate_task(task):
    if not isinstance(task, str) or len(task) > 100:
        return False
    if any(c in task for c in [';', '|', '&', '$', '`']):
        return False
    return True

# Dynamic command registry
def register_command(name, handler):
    COMMANDS[name] = handler

COMMANDS = {}

# Register all commands (refactored)
register_command("status", handle_status)
register_command("stealth scan", handle_stealth_scan)
register_command("launch njax market", handle_launch_njax_market)
register_command("build drone", handle_build_drone)
register_command("defend", handle_defend)
register_command("launch njax engineering", handle_launch_njax_engineering)
register_command("phantom lockdown", handle_phantom_lockdown)
register_command("system health", handle_system_health)
register_command("version", handle_version)
register_command("help", handle_help)
# CLAUD
register_command("claud analyze", handle_claud_analyze)
register_command("claud summarize", handle_claud_summarize)
register_command("claud sync", handle_claud_sync)
register_command("claud secure", handle_claud_secure)
register_command("claud upgrade", handle_claud_upgrade)
register_command("claud help", handle_claud_help)

# Persistent task queue
TASK_QUEUE_FILE = config.get("task_queue_file", "src/ai_agent/task_queue.json")
def load_task_queue():
    if os.path.exists(TASK_QUEUE_FILE):
        with open(TASK_QUEUE_FILE, "r") as f:
            return json.load(f)
    return []
def save_task_queue(queue):
    with open(TASK_QUEUE_FILE, "w") as f:
        json.dump(queue, f)

def enqueue_task(task):
    queue = load_task_queue()
    queue.append(task)
    save_task_queue(queue)

def dequeue_task():
    queue = load_task_queue()
    if queue:
        task = queue.pop(0)
        save_task_queue(queue)
        return task
    return None

# Command usage tracking
def track_command_usage(command):
    usage_file = config.get("usage_file", "src/ai_agent/command_usage.json")
    usage = {}
    if os.path.exists(usage_file):
        with open(usage_file, "r") as f:
            usage = json.load(f)
    usage[command] = usage.get(command, 0) + 1
    with open(usage_file, "w") as f:
        json.dump(usage, f)

# Audit logging
def audit_log(event):
    audit_file = config.get("audit_file", "src/ai_agent/audit.log")
    with locked_file(audit_file, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {event}\n")

# Self-healing: auto-retry on repeated errors
ERROR_COUNT = {}
ERROR_THRESHOLD = int(config.get("error_threshold", 3))
def handle_task(task):
    task = task.strip().lower()
    if not validate_task(task):
        log(f"[Baddy] Invalid or unsafe task: {task}")
        notify_critical(f"Rejected unsafe task: {task}")
        audit_log(f"Rejected unsafe task: {task}")
        return
    handler = COMMANDS.get(task, None)
    track_command_usage(task)
    audit_log(f"Task received: {task}")
    if handler:
        try:
            handler()
            ERROR_COUNT[task] = 0
        except Exception as e:
            log(f"[Baddy] Error handling '{task}': {e}\n{traceback.format_exc()}")
            notify_critical(f"Critical error in task '{task}': {e}")
            audit_log(f"Error in task '{task}': {e}")
            ERROR_COUNT[task] = ERROR_COUNT.get(task, 0) + 1
            if ERROR_COUNT[task] >= ERROR_THRESHOLD:
                log(f"[Baddy] Self-healing: retrying task '{task}'")
                ERROR_COUNT[task] = 0
                try:
                    handler()
                    audit_log(f"Self-healed task: {task}")
                except Exception as e2:
                    log(f"[Baddy] Self-heal failed for '{task}': {e2}")
                    notify_critical(f"Self-heal failed for '{task}': {e2}")
                    audit_log(f"Self-heal failed for '{task}': {e2}")
    else:
        handle_unrecognized(task)
        audit_log(f"Unrecognized task: {task}")

# Periodic health check
def periodic_health_check():
    while True:
        try:
            handle_claud_analyze()
            handle_claud_secure()
            audit_log("Periodic health check completed.")
        except Exception as e:
            log(f"[Baddy] Health check error: {e}")
            notify_critical(f"Health check error: {e}")
        time.sleep(int(config.get("health_check_interval", 600)))

# Start health check thread
threading.Thread(target=periodic_health_check, daemon=True).start()

# Natural Language Command Parsing with OpenAI GPT
def handle_natural_language_command(text):
    log(f"[NLP] Received: {text}")
    audit_log(f"NLP command received: {text}")
    if not OPENAI_API_KEY:
        log("[NLP] OpenAI API key not set. Cannot process natural language command.")
        return
    prompt = (
        "You are an AI agent assistant. Map the following user request to a valid agent command. "
        "If the request is not actionable, reply 'unrecognized'.\n"
        f"User: {text}\nAgent Command:"
    )
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=32,
            temperature=0.0,
            stop=["\n"]
        )
        command = response.choices[0].text.strip().lower()
        log(f"[NLP] Parsed command: {command}")
        if command != "unrecognized":
            enqueue_task(command)
            audit_log(f"NLP parsed and enqueued: {command}")
        else:
            log("[NLP] Could not map input to a known command.")
    except Exception as e:
        log(f"[NLP] OpenAI error: {e}")
        notify_critical(f"NLP error: {e}")

# Self-Build: Use OpenAI to generate new command handler code
def handle_self_build(description):
    log(f"[SELF-BUILD] Generating handler for: {description}")
    audit_log(f"Self-build requested: {description}")
    if not OPENAI_API_KEY:
        log("[SELF-BUILD] OpenAI API key not set. Cannot self-build.")
        return
    prompt = (
        "Write a Python function that can be registered as a command handler for an AI agent. "
        "The function should log a message and perform the following action: "
        f"{description}\n"
        "Return only the function code."
    )
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.2,
            stop=["\n\n"]
        )
        code = response.choices[0].text.strip()
        log(f"[SELF-BUILD] Generated code:\n{code}")
        # Optionally, write to a file or dynamically exec/register
        with open("src/ai_agent/self_built_handlers.py", "a") as f:
            f.write(f"\n{code}\n")
        audit_log(f"Self-build code generated and saved.")
    except Exception as e:
        log(f"[SELF-BUILD] OpenAI error: {e}")
        notify_critical(f"Self-build error: {e}")

# Web Dashboard and Remote Control (FastAPI stub)
def start_web_dashboard():
    try:
        from fastapi import FastAPI, Request
        import uvicorn
        app = FastAPI()
        @app.get("/status")
        async def status():
            return {"status": "ok", "uptime": time.time()}
        @app.post("/command")
        async def command(request: Request):
            data = await request.json()
            cmd = data.get("command", "")
            token = data.get("token", "")
            # TODO: Authenticate token
            enqueue_task(cmd)
            return {"enqueued": cmd}
        @app.get("/logs")
        async def logs():
            with open(config.get("audit_file", "src/ai_agent/audit.log")) as f:
                return {"logs": f.read()}
        port = int(config.get("dashboard_port", 8080))
        threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port, log_level="info"), daemon=True).start()
        log(f"[DASHBOARD] Web dashboard started on port {port}")
    except Exception as e:
        log(f"[DASHBOARD] Failed to start web dashboard: {e}")

# Self-Upgrade from GitHub
def handle_self_upgrade():
    log("[SELF-UPGRADE] Checking for updates from GitHub...")
    audit_log("Self-upgrade initiated.")
    repo_url = config.get("github_repo", "")
    if not repo_url:
        log("[SELF-UPGRADE] No GitHub repo configured.")
        return
    try:
        # Pull latest code
        result = subprocess.run(["git", "pull"], cwd=os.path.dirname(__file__), capture_output=True, text=True)
        log(f"[SELF-UPGRADE] git pull output: {result.stdout}")
        if "Already up to date" not in result.stdout:
            log("[SELF-UPGRADE] Update applied. Restarting agent...")
            audit_log("Self-upgrade: restart triggered.")
            # Optionally restart agent
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            log("[SELF-UPGRADE] No update needed.")
    except Exception as e:
        log(f"[SELF-UPGRADE] Failed: {e}")
        notify_critical(f"Self-upgrade failed: {e}")

# Platform Integration Stubs
def send_teams(message):
    webhook = config.get("notify_teams_webhook")
    if webhook and requests:
        try:
            resp = requests.post(webhook, json={"text": message})
            log(f"[NOTIFY] Teams response: {resp.status_code}")
        except Exception as e:
            log(f"[NOTIFY] Teams send failed: {e}")

def send_aws_event(event):
    # TODO: Integrate with AWS SNS, SQS, or Lambda
    log(f"[AWS] Event: {event}")

def send_gcp_event(event):
    # TODO: Integrate with GCP Pub/Sub or Cloud Functions
    log(f"[GCP] Event: {event}")

# Load plugins and self-built handlers on startup
def load_plugins():
    """Load any plugin modules from the plugins directory."""
    plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if os.path.exists(plugin_dir):
        for plugin_file in os.listdir(plugin_dir):
            if plugin_file.endswith(".py") and not plugin_file.startswith("__"):
                try:
                    plugin_name = plugin_file[:-3]
                    spec = importlib.util.spec_from_file_location(
                        plugin_name,
                        os.path.join(plugin_dir, plugin_file)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    log(f"[PLUGINS] Loaded plugin: {plugin_name}")
                except Exception as e:
                    log(f"[PLUGINS] Failed to load plugin {plugin_file}: {e}")

def load_self_built_handlers():
    """Load any self-built command handlers."""
    handlers_file = os.path.join(os.path.dirname(__file__), "self_built_handlers.py")
    if os.path.exists(handlers_file):
        try:
            spec = importlib.util.spec_from_file_location(
                "self_built_handlers",
                handlers_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            log("[SELF-BUILD] Loaded self-built handlers")
        except Exception as e:
            log(f"[SELF-BUILD] Failed to load handlers: {e}")

# Start web dashboard if enabled
if config.get("enable_dashboard", True):
    start_web_dashboard()

def main():
    log("[Baddy] Online and watching for tasks...")
    while True:
        try:
            if os.path.exists(TASK_FILE):
                with locked_file(TASK_FILE, "r") as f:
                    tasks = f.readlines()
                if tasks:
                    for task in tasks[:20]:  # Limit to 20 tasks per cycle
                        handle_task(task)
                    # Clear task file after processing
                    with locked_file(TASK_FILE, "w") as f:
                        f.write("")
        except Exception as e:
            log(f"[Baddy] Main loop error: {e}\n{traceback.format_exc()}")
            notify_critical(f"Main loop error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()

# config.yaml documentation example:
# claud_sync_endpoint: "https://your-cloud-endpoint/api/sync"
# claud_upgrade_endpoint: "https://your-cloud-endpoint/api/version"
