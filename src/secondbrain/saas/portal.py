"""
SaaS portal for SecondBrainApp
"""
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import logging
from typing import Optional
from datetime import datetime
import os

from ..utils.config import Config
from ..payments.payment_gateway import PaymentGateway

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///saas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
mail = Mail(app)

# Configure logging
logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    """User model for authentication and subscription management."""
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    subscription_id = db.Column(db.String(120))
    subscription_status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))

class Portal:
    """Manages the SaaS portal functionality."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize portal.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or Config()
        self.payment_gateway = PaymentGateway(config)
        self._setup_mail()
        
    def _setup_mail(self):
        """Configure email settings."""
        app.config['MAIL_SERVER'] = self.config.get('mail_server', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = self.config.get('mail_port', 587)
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USERNAME'] = self.config.get('mail_username')
        app.config['MAIL_PASSWORD'] = self.config.get('mail_password')
        
    def send_verification_email(self, user: User):
        """
        Send verification email to user.
        
        Args:
            user: User instance
        """
        try:
            msg = Message(
                'Verify your SecondBrainApp account',
                sender=self.config.get('mail_username'),
                recipients=[user.email]
            )
            msg.body = f"""
            Welcome to SecondBrainApp!
            
            Please verify your email by clicking the link below:
            {url_for('verify_email', token=user.id, _external=True)}
            """
            mail.send(msg)
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            
    def create_subscription(self, user: User, plan_id: str, payment_method: str) -> bool:
        """
        Create subscription for user.
        
        Args:
            user: User instance
            plan_id: Plan ID
            payment_method: Payment method
            
        Returns:
            True if successful
        """
        try:
            # Create customer in payment gateway
            if payment_method == 'stripe':
                customer_id = self.payment_gateway.create_stripe_customer(user.email, user.name)
            else:
                customer_id = self.payment_gateway.create_paypal_customer(user.email, user.name)
                
            if not customer_id:
                return False
                
            # Create subscription
            subscription_id = self.payment_gateway.create_subscription(
                customer_id,
                plan_id,
                payment_method
            )
            
            if subscription_id:
                user.subscription_id = subscription_id
                user.subscription_status = 'active'
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return False
            
    def check_subscription(self, user: User) -> str:
        """
        Check subscription status.
        
        Args:
            user: User instance
            
        Returns:
            Subscription status
        """
        try:
            if user.subscription_id:
                status = self.payment_gateway.get_subscription_status(
                    user.subscription_id,
                    'stripe' if 'cus_' in user.subscription_id else 'paypal'
                )
                user.subscription_status = status
                db.session.commit()
                return status
            return 'none'
        except Exception as e:
            logger.error(f"Failed to check subscription: {e}")
            return 'error'
            
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        Run the portal server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        app.run(host=host, port=port, debug=debug) 