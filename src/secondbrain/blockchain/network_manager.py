"""
Blockchain network management system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from web3 import Web3, HTTPProvider
from eth_typing import URI
from eth_utils import to_checksum_address

logger = logging.getLogger(__name__)


class NetworkManager:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize network manager with optional config path."""
        if config_path is None:
            config_path = str(Path.home() / ".secondbrain" / "networks.json")

        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.networks: Dict[str, Dict] = {}
        self.active_network: Optional[str] = None
        self.web3: Optional[Web3] = None

        self._load_networks()

    def _load_networks(self):
        """Load network configurations from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    self.networks = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load networks: {str(e)}")

    def _save_networks(self):
        """Save network configurations to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.networks, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save networks: {str(e)}")

    def add_network(
        self,
        name: str,
        rpc_url: str,
        chain_id: int,
        currency_symbol: str = "ETH",
        explorer_url: Optional[str] = None,
    ) -> bool:
        """Add a new network configuration."""
        try:
            # Validate RPC connection
            web3 = Web3(HTTPProvider(URI(rpc_url)))
            if not web3.is_connected():
                raise ConnectionError("Failed to connect to RPC endpoint")

            self.networks[name] = {
                "rpc_url": rpc_url,
                "chain_id": chain_id,
                "currency_symbol": currency_symbol,
                "explorer_url": explorer_url,
            }

            self._save_networks()
            return True

        except Exception as e:
            logger.error(f"Failed to add network: {str(e)}")
            return False

    def remove_network(self, name: str) -> bool:
        """Remove a network configuration."""
        if name not in self.networks:
            return False

        if self.active_network == name:
            self.disconnect()

        del self.networks[name]
        self._save_networks()
        return True

    def list_networks(self) -> List[Dict]:
        """List all configured networks."""
        return [{"name": name, **config} for name, config in self.networks.items()]

    def connect(self, network_name: str) -> Optional[Web3]:
        """Connect to a configured network."""
        if network_name not in self.networks:
            raise ValueError(f"Network '{network_name}' not found")

        try:
            network = self.networks[network_name]
            web3 = Web3(HTTPProvider(URI(network["rpc_url"])))

            if not web3.is_connected():
                raise ConnectionError("Failed to connect to network")

            self.web3 = web3
            self.active_network = network_name

            logger.info(f"Connected to network: {network_name}")
            return web3

        except Exception as e:
            logger.error(f"Failed to connect to network: {str(e)}")
            self.web3 = None
            self.active_network = None
            raise

    def disconnect(self):
        """Disconnect from current network."""
        self.web3 = None
        self.active_network = None

    def get_active_network(self) -> Optional[Dict]:
        """Get current network information."""
        if not self.active_network:
            return None

        return {"name": self.active_network, **self.networks[self.active_network]}

    async def get_balance(self, address: str) -> float:
        """Get balance of address in network's native currency."""
        if not self.web3:
            raise ConnectionError("Not connected to any network")

        try:
            balance_wei = await self.web3.eth.get_balance(to_checksum_address(address))
            return float(Web3.from_wei(balance_wei, "ether"))
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            raise

    async def get_transaction_count(self, address: str) -> int:
        """Get transaction count (nonce) for address."""
        if not self.web3:
            raise ConnectionError("Not connected to any network")

        try:
            return await self.web3.eth.get_transaction_count(
                to_checksum_address(address)
            )
        except Exception as e:
            logger.error(f"Failed to get transaction count: {str(e)}")
            raise

    async def get_gas_price(self) -> int:
        """Get current gas price in wei."""
        if not self.web3:
            raise ConnectionError("Not connected to any network")

        try:
            return await self.web3.eth.gas_price
        except Exception as e:
            logger.error(f"Failed to get gas price: {str(e)}")
            raise
