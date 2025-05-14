"""
Njax Market Integration Module
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class NjaxMarket:
    """Integration with the Njax Market system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize market integration."""
        self.config = config
        self.market_data_file = Path("data/market_data.json")
        self.transaction_log = Path("logs/market_transactions.json")
        self.cart = {}
        self.categories = {}
        self.items = {}
        self.user_balance = 1000.0  # Starting balance
        self.purchase_history = []
        self.favorites = set()
        self._initialize_market()
        
    def _initialize_market(self):
        """Initialize market data and directories."""
        try:
            self.market_data_file.parent.mkdir(parents=True, exist_ok=True)
            self.transaction_log.parent.mkdir(parents=True, exist_ok=True)
            
            if not self.market_data_file.exists():
                self._create_default_market_data()
            
            self._load_categories()
            self._load_items()
            self._load_transaction_log()
            logger.info("Market initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing market: {e}")
            raise
    
    def _create_default_market_data(self):
        """Create default market data structure."""
        default_data = {
            "categories": {
                "tools": {
                    "name": "Tools",
                    "description": "Development and productivity tools"
                },
                "services": {
                    "name": "Services",
                    "description": "Professional services and consulting"
                },
                "resources": {
                    "name": "Resources",
                    "description": "Learning resources and materials"
                }
            },
            "items": {
                "code_editor": {
                    "name": "Code Editor",
                    "category": "tools",
                    "price": 99.99,
                    "description": "Advanced code editor with AI features",
                    "stock": 100
                },
                "debugger": {
                    "name": "Debugger",
                    "category": "tools",
                    "price": 49.99,
                    "description": "Intelligent debugging tool",
                    "stock": 50
                }
            }
        }
        self._save_market_data(default_data)
    
    def _load_categories(self):
        """Load market categories from file."""
        try:
            with open(self.market_data_file, "r") as f:
                data = json.load(f)
                self.categories = data.get("categories", {})
            logger.info(f"Loaded {len(self.categories)} categories")
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            self.categories = {}
    
    def _load_items(self):
        """Load market items from file."""
        try:
            with open(self.market_data_file, "r") as f:
                data = json.load(f)
                self.items = data.get("items", {})
            logger.info(f"Loaded {len(self.items)} items")
        except Exception as e:
            logger.error(f"Error loading items: {e}")
            self.items = {}
    
    def _save_market_data(self, data: Dict[str, Any]):
        """Save market data to file with atomic write."""
        try:
            temp_file = self.market_data_file.with_suffix('.json.tmp')
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.market_data_file)
            logger.info("Market data saved successfully")
        except Exception as e:
            logger.error(f"Error saving market data: {e}")
            raise
    
    def _load_transaction_log(self):
        """Load transaction history."""
        try:
            if self.transaction_log.exists():
                with open(self.transaction_log, "r") as f:
                    self.purchase_history = json.load(f)
                logger.info(f"Loaded {len(self.purchase_history)} transactions")
        except Exception as e:
            logger.error(f"Error loading transaction log: {e}")
            self.purchase_history = []
    
    def _save_transaction_log(self):
        """Save transaction history with atomic write."""
        try:
            temp_file = self.transaction_log.with_suffix('.json.tmp')
            with open(temp_file, "w") as f:
                json.dump(self.purchase_history, f, indent=2)
            temp_file.replace(self.transaction_log)
            logger.info("Transaction log saved successfully")
        except Exception as e:
            logger.error(f"Error saving transaction log: {e}")
            raise
    
    def _log_transaction(self, transaction: Dict[str, Any]):
        """Log a transaction with timestamp."""
        try:
            transaction["timestamp"] = datetime.now().isoformat()
            self.purchase_history.append(transaction)
            self._save_transaction_log()
            logger.info(f"Logged transaction: {transaction['type']}")
        except Exception as e:
            logger.error(f"Error logging transaction: {e}")
    
    def open_market(self) -> Dict[str, Any]:
        """Open the Njax Market interface."""
        try:
            featured_items = self._get_featured_items()
            cart_summary = self._get_cart_summary()
            
            return {
                "status": "success",
                "message": "Welcome to Njax Market",
                "categories": self.categories,
                "featured_items": featured_items,
                "cart_summary": cart_summary,
                "balance": self.user_balance
            }
        except Exception as e:
            logger.error(f"Error opening market: {e}")
            return {"status": "error", "error": str(e)}
    
    def search_items(self, query: str) -> Dict[str, Any]:
        """Search for items in the market."""
        try:
            query = query.lower()
            results = []
            
            for item_id, item in self.items.items():
                if (query in item["name"].lower() or
                    query in item["description"].lower() or
                    query in item["category"].lower()):
                    results.append({
                        "id": item_id,
                        **item
                    })
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Error searching items: {e}")
            return {"status": "error", "error": str(e)}
    
    def browse_categories(self) -> Dict[str, Any]:
        """Browse items by category."""
        try:
            category_items = {}
            for category_id in self.categories:
                category_items[category_id] = {
                    "category": self.categories[category_id],
                    "items": [
                        {"id": item_id, **item}
                        for item_id, item in self.items.items()
                        if item["category"] == category_id
                    ]
                }
            
            return {
                "status": "success",
                "categories": category_items
            }
        except Exception as e:
            logger.error(f"Error browsing categories: {e}")
            return {"status": "error", "error": str(e)}
    
    def purchase_item(self, item_id: str) -> Dict[str, Any]:
        """Purchase an item from the market."""
        try:
            if item_id not in self.items:
                return {"status": "error", "error": "Item not found"}
            
            item = self.items[item_id]
            if item["stock"] <= 0:
                return {"status": "error", "error": "Item out of stock"}
            
            if self.user_balance < item["price"]:
                return {"status": "error", "error": "Insufficient balance"}
            
            # Process purchase
            self.user_balance -= item["price"]
            item["stock"] -= 1
            
            # Update market data
            self._save_market_data({
                "categories": self.categories,
                "items": self.items
            })
            
            # Log transaction
            transaction = {
                "type": "purchase",
                "item_id": item_id,
                "item_name": item["name"],
                "price": item["price"],
                "balance_after": self.user_balance
            }
            self._log_transaction(transaction)
            
            return {
                "status": "success",
                "message": f"Purchased {item['name']}",
                "item": item,
                "balance": self.user_balance
            }
        except Exception as e:
            logger.error(f"Error purchasing item: {e}")
            return {"status": "error", "error": str(e)}
    
    def add_to_cart(self, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add an item to the shopping cart."""
        try:
            if item_id not in self.items:
                return {"status": "error", "error": "Item not found"}
            
            item = self.items[item_id]
            if item["stock"] < quantity:
                return {"status": "error", "error": "Not enough stock"}
            
            if item_id in self.cart:
                self.cart[item_id]["quantity"] += quantity
            else:
                self.cart[item_id] = {
                    "item": item,
                    "quantity": quantity
                }
            
            return {
                "status": "success",
                "message": f"Added {quantity} {item['name']} to cart",
                "cart": self._get_cart_summary()
            }
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return {"status": "error", "error": str(e)}
    
    def remove_from_cart(self, item_id: str, quantity: int = None) -> Dict[str, Any]:
        """Remove an item from the shopping cart."""
        try:
            if item_id not in self.cart:
                return {"status": "error", "error": "Item not in cart"}
            
            if quantity is None or quantity >= self.cart[item_id]["quantity"]:
                del self.cart[item_id]
            else:
                self.cart[item_id]["quantity"] -= quantity
            
            return {
                "status": "success",
                "message": f"Removed {item_id} from cart",
                "cart": self._get_cart_summary()
            }
        except Exception as e:
            logger.error(f"Error removing from cart: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_cart_summary(self) -> Dict[str, Any]:
        """Get summary of the shopping cart."""
        try:
            total_items = sum(item["quantity"] for item in self.cart.values())
            total_price = sum(
                item["item"]["price"] * item["quantity"]
                for item in self.cart.values()
            )
            
            return {
                "items": [
                    {
                        "id": item_id,
                        "name": item["item"]["name"],
                        "quantity": item["quantity"],
                        "price": item["item"]["price"],
                        "total": item["item"]["price"] * item["quantity"]
                    }
                    for item_id, item in self.cart.items()
                ],
                "total_items": total_items,
                "total_price": total_price
            }
        except Exception as e:
            logger.error(f"Error getting cart summary: {e}")
            return {"items": [], "total_items": 0, "total_price": 0}
    
    def _get_featured_items(self) -> List[Dict[str, Any]]:
        """Get featured items based on price and popularity."""
        try:
            # Sort items by price and get top 5
            sorted_items = sorted(
                self.items.items(),
                key=lambda x: x[1]["price"],
                reverse=True
            )[:5]
            
            return [
                {"id": item_id, **item}
                for item_id, item in sorted_items
            ]
        except Exception as e:
            logger.error(f"Error getting featured items: {e}")
            return []
    
    def get_purchase_history(self) -> Dict[str, Any]:
        """Get user's purchase history."""
        try:
            return {
                "status": "success",
                "history": self.purchase_history,
                "count": len(self.purchase_history),
                "total_spent": sum(
                    t["price"] for t in self.purchase_history
                    if t["type"] == "purchase"
                )
            }
        except Exception as e:
            logger.error(f"Error getting purchase history: {e}")
            return {"status": "error", "error": str(e)}
    
    def add_to_favorites(self, item_id: str) -> Dict[str, Any]:
        """Add an item to favorites."""
        try:
            if item_id not in self.items:
                return {"status": "error", "error": "Item not found"}
            
            self.favorites.add(item_id)
            return {
                "status": "success",
                "message": f"Added {self.items[item_id]['name']} to favorites",
                "favorites": list(self.favorites)
            }
        except Exception as e:
            logger.error(f"Error adding to favorites: {e}")
            return {"status": "error", "error": str(e)}
    
    def remove_from_favorites(self, item_id: str) -> Dict[str, Any]:
        """Remove an item from favorites."""
        try:
            if item_id not in self.favorites:
                return {"status": "error", "error": "Item not in favorites"}
            
            self.favorites.remove(item_id)
            return {
                "status": "success",
                "message": f"Removed {self.items[item_id]['name']} from favorites",
                "favorites": list(self.favorites)
            }
        except Exception as e:
            logger.error(f"Error removing from favorites: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_favorites(self) -> Dict[str, Any]:
        """Get user's favorite items."""
        try:
            favorite_items = [
                {"id": item_id, **self.items[item_id]}
                for item_id in self.favorites
                if item_id in self.items
            ]
            
            return {
                "status": "success",
                "favorites": favorite_items,
                "count": len(favorite_items)
            }
        except Exception as e:
            logger.error(f"Error getting favorites: {e}")
            return {"status": "error", "error": str(e)} 