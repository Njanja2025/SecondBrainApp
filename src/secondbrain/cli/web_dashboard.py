from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import json
from pathlib import Path
import time
from datetime import datetime, timedelta
import os
import psutil
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
import pyotp
import qrcode
from io import BytesIO
import base64
from functools import wraps
import re
import requests
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from jwt.exceptions import InvalidTokenError
import csv
import pdfkit
import pandas as pd
import numpy as np
from flask_mobility import Mobility
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading
import queue
import math

app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
Mobility(app)

# Initialize OAuth
oauth = OAuth(app)

# Google OAuth
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# GitHub OAuth
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

# Microsoft OAuth
oauth.register(
    name="microsoft",
    client_id=os.getenv("MICROSOFT_CLIENT_ID"),
    client_secret=os.getenv("MICROSOFT_CLIENT_SECRET"),
    authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    authorize_params=None,
    access_token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=os.getenv("MICROSOFT_REDIRECT_URI"),
    client_kwargs={"scope": "openid email profile"},
)

# Initialize rate limiter
limiter = Limiter(
    app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)

# Path to the metrics JSON file
METRICS_FILE = Path("/tmp/secondbrain_health.json")
USERS_FILE = Path("/tmp/secondbrain_users.json")

# Password policy
PASSWORD_POLICY = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
}

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", os.urandom(24).hex())
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour

# Telegram Bot Setup
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_TOKEN)
message_queue = queue.Queue()


def telegram_bot_worker():
    """Background worker for sending Telegram messages."""
    while True:
        try:
            message = message_queue.get()
            if message:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            time.sleep(1)
        except Exception as e:
            print(f"Telegram bot error: {e}")
            time.sleep(5)


# Start Telegram bot worker
telegram_thread = threading.Thread(target=telegram_bot_worker, daemon=True)
telegram_thread.start()


def send_telegram_alert(message):
    """Send alert to Telegram."""
    message_queue.put(message)


class User(UserMixin):
    def __init__(
        self,
        id,
        username,
        password_hash=None,
        email=None,
        role="user",
        two_factor_enabled=False,
        two_factor_secret=None,
        oauth_provider=None,
    ):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.role = role
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret
        self.oauth_provider = oauth_provider

    @staticmethod
    def get(user_id):
        if USERS_FILE.exists():
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
                if user_id in users:
                    user_data = users[user_id]
                    return User(
                        user_id,
                        user_data["username"],
                        user_data.get("password_hash"),
                        user_data.get("email"),
                        user_data.get("role", "user"),
                        user_data.get("two_factor_enabled", False),
                        user_data.get("two_factor_secret"),
                        user_data.get("oauth_provider"),
                    )
        return None

    @staticmethod
    def get_by_username(username):
        if USERS_FILE.exists():
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
                for user_id, user_data in users.items():
                    if user_data["username"] == username:
                        return User(
                            user_id,
                            username,
                            user_data.get("password_hash"),
                            user_data.get("email"),
                            user_data.get("role", "user"),
                            user_data.get("two_factor_enabled", False),
                            user_data.get("two_factor_secret"),
                            user_data.get("oauth_provider"),
                        )
        return None

    @staticmethod
    def get_by_email(email):
        if USERS_FILE.exists():
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
                for user_id, user_data in users.items():
                    if user_data.get("email") == email:
                        return User(
                            user_id,
                            user_data["username"],
                            user_data.get("password_hash"),
                            email,
                            user_data.get("role", "user"),
                            user_data.get("two_factor_enabled", False),
                            user_data.get("two_factor_secret"),
                            user_data.get("oauth_provider"),
                        )
        return None


def generate_jwt_token(user):
    """Generate a JWT token for the user."""
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token):
    """Verify a JWT token and return the user."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return User.get(payload["user_id"])
    except InvalidTokenError:
        return None


@app.route("/login/google")
def google_login():
    """Handle Google OAuth login."""
    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/login/google/callback")
def google_callback():
    """Handle Google OAuth callback."""
    token = oauth.google.authorize_access_token()
    userinfo = oauth.google.parse_id_token(token)

    email = userinfo["email"]
    user = User.get_by_email(email)

    if not user:
        # Create new user from Google account
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            user_id = str(len(users) + 1)
            users[user_id] = {
                "username": email.split("@")[0],
                "email": email,
                "role": "user",
                "oauth_provider": "google",
                "two_factor_enabled": False,
            }
            save_users(users)
            user = User.get(user_id)

    login_user(user)
    return redirect(url_for("dashboard"))


@app.route("/login/github")
def github_login():
    """Handle GitHub OAuth login."""
    redirect_uri = url_for("github_callback", _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@app.route("/login/github/callback")
def github_callback():
    """Handle GitHub OAuth callback."""
    token = oauth.github.authorize_access_token()
    resp = oauth.github.get("user")
    profile = resp.json()

    email = profile.get("email")
    user = User.get_by_email(email)

    if not user:
        # Create new user from GitHub account
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            user_id = str(len(users) + 1)
            users[user_id] = {
                "username": profile["login"],
                "email": email,
                "role": "user",
                "oauth_provider": "github",
                "two_factor_enabled": False,
            }
            save_users(users)
            user = User.get(user_id)

    login_user(user)
    return redirect(url_for("dashboard"))


@app.route("/login/microsoft")
def microsoft_login():
    """Handle Microsoft OAuth login."""
    redirect_uri = url_for("microsoft_callback", _external=True)
    return oauth.microsoft.authorize_redirect(redirect_uri)


@app.route("/login/microsoft/callback")
def microsoft_callback():
    """Handle Microsoft OAuth callback."""
    token = oauth.microsoft.authorize_access_token()
    userinfo = oauth.microsoft.parse_id_token(token)

    email = userinfo["email"]
    user = User.get_by_email(email)

    if not user:
        # Create new user from Microsoft account
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            user_id = str(len(users) + 1)
            users[user_id] = {
                "username": email.split("@")[0],
                "email": email,
                "role": "user",
                "oauth_provider": "microsoft",
                "two_factor_enabled": False,
            }
            save_users(users)
            user = User.get(user_id)

    login_user(user)
    return redirect(url_for("dashboard"))


@app.route("/api/token", methods=["POST"])
@limiter.limit("5 per minute")
def get_token():
    """Get a JWT token for API access."""
    username = request.json.get("username")
    password = request.json.get("password")

    user = User.get_by_username(username)
    if (
        user
        and user.password_hash
        and check_password_hash(user.password_hash, password)
    ):
        token = generate_jwt_token(user)
        return jsonify({"token": token})

    return jsonify({"error": "Invalid credentials"}), 401


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        if token.startswith("Bearer "):
            token = token[7:]

        user = verify_jwt_token(token)
        if not user:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


@app.route("/api/metrics")
@token_required
def api_metrics():
    """API endpoint to get metrics with JWT authentication."""
    metrics_data = get_metrics()
    if metrics_data:
        return jsonify(metrics_data)
    return jsonify({"error": "No metrics available"}), 404


def validate_password(password):
    """Validate password against policy."""
    if len(password) < PASSWORD_POLICY["min_length"]:
        return (
            False,
            f"Password must be at least {PASSWORD_POLICY['min_length']} characters long",
        )

    if PASSWORD_POLICY["require_uppercase"] and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if PASSWORD_POLICY["require_lowercase"] and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if PASSWORD_POLICY["require_digit"] and not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if PASSWORD_POLICY["require_special"] and not re.search(
        r'[!@#$%^&*(),.?":{}|<>]', password
    ):
        return False, "Password must contain at least one special character"

    return True, "Password is valid"


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Access denied")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def generate_reset_token():
    """Generate a secure reset token."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(32))


def save_users(users):
    """Save users to the JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def get_metrics():
    """Read and return the latest metrics from the JSON file."""
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, "r") as f:
                metrics = json.load(f)

                # Enhanced CPU metrics
                cpu_freq = psutil.cpu_freq()
                metrics["cpu"]["frequency"] = cpu_freq.current if cpu_freq else 0
                metrics["cpu"]["min_frequency"] = cpu_freq.min if cpu_freq else 0
                metrics["cpu"]["max_frequency"] = cpu_freq.max if cpu_freq else 0
                metrics["cpu"]["load_avg"] = psutil.getloadavg()
                metrics["cpu"]["ctx_switches"] = psutil.cpu_stats().ctx_switches
                metrics["cpu"]["interrupts"] = psutil.cpu_stats().interrupts

                # Enhanced memory metrics
                swap = psutil.swap_memory()
                metrics["memory"]["swap_used"] = swap.used
                metrics["memory"]["swap_total"] = swap.total
                metrics["memory"]["swap_percent"] = swap.percent
                metrics["memory"]["swap_sin"] = swap.sin
                metrics["memory"]["swap_sout"] = swap.sout

                # Enhanced disk metrics
                disk_io = psutil.disk_io_counters()
                metrics["disk"]["read_count"] = disk_io.read_count
                metrics["disk"]["write_count"] = disk_io.write_count
                metrics["disk"]["read_bytes"] = disk_io.read_bytes
                metrics["disk"]["write_bytes"] = disk_io.write_bytes
                metrics["disk"]["read_time"] = disk_io.read_time
                metrics["disk"]["write_time"] = disk_io.write_time

                # Enhanced network metrics
                net_io = psutil.net_io_counters()
                metrics["network"]["packets_sent"] = net_io.packets_sent
                metrics["network"]["packets_recv"] = net_io.packets_recv
                metrics["network"]["bytes_sent"] = net_io.bytes_sent
                metrics["network"]["bytes_recv"] = net_io.bytes_recv
                metrics["network"]["errin"] = net_io.errin
                metrics["network"]["errout"] = net_io.errout
                metrics["network"]["dropin"] = net_io.dropin
                metrics["network"]["dropout"] = net_io.dropout

                # Enhanced process metrics
                process = psutil.Process()
                metrics["processes"]["threads"] = process.num_threads()
                metrics["processes"]["handles"] = (
                    process.num_handles() if hasattr(process, "num_handles") else 0
                )
                metrics["processes"]["cpu_percent"] = process.cpu_percent()
                metrics["processes"]["memory_percent"] = process.memory_percent()
                metrics["processes"]["create_time"] = process.create_time()
                metrics["processes"]["status"] = process.status()

                # Enhanced system metrics
                metrics["system"]["boot_time"] = psutil.boot_time()
                metrics["system"]["users"] = len(psutil.users())
                metrics["system"]["platform"] = os.name
                metrics["system"]["python_version"] = os.sys.version
                metrics["system"]["cpu_count"] = psutil.cpu_count()
                metrics["system"]["cpu_count_logical"] = psutil.cpu_count(logical=True)

                # Add battery info if available
                try:
                    battery = psutil.sensors_battery()
                    if battery:
                        metrics["system"]["battery"] = {
                            "percent": battery.percent,
                            "power_plugged": battery.power_plugged,
                            "time_left": (
                                battery.secsleft if battery.secsleft != -2 else None
                            ),
                        }
                except:
                    pass

                return metrics
    except Exception as e:
        print(f"Error reading metrics: {e}")
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.get_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            if user.two_factor_enabled:
                session["user_id"] = user.id
                return redirect(url_for("verify_2fa"))

            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.get(session["user_id"])
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        token = request.form.get("token")
        totp = pyotp.TOTP(user.two_factor_secret)

        if totp.verify(token):
            login_user(user)
            session.pop("user_id", None)
            return redirect(url_for("dashboard"))

        flash("Invalid 2FA token")
    return render_template("verify_2fa.html")


@app.route("/setup-2fa", methods=["GET", "POST"])
@login_required
def setup_2fa():
    if request.method == "POST":
        token = request.form.get("token")
        totp = pyotp.TOTP(current_user.two_factor_secret)

        if totp.verify(token):
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
                users[current_user.id]["two_factor_enabled"] = True
                save_users(users)

            flash("2FA has been enabled")
            return redirect(url_for("dashboard"))

        flash("Invalid token")

    # Generate new 2FA secret
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        current_user.email or current_user.username, issuer_name="SecondBrain"
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR code to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()

    # Save secret temporarily
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
        users[current_user.id]["two_factor_secret"] = secret
        save_users(users)

    return render_template("setup_2fa.html", qr_code=qr_code)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not check_password_hash(current_user.password_hash, current_password):
            flash("Current password is incorrect")
            return redirect(url_for("profile"))

        if new_password != confirm_password:
            flash("New passwords do not match")
            return redirect(url_for("profile"))

        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message)
            return redirect(url_for("profile"))

        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            users[current_user.id]["password_hash"] = generate_password_hash(
                new_password
            )
            save_users(users)

        flash("Password updated successfully")
        return redirect(url_for("profile"))

    return render_template("profile.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")

        user = User.get_by_username(username)
        if user and user.email == email:
            # Generate new password
            new_password = "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
            )

            # Update user's password
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
                users[user.id]["password_hash"] = generate_password_hash(new_password)
                save_users(users)

            flash(f"Your new password is: {new_password}")
            return redirect(url_for("login"))

        flash("Invalid username or email")
    return render_template("reset_password.html")


@app.route("/users")
@login_required
def users():
    if current_user.role != "admin":
        flash("Access denied")
        return redirect(url_for("dashboard"))

    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    return render_template("users.html", users=users)


@app.route("/users/add", methods=["GET", "POST"])
@login_required
def add_user():
    if current_user.role != "admin":
        flash("Access denied")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        role = request.form.get("role", "user")

        with open(USERS_FILE, "r") as f:
            users = json.load(f)

        # Check if username already exists
        if any(u["username"] == username for u in users.values()):
            flash("Username already exists")
            return redirect(url_for("add_user"))

        # Add new user
        user_id = str(len(users) + 1)
        users[user_id] = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "email": email,
            "role": role,
        }
        save_users(users)

        flash("User added successfully")
        return redirect(url_for("users"))

    return render_template("add_user.html")


@app.route("/users/<user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        flash("Access denied")
        return redirect(url_for("dashboard"))

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if user_id in users:
        del users[user_id]
        save_users(users)
        flash("User deleted successfully")
    else:
        flash("User not found")

    return redirect(url_for("users"))


@app.route("/")
@login_required
def dashboard():
    """Serve the dashboard HTML page."""
    return render_template("dashboard.html")


@app.route("/api/metrics/history")
@login_required
def metrics_history():
    """Get historical metrics data for charts."""
    now = datetime.now()
    timestamps = [(now - timedelta(minutes=i)).isoformat() for i in range(60)]

    # Generate more realistic metrics with periodic patterns
    cpu_data = []
    memory_data = []
    disk_data = []
    network_sent = []
    network_recv = []
    process_data = []
    temperature_data = []

    base_cpu = 30
    base_memory = 40
    base_disk = 50
    base_network = 1000
    base_processes = 100
    base_temp = 45

    for i in range(60):
        # Add periodic patterns and random variations
        time_factor = math.sin(i / 10) * 10
        random_factor = np.random.normal(0, 5)

        # CPU with periodic spikes
        cpu_value = base_cpu + time_factor + random_factor
        if i % 15 == 0:  # Add periodic spikes
            cpu_value += 20
        cpu_data.append(max(0, min(100, cpu_value)))

        # Memory with gradual changes
        memory_value = base_memory + time_factor * 0.8 + random_factor
        memory_data.append(max(0, min(100, memory_value)))

        # Disk with slow growth
        disk_value = base_disk + (i * 0.1) + random_factor
        disk_data.append(max(0, min(100, disk_value)))

        # Network with burst patterns
        network_value = base_network + time_factor * 100 + random_factor * 50
        if i % 20 == 0:  # Add network bursts
            network_value *= 2
        network_sent.append(max(0, network_value))
        network_recv.append(max(0, network_value * 1.5))

        # Process count with variations
        process_value = base_processes + time_factor * 5 + random_factor * 2
        process_data.append(max(0, process_value))

        # Temperature with daily cycle
        temp_value = base_temp + math.sin(i / 30) * 5 + random_factor * 0.5
        temperature_data.append(max(0, temp_value))

    data = {
        "timestamps": timestamps,
        "cpu": cpu_data,
        "memory": memory_data,
        "disk": disk_data,
        "network": {"bytes_sent": network_sent, "bytes_recv": network_recv},
        "processes": process_data,
        "temperature": temperature_data,
    }

    return jsonify(data)


@app.route("/export/csv")
@login_required
def export_csv():
    """Export metrics data as CSV."""
    metrics = get_metrics()
    if not metrics:
        flash("No metrics available for export")
        return redirect(url_for("dashboard"))

    # Create CSV data
    output = BytesIO()
    writer = csv.writer(output)

    # Write headers
    writer.writerow(["Category", "Metric", "Value", "Unit", "Timestamp"])

    # Write data
    timestamp = datetime.now().isoformat()

    # CPU metrics
    for key, value in metrics["cpu"].items():
        unit = "%" if key == "percent" else "MHz" if "frequency" in key else "count"
        writer.writerow(["CPU", key, value, unit, timestamp])

    # Memory metrics
    for key, value in metrics["memory"].items():
        unit = "%" if key == "percent" else "bytes"
        writer.writerow(["Memory", key, value, unit, timestamp])

    # Disk metrics
    for key, value in metrics["disk"].items():
        unit = "%" if key == "percent" else "bytes"
        writer.writerow(["Disk", key, value, unit, timestamp])

    # Network metrics
    for key, value in metrics["network"].items():
        unit = "bytes"
        writer.writerow(["Network", key, value, unit, timestamp])

    # Process metrics
    for key, value in metrics["processes"].items():
        unit = "%" if "percent" in key else "count"
        writer.writerow(["Processes", key, value, unit, timestamp])

    # System metrics
    for key, value in metrics["system"].items():
        unit = "timestamp" if "time" in key else "count" if "count" in key else "text"
        writer.writerow(["System", key, value, unit, timestamp])

    output.seek(0)
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f'metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
    )


@app.route("/export/pdf")
@login_required
def export_pdf():
    """Export metrics data as PDF report."""
    metrics = get_metrics()
    if not metrics:
        flash("No metrics available for export")
        return redirect(url_for("dashboard"))

    # Generate HTML report
    html = render_template("report.html", metrics=metrics)

    # Convert to PDF with custom options
    options = {
        "page-size": "A4",
        "margin-top": "20mm",
        "margin-right": "20mm",
        "margin-bottom": "20mm",
        "margin-left": "20mm",
        "encoding": "UTF-8",
        "no-outline": None,
        "enable-local-file-access": None,
    }

    pdf = pdfkit.from_string(html, False, options=options)

    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f'metrics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
    )


@app.route("/export/json")
@login_required
def export_json():
    """Export metrics data as JSON."""
    metrics = get_metrics()
    if not metrics:
        flash("No metrics available for export")
        return redirect(url_for("dashboard"))

    # Add metadata
    export_data = {
        "metadata": {
            "export_time": datetime.now().isoformat(),
            "version": "1.0",
            "format": "json",
        },
        "metrics": metrics,
    }

    return send_file(
        BytesIO(json.dumps(export_data, indent=2).encode()),
        mimetype="application/json",
        as_attachment=True,
        download_name=f'metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
    )


@app.route("/export/excel")
@login_required
def export_excel():
    """Export metrics data as Excel file."""
    metrics = get_metrics()
    if not metrics:
        flash("No metrics available for export")
        return redirect(url_for("dashboard"))

    # Create DataFrame
    data = []
    timestamp = datetime.now().isoformat()

    # CPU metrics
    for key, value in metrics["cpu"].items():
        data.append(
            {
                "Category": "CPU",
                "Metric": key,
                "Value": value,
                "Unit": (
                    "%"
                    if key == "percent"
                    else "MHz" if "frequency" in key else "count"
                ),
                "Timestamp": timestamp,
            }
        )

    # Memory metrics
    for key, value in metrics["memory"].items():
        data.append(
            {
                "Category": "Memory",
                "Metric": key,
                "Value": value,
                "Unit": "%" if key == "percent" else "bytes",
                "Timestamp": timestamp,
            }
        )

    # Disk metrics
    for key, value in metrics["disk"].items():
        data.append(
            {
                "Category": "Disk",
                "Metric": key,
                "Value": value,
                "Unit": "%" if key == "percent" else "bytes",
                "Timestamp": timestamp,
            }
        )

    # Network metrics
    for key, value in metrics["network"].items():
        data.append(
            {
                "Category": "Network",
                "Metric": key,
                "Value": value,
                "Unit": "bytes",
                "Timestamp": timestamp,
            }
        )

    # Process metrics
    for key, value in metrics["processes"].items():
        data.append(
            {
                "Category": "Processes",
                "Metric": key,
                "Value": value,
                "Unit": "%" if "percent" in key else "count",
                "Timestamp": timestamp,
            }
        )

    # System metrics
    for key, value in metrics["system"].items():
        data.append(
            {
                "Category": "System",
                "Metric": key,
                "Value": value,
                "Unit": (
                    "timestamp"
                    if "time" in key
                    else "count" if "count" in key else "text"
                ),
                "Timestamp": timestamp,
            }
        )

    df = pd.DataFrame(data)

    # Create Excel writer
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Metrics", index=False)

        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets["Metrics"]

        # Add formats
        header_format = workbook.add_format(
            {
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#D7E4BC",
                "border": 1,
            }
        )

        # Write headers with format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Adjust column widths
        worksheet.set_column("A:A", 15)  # Category
        worksheet.set_column("B:B", 20)  # Metric
        worksheet.set_column("C:C", 15)  # Value
        worksheet.set_column("D:D", 10)  # Unit
        worksheet.set_column("E:E", 30)  # Timestamp

    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f'metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
    )


@app.route("/api/alerts", methods=["POST"])
@login_required
def set_alert():
    """Set up metric alerts."""
    data = request.json
    metric = data.get("metric")
    threshold = data.get("threshold")
    condition = data.get("condition")

    if not all([metric, threshold, condition]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Store alert configuration
    alerts = get_alerts()
    alerts.append(
        {
            "metric": metric,
            "threshold": threshold,
            "condition": condition,
            "user_id": current_user.id,
            "created_at": datetime.now().isoformat(),
        }
    )
    save_alerts(alerts)

    return jsonify({"message": "Alert configured successfully"})


@app.route("/api/alerts", methods=["GET"])
@login_required
def get_alerts():
    """Get configured alerts."""
    alerts_file = Path("/tmp/secondbrain_alerts.json")
    if alerts_file.exists():
        with open(alerts_file, "r") as f:
            return jsonify(json.load(f))
    return jsonify([])


def check_alerts(metrics):
    """Check metrics against configured alerts."""
    alerts = get_alerts()
    for alert in alerts:
        if alert["user_id"] != current_user.id:
            continue

        metric_value = metrics.get(alert["metric"])
        if metric_value is None:
            continue

        triggered = False
        if alert["condition"] == "above" and metric_value > alert["threshold"]:
            triggered = True
        elif alert["condition"] == "below" and metric_value < alert["threshold"]:
            triggered = True

        if triggered:
            message = f"Alert: {alert['metric']} is {alert['condition']} {alert['threshold']} (current: {metric_value})"
            send_telegram_alert(message)


def run_server(host="127.0.0.1", port=5000):
    """Run the Flask server."""
    # Create default admin user if no users exist
    if not USERS_FILE.exists():
        users = {
            "1": {
                "username": "admin",
                "password_hash": generate_password_hash("admin"),
                "email": "admin@localhost",
                "role": "admin",
                "two_factor_enabled": False,
                "two_factor_secret": None,
                "oauth_provider": None,
            }
        }
        save_users(users)

    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
