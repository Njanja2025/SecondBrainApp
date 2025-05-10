"""
Payment dashboard for visualizing subscription plans and payment statistics.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import stripe
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import threading
import time
import os

from src.secondbrain.monetization.subscription_manager import start_payment_flow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/payments.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PaymentDashboard:
    """GUI dashboard for payment management."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the dashboard."""
        self.root = root
        self.root.title("SecondBrain Payment Dashboard")
        self.root.geometry("1000x800")
        
        # Load configuration
        self.config = self._load_config()
        stripe.api_key = self.config["stripe_keys"]["secret"]
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create widgets
        self._create_widgets()
        
        # Load initial data
        self._load_data()
        
        # Set up auto-refresh
        self._schedule_refresh()
        
        # Set up log monitoring
        self._start_log_monitor()
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        config_path = Path("config/payment_config.json")
        with open(config_path) as f:
            return json.load(f)
    
    def _create_widgets(self):
        """Create dashboard widgets."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.plans_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.plans_tab, text="Subscription Plans")
        self.notebook.add(self.stats_tab, text="Payment Statistics")
        self.notebook.add(self.logs_tab, text="Payment Logs")
        
        # Subscription plans section
        plans_frame = ttk.LabelFrame(self.plans_tab, text="Available Plans", padding="5")
        plans_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create plan buttons
        self.plan_buttons = {}
        plans = {
            "basic": {
                "name": "Basic Plan",
                "description": "Basic features for individual users",
                "price": "$9.99/month"
            },
            "premium": {
                "name": "Premium Plan",
                "description": "Advanced features for power users",
                "price": "$19.99/month"
            },
            "enterprise": {
                "name": "Enterprise Plan",
                "description": "Custom solutions for organizations",
                "price": "Custom pricing"
            }
        }
        
        for i, (plan_id, plan) in enumerate(plans.items()):
            btn = ttk.Button(
                plans_frame,
                text=f"{plan['name']}\n{plan['description']}\n{plan['price']}",
                command=lambda p=plan_id: self._select_plan(p)
            )
            btn.pack(fill=tk.X, padx=5, pady=5)
            self.plan_buttons[plan_id] = btn
        
        # Payment statistics section
        stats_frame = ttk.LabelFrame(self.stats_tab, text="Payment Statistics", padding="5")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create statistics labels
        self.stats_labels = {}
        stats = ["Total Revenue", "Active Subscriptions", "Average Revenue per User"]
        for i, stat in enumerate(stats):
            ttk.Label(stats_frame, text=stat).grid(row=i, column=0, sticky=tk.W, padx=5)
            self.stats_labels[stat] = ttk.Label(stats_frame, text="0")
            self.stats_labels[stat].grid(row=i, column=1, sticky=tk.E, padx=5)
        
        # Recent transactions section
        trans_frame = ttk.LabelFrame(self.stats_tab, text="Recent Transactions", padding="5")
        trans_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create transactions treeview
        columns = ("Date", "Customer", "Amount", "Status", "Plan")
        self.trans_tree = ttk.Treeview(trans_frame, columns=columns, show="headings")
        for col in columns:
            self.trans_tree.heading(col, text=col)
            self.trans_tree.column(col, width=100)
        self.trans_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(trans_frame, orient=tk.VERTICAL, command=self.trans_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.trans_tree.configure(yscrollcommand=scrollbar.set)
        
        # Payment logs section
        logs_frame = ttk.LabelFrame(self.logs_tab, text="Payment Logs", padding="5")
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create log text area
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, width=80, height=30)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add refresh button
        refresh_btn = ttk.Button(logs_frame, text="Refresh Logs", command=self._refresh_logs)
        refresh_btn.pack(pady=5)
    
    def _load_data(self):
        """Load dashboard data."""
        try:
            # Update statistics
            self._update_statistics()
            
            # Update transactions
            self._update_transactions()
            
            # Load logs
            self._refresh_logs()
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
            messagebox.showerror("Error", f"Failed to load dashboard data: {str(e)}")
    
    def _update_statistics(self):
        """Update payment statistics."""
        try:
            # Get total revenue
            total_revenue = 0
            active_subscriptions = 0
            
            # Get all subscriptions
            subscriptions = stripe.Subscription.list(limit=100)
            for sub in subscriptions.data:
                if sub.status == "active":
                    active_subscriptions += 1
                    total_revenue += sub.items.data[0].price.unit_amount / 100  # Convert from cents
            
            # Calculate average revenue
            avg_revenue = total_revenue / active_subscriptions if active_subscriptions > 0 else 0
            
            # Update labels
            self.stats_labels["Total Revenue"].config(text=f"${total_revenue:.2f}")
            self.stats_labels["Active Subscriptions"].config(text=str(active_subscriptions))
            self.stats_labels["Average Revenue per User"].config(text=f"${avg_revenue:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            raise
    
    def _update_transactions(self):
        """Update recent transactions."""
        try:
            # Clear existing items
            for item in self.trans_tree.get_children():
                self.trans_tree.delete(item)
            
            # Get recent charges
            charges = stripe.Charge.list(limit=10)
            for charge in charges.data:
                # Get customer email
                customer = stripe.Customer.retrieve(charge.customer)
                email = customer.email
                
                # Get subscription details if available
                subscription = None
                if charge.invoice:
                    invoice = stripe.Invoice.retrieve(charge.invoice)
                    if invoice.subscription:
                        subscription = stripe.Subscription.retrieve(invoice.subscription)
                
                # Add to treeview
                self.trans_tree.insert("", tk.END, values=(
                    datetime.fromtimestamp(charge.created).strftime("%Y-%m-%d"),
                    email,
                    f"${charge.amount/100:.2f}",
                    charge.status,
                    subscription.items.data[0].price.nickname if subscription else "N/A"
                ))
                
        except Exception as e:
            logger.error(f"Error updating transactions: {e}")
            raise
    
    def _refresh_logs(self):
        """Refresh payment logs."""
        try:
            self.log_text.delete(1.0, tk.END)
            with open("logs/stripe_payments.log", "r") as log_file:
                content = log_file.read()
                self.log_text.insert(tk.END, content)
        except FileNotFoundError:
            self.log_text.insert(tk.END, "No payment logs found.")
        except Exception as e:
            logger.error(f"Error refreshing logs: {e}")
            self.log_text.insert(tk.END, f"Error loading logs: {str(e)}")
    
    def _start_log_monitor(self):
        """Start monitoring log file for changes."""
        def monitor_logs():
            last_size = 0
            while True:
                try:
                    current_size = os.path.getsize("logs/stripe_payments.log")
                    if current_size != last_size:
                        self._refresh_logs()
                        last_size = current_size
                except Exception as e:
                    logger.error(f"Error monitoring logs: {e}")
                time.sleep(1)
        
        thread = threading.Thread(target=monitor_logs, daemon=True)
        thread.start()
    
    def _schedule_refresh(self):
        """Schedule periodic refresh of dashboard data."""
        self._load_data()
        self.root.after(300000, self._schedule_refresh)  # Refresh every 5 minutes
    
    def _select_plan(self, plan_id: str):
        """Handle plan selection."""
        try:
            # Get customer email
            email = self._get_customer_email()
            if not email:
                return
            
            # Start payment flow
            start_payment_flow(plan_id, email)
            
        except Exception as e:
            logger.error(f"Error selecting plan: {e}")
            messagebox.showerror("Error", f"Failed to start payment: {str(e)}")
    
    def _get_customer_email(self) -> Optional[str]:
        """Get customer email through dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Enter Email")
        dialog.geometry("300x100")
        
        email_var = tk.StringVar()
        result = [None]  # Use list to store result
        
        def on_submit():
            email = email_var.get().strip()
            if email:
                result[0] = email
                dialog.destroy()
        
        ttk.Label(dialog, text="Enter your email:").pack(pady=5)
        ttk.Entry(dialog, textvariable=email_var).pack(pady=5)
        ttk.Button(dialog, text="Submit", command=on_submit).pack(pady=5)
        
        # Wait for dialog to close
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        
        return result[0]

def run_dashboard():
    """Run the payment dashboard."""
    root = tk.Tk()
    app = PaymentDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    run_dashboard() 