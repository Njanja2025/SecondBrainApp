"""
Route handlers for SecondBrainApp SaaS portal
"""

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging

from .portal import app, db, User, Portal

logger = logging.getLogger(__name__)

# Initialize portal
portal = Portal()


@app.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@app.route("/pricing")
def pricing():
    """Pricing plans page."""
    return render_template("pricing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """User signup."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")

        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for("signup"))

        user = User(email=email, password=generate_password_hash(password), name=name)
        db.session.add(user)
        db.session.commit()

        portal.send_verification_email(user)
        flash("Please check your email to verify your account")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    """User dashboard."""
    subscription_status = portal.check_subscription(current_user)
    return render_template("dashboard.html", status=subscription_status)


@app.route("/subscribe/<plan_id>", methods=["POST"])
@login_required
def subscribe(plan_id):
    """Subscribe to a plan."""
    payment_method = request.form.get("payment_method")

    if portal.create_subscription(current_user, plan_id, payment_method):
        flash("Subscription created successfully")
    else:
        flash("Failed to create subscription")

    return redirect(url_for("dashboard"))


@app.route("/verify/<token>")
def verify_email(token):
    """Verify user email."""
    user = User.query.get(token)
    if user:
        # TODO: Add email verification logic
        flash("Email verified successfully")
        return redirect(url_for("login"))
    flash("Invalid verification token")
    return redirect(url_for("index"))
