"""
Web3 Wallet Manager for blockchain interactions.
"""
import os
import json
from typing import Dict, Any, Optional
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_utils import to_checksum_address
from dotenv import load_dotenv
from ..phantom.phantom_core import PhantomCore

logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self):
        load_dotenv()
        
        # Initialize Web3 connection
        self.network = os.getenv("ETHEREUM_NETWORK", "sepolia")
        self.w3 = self._initialize_web3()
        
        # Add PoA middleware for testnets
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Initialize Phantom Core
        self.phantom = PhantomCore()
        
        # Initialize account if private key is available
        self.account = None
        private_key = os.getenv("PRIVATE_KEY")
        if private_key:
            self.account = Account.from_key(private_key)
            self.phantom.log_event(
                "Wallet",
                f"Initialized for address: {self.account.address}"
            )
            logger.info(f"Wallet initialized for address: {self.account.address}")

    def _initialize_web3(self) -> Web3:
        """Initialize Web3 connection based on network."""
        networks = {
            "mainnet": f"https://mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}",
            "sepolia": f"https://sepolia.infura.io/v3/{os.getenv('INFURA_API_KEY')}",
            "goerli": f"https://goerli.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
        }
        
        if self.network not in networks:
            error_msg = f"Unsupported network: {self.network}"
            self.phantom.log_event("Web3 Init", error_msg, "ERROR")
            raise ValueError(error_msg)
            
        return Web3(Web3.HTTPProvider(networks[self.network]))

    async def get_balance(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Get wallet balance in Ether."""
        try:
            if not address and self.account:
                address = self.account.address
            
            if not address:
                error_msg = "No wallet address provided"
                self.phantom.log_event("Balance Check", error_msg, "ERROR")
                raise ValueError(error_msg)
                
            address = to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            result = {
                "status": "success",
                "address": address,
                "balance_eth": float(balance_eth),
                "balance_wei": balance_wei,
                "network": self.network
            }
            
            self.phantom.log_event(
                "Balance Check",
                f"Address {address}: {float(balance_eth)} ETH"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error getting wallet balance: {str(e)}"
            self.phantom.log_event("Balance Error", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    async def send_transaction(self, to_address: str, amount_eth: float, gas_limit: int = 21000) -> Dict[str, Any]:
        """Send Ether to another address."""
        try:
            if not self.account:
                error_msg = "No wallet account configured"
                self.phantom.log_event("Transaction", error_msg, "ERROR")
                raise ValueError(error_msg)
                
            to_address = to_checksum_address(to_address)
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # Log transaction attempt
            self.phantom.log_event(
                "Transaction",
                f"Sending {amount_eth} ETH to {to_address}"
            )
            
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Get gas price
            gas_price = self.w3.eth.gas_price
            
            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': amount_wei,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            result = {
                "status": "success",
                "transaction_hash": tx_hash.hex(),
                "from_address": self.account.address,
                "to_address": to_address,
                "amount_eth": amount_eth,
                "network": self.network
            }
            
            # Log successful transaction
            self.phantom.log_event(
                "Transaction",
                f"Sent {amount_eth} ETH to {to_address}. Hash: {tx_hash.hex()}"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error sending transaction: {str(e)}"
            self.phantom.log_event("Transaction Error", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    async def get_transaction_history(self, address: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get transaction history for an address."""
        try:
            if not address and self.account:
                address = self.account.address
            
            if not address:
                error_msg = "No wallet address provided"
                self.phantom.log_event("History", error_msg, "ERROR")
                raise ValueError(error_msg)
                
            address = to_checksum_address(address)
            
            self.phantom.log_event(
                "History",
                f"Fetching transaction history for {address}"
            )
            
            # Get latest block number
            latest_block = self.w3.eth.block_number
            
            # Get transactions
            transactions = []
            for i in range(limit):
                block = self.w3.eth.get_block(latest_block - i, full_transactions=True)
                for tx in block.transactions:
                    if tx['to'] == address or tx['from'] == address:
                        transactions.append({
                            "hash": tx['hash'].hex(),
                            "from": tx['from'],
                            "to": tx['to'],
                            "value_eth": self.w3.from_wei(tx['value'], 'ether'),
                            "block_number": tx['blockNumber'],
                            "timestamp": block.timestamp
                        })
            
            result = {
                "status": "success",
                "address": address,
                "transactions": transactions,
                "network": self.network
            }
            
            self.phantom.log_event(
                "History",
                f"Found {len(transactions)} transactions for {address}"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error getting transaction history: {str(e)}"
            self.phantom.log_event("History Error", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def get_wallet_info(self) -> Dict[str, Any]:
        """Get current wallet information."""
        try:
            info = {
                "address": self.account.address if self.account else None,
                "network": self.network,
                "is_connected": self.w3.is_connected(),
                "chain_id": self.w3.eth.chain_id,
                "latest_block": self.w3.eth.block_number,
                "phantom_status": self.phantom.get_status()
            }
            
            self.phantom.log_event(
                "Wallet Info",
                f"Connected to {self.network}, latest block: {info['latest_block']}"
            )
            
            return info
            
        except Exception as e:
            error_msg = f"Error getting wallet info: {str(e)}"
            self.phantom.log_event("Info Error", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    async def estimate_gas(self, to_address: str, amount_eth: float) -> Dict[str, Any]:
        """Estimate gas cost for a transaction."""
        try:
            if not self.account:
                error_msg = "No wallet account configured"
                self.phantom.log_event("Gas Estimate", error_msg, "ERROR")
                raise ValueError(error_msg)
                
            to_address = to_checksum_address(to_address)
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # Build transaction for estimation
            transaction = {
                'from': self.account.address,
                'to': to_address,
                'value': amount_wei
            }
            
            # Estimate gas
            gas_estimate = self.w3.eth.estimate_gas(transaction)
            gas_price = self.w3.eth.gas_price
            total_cost_wei = gas_estimate * gas_price
            
            result = {
                "status": "success",
                "gas_estimate": gas_estimate,
                "gas_price_wei": gas_price,
                "total_cost_eth": self.w3.from_wei(total_cost_wei, 'ether'),
                "network": self.network
            }
            
            self.phantom.log_event(
                "Gas Estimate",
                f"Estimated gas: {gas_estimate}, total cost: {result['total_cost_eth']} ETH"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error estimating gas: {str(e)}"
            self.phantom.log_event("Gas Error", error_msg, "ERROR")
            logger.error(error_msg)
            return {"status": "error", "message": error_msg} 