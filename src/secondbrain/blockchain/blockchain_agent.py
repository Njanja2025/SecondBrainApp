"""
Main blockchain agent for managing all blockchain operations.
"""
import asyncio
import logging
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from .wallet_manager import WalletManager
from .contract_manager import ContractManager
from .network_manager import NetworkManager
from ..memory import MemoryStore
from ..voice_processor import VoiceProcessor

logger = logging.getLogger(__name__)

class BlockchainAgent:
    def __init__(self, memory_store: Optional[MemoryStore] = None, voice_processor: Optional[VoiceProcessor] = None):
        """Initialize the blockchain agent with optional memory store."""
        self.memory_store = memory_store or MemoryStore()
        self.voice_processor = voice_processor
        
        # Initialize managers
        self.network_manager = NetworkManager()
        self.wallet_manager = WalletManager()
        self.contract_manager = None  # Will be initialized after network connection
        
        # Contract templates directory
        self.contract_templates_dir = Path(__file__).parent / "contract_templates"
        self.contract_templates_dir.mkdir(exist_ok=True)
        
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Available contract templates
        self.templates = {
            "token": "basic_template.sol",
            "nft": "nft_template.sol",
            "dao": "dao_template.sol",
            "vesting": "vesting_template.sol",
            "multisig": "multisig_template.sol",
            "dex": "dex_template.sol",
            "marketplace": "marketplace_template.sol"
        }
        
    async def initialize(self):
        """Initialize the blockchain agent."""
        logger.info("Initializing blockchain agent...")
        return True
        
    async def start(self):
        """Start the blockchain agent."""
        if self.running:
            logger.warning("Blockchain agent is already running")
            return
            
        self.running = True
        self._task = asyncio.create_task(self._main_loop())
        
        # Store startup in memory
        if self.memory_store:
            self.memory_store.store(
                memory_type="blockchain_event",
                content={"event": "agent_start"},
                importance=1.0
            )
            
        logger.info("Blockchain agent started")
        
    async def stop(self):
        """Stop the blockchain agent."""
        if not self.running:
            return
            
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
        # Store shutdown in memory
        if self.memory_store:
            self.memory_store.store(
                memory_type="blockchain_event",
                content={"event": "agent_stop"},
                importance=1.0
            )
            
        logger.info("Blockchain agent stopped")
        
    async def _main_loop(self):
        """Main processing loop."""
        try:
            while self.running:
                # Monitor network connection
                if self.network_manager.web3 and not self.network_manager.web3.is_connected():
                    logger.warning("Network connection lost, attempting reconnect...")
                    await self._reconnect()
                    
                # Process any pending operations
                await self._process_operations()
                
                # Prevent CPU spinning
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Blockchain agent loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in blockchain agent loop: {str(e)}")
            if self.memory_store:
                self.memory_store.store(
                    memory_type="blockchain_error",
                    content={"error": str(e)},
                    importance=2.0
                )
            raise
            
    async def _reconnect(self):
        """Attempt to reconnect to the last active network."""
        if not self.network_manager.active_network:
            return
            
        try:
            await self.connect_network(self.network_manager.active_network)
        except Exception as e:
            logger.error(f"Failed to reconnect: {str(e)}")
            
    async def _process_operations(self):
        """Process any pending blockchain operations."""
        # TODO: Implement operation queue processing
        pass
        
    async def connect_network(self, network_name: str) -> bool:
        """Connect to a blockchain network."""
        try:
            web3 = self.network_manager.connect(network_name)
            if web3:
                self.contract_manager = ContractManager(web3)
                
                if self.memory_store:
                    self.memory_store.store(
                        memory_type="blockchain_event",
                        content={
                            "event": "network_connect",
                            "network": network_name
                        }
                    )
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to network: {str(e)}")
            return False
            
    # Wallet Management
    
    def create_wallet(self, name: str) -> Dict[str, str]:
        """Create a new wallet."""
        result = self.wallet_manager.create_wallet(name)
        
        if self.memory_store:
            self.memory_store.store(
                memory_type="blockchain_event",
                content={
                    "event": "wallet_create",
                    "name": name,
                    "address": result["address"]
                }
            )
            
        return result
        
    def import_wallet(self, name: str, private_key: str) -> Dict[str, str]:
        """Import an existing wallet."""
        result = self.wallet_manager.import_wallet(name, private_key)
        
        if self.memory_store:
            self.memory_store.store(
                memory_type="blockchain_event",
                content={
                    "event": "wallet_import",
                    "name": name,
                    "address": result["address"]
                }
            )
            
        return result
        
    # Contract Management
    
    async def deploy_contract(self, 
                            name: str, 
                            abi: List[Dict[str, Any]], 
                            bytecode: str,
                            *args) -> Dict[str, Any]:
        """Deploy a new smart contract."""
        if not self.contract_manager:
            raise ConnectionError("Not connected to any network")
            
        result = await self.contract_manager.deploy_contract(
            name, abi, bytecode, *args
        )
        
        if self.memory_store:
            self.memory_store.store(
                memory_type="blockchain_event",
                content={
                    "event": "contract_deploy",
                    "name": name,
                    "address": result["address"],
                    "transaction_hash": result["transaction_hash"]
                }
            )
            
        return result
        
    async def call_contract(self, 
                          name: str, 
                          method: str, 
                          *args, 
                          **kwargs) -> Any:
        """Call a contract method (read-only)."""
        if not self.contract_manager:
            raise ConnectionError("Not connected to any network")
            
        return await self.contract_manager.call_contract(
            name, method, *args, **kwargs
        )
        
    async def send_transaction(self, 
                             name: str, 
                             method: str, 
                             *args, 
                             **kwargs) -> str:
        """Send a contract transaction (state-changing)."""
        if not self.contract_manager:
            raise ConnectionError("Not connected to any network")
            
        tx_hash = await self.contract_manager.send_transaction(
            name, method, *args, **kwargs
        )
        
        if self.memory_store:
            self.memory_store.store(
                memory_type="blockchain_event",
                content={
                    "event": "contract_transaction",
                    "contract": name,
                    "method": method,
                    "transaction_hash": tx_hash
                }
            )
            
        return tx_hash
        
    # Network Information
    
    async def get_balance(self, address: str) -> float:
        """Get balance of an address."""
        return await self.network_manager.get_balance(address)
        
    async def get_gas_price(self) -> int:
        """Get current gas price."""
        return await self.network_manager.get_gas_price()
        
    def get_network_info(self) -> Optional[Dict]:
        """Get current network information."""
        return self.network_manager.get_active_network()
        
    # Memory and History
    
    def get_transaction_history(self, limit: int = 10) -> List[Dict]:
        """Get recent transaction history."""
        if not self.memory_store:
            return []
            
        return self.memory_store.retrieve(
            memory_type="blockchain_event",
            limit=limit
        )
        
    async def generate_contract(self, name: str, contract_type: str = "token", symbol: Optional[str] = None) -> str:
        """Generate a new smart contract from template."""
        try:
            if contract_type not in self.templates:
                raise ValueError(f"Unknown contract type: {contract_type}")
                
            template = self.templates[contract_type]
            template_path = self.contract_templates_dir / template
            
            if not template_path.exists():
                raise FileNotFoundError(f"Template {template} not found")

            # Read template
            with open(template_path, 'r') as f:
                content = f.read()

            # Replace placeholders
            symbol = symbol or name[:4].upper()
            content = content.replace("{{ContractName}}", name)
            content = content.replace("{{ContractSymbol}}", symbol)

            # Save new contract
            output_path = Path(__file__).parent / "contracts" / f"{name}.sol"
            with open(output_path, 'w') as f:
                f.write(content)

            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"Created {name} {contract_type} contract with symbol {symbol}."
                )

            if self.memory_store:
                self.memory_store.store(
                    memory_type="blockchain_event",
                    content={
                        "event": "contract_generate",
                        "name": name,
                        "type": contract_type,
                        "symbol": symbol
                    }
                )

            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to generate contract: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to create contract: {str(e)}")
            raise

    async def verify_contract(self, contract_address: str, network: str) -> bool:
        """Verify contract source code on block explorer."""
        try:
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            result = await self.contract_manager.verify_contract(
                contract_address,
                network
            )
            
            if self.voice_processor:
                if result:
                    await self.voice_processor.respond_with_voice(
                        f"Contract verified successfully on {network}."
                    )
                else:
                    await self.voice_processor.respond_with_voice(
                        f"Contract verification failed on {network}."
                    )
                    
            return result
            
        except Exception as e:
            logger.error(f"Contract verification failed: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"Contract verification failed: {str(e)}"
                )
            return False

    async def launch_token(self, name: str, symbol: str, initial_supply: int = 1000000) -> Dict[str, Any]:
        """Automate token launch process."""
        try:
            # Generate contract
            contract_path = await self.generate_contract(name, "token", symbol)
            
            # Deploy contract
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            # Compile contract
            compiled = await self.contract_manager.compile_contract(contract_path)
            
            # Deploy
            result = await self.deploy_contract(
                name,
                compiled["abi"],
                compiled["bytecode"],
                initial_supply
            )
            
            # Verify contract
            await self.verify_contract(result["address"], self.network_manager.active_network)
            
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"Token {name} launched successfully at address {result['address']}"
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Token launch failed: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Token launch failed: {str(e)}")
            raise

    async def create_dao(self, name: str, token_address: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new DAO with governance token."""
        try:
            # Generate DAO contract
            contract_path = await self.generate_contract(name, "dao")
            
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            # Deploy timelock controller first
            timelock = await self.contract_manager.deploy_contract(
                "TimelockController",
                [],  # Use default OpenZeppelin contract
                [],
                settings.get("min_delay", 172800),  # 2 days default
                [settings.get("proposer", self.wallet_manager.get_active_address())],
                [settings.get("executor", self.wallet_manager.get_active_address())]
            )
            
            # Deploy DAO with token and timelock
            compiled = await self.contract_manager.compile_contract(contract_path)
            result = await self.deploy_contract(
                name,
                compiled["abi"],
                compiled["bytecode"],
                token_address,
                timelock["address"],
                settings.get("voting_delay", 1),      # 1 block
                settings.get("voting_period", 50400), # 1 week
                settings.get("quorum_percentage", 4), # 4%
                settings.get("proposal_threshold", 0)  # 0 tokens
            )
            
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"DAO {name} created successfully with governance token at {token_address}"
                )
                
            return {
                "dao_address": result["address"],
                "timelock_address": timelock["address"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create DAO: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to create DAO: {str(e)}")
            raise

    async def setup_vesting(self, token_address: str, name: str) -> Dict[str, Any]:
        """Set up token vesting contract."""
        try:
            # Generate vesting contract
            contract_path = await self.generate_contract(name, "vesting")
            
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            # Deploy vesting contract
            compiled = await self.contract_manager.compile_contract(contract_path)
            result = await self.deploy_contract(
                name,
                compiled["abi"],
                compiled["bytecode"],
                token_address
            )
            
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"Vesting contract created for token at {token_address}"
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to setup vesting: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to setup vesting: {str(e)}")
            raise

    async def create_multisig(self, name: str, owners: List[str], required_confirmations: int) -> Dict[str, Any]:
        """Create a multi-signature wallet."""
        try:
            # Generate multisig contract
            contract_path = await self.generate_contract(name, "multisig")
            
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            # Deploy multisig contract
            compiled = await self.contract_manager.compile_contract(contract_path)
            result = await self.deploy_contract(
                name,
                compiled["abi"],
                compiled["bytecode"],
                owners,
                required_confirmations
            )
            
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"Multisig wallet created with {len(owners)} owners and {required_confirmations} required confirmations"
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to create multisig: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to create multisig: {str(e)}")
            raise

    async def create_dex(self, name: str, fee: int = 30) -> Dict[str, Any]:
        """Create a new DEX with AMM functionality."""
        try:
            # Generate DEX contract
            contract_path = await self.generate_contract(name, "dex")
            
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            # Deploy DEX contract
            compiled = await self.contract_manager.compile_contract(contract_path)
            result = await self.deploy_contract(
                name,
                compiled["abi"],
                compiled["bytecode"]
            )
            
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"DEX {name} created with {fee/100}% fee"
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to create DEX: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to create DEX: {str(e)}")
            raise

    async def create_marketplace(
        self,
        name: str,
        payment_token: str,
        platform_fee: int = 250  # 2.5%
    ) -> Dict[str, Any]:
        """Create a new NFT marketplace."""
        try:
            # Generate marketplace contract
            contract_path = await self.generate_contract(name, "marketplace")
            
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            # Deploy marketplace contract
            compiled = await self.contract_manager.compile_contract(contract_path)
            result = await self.deploy_contract(
                name,
                compiled["abi"],
                compiled["bytecode"],
                payment_token,
                platform_fee
            )
            
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"NFT Marketplace {name} created with {platform_fee/100}% platform fee"
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to create marketplace: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to create marketplace: {str(e)}")
            raise

    async def create_liquidity_pool(
        self,
        dex_address: str,
        token0: str,
        token1: str,
        amount0: int,
        amount1: int,
        fee: int = 30  # 0.3%
    ) -> Dict[str, Any]:
        """Create a new liquidity pool in the DEX."""
        try:
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            # Create pool
            result = await self.contract_manager.send_transaction(
                dex_address,
                "createPool",
                token0,
                token1,
                fee
            )
            
            # Add initial liquidity
            await self.contract_manager.send_transaction(
                dex_address,
                "addLiquidity",
                token0,
                token1,
                amount0,
                amount1,
                amount0 * 95 // 100,  # 5% slippage tolerance
                amount1 * 95 // 100
            )
            
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(
                    f"Liquidity pool created with {amount0} token0 and {amount1} token1"
                )
                
            return {
                "pool_created": True,
                "token0": token0,
                "token1": token1,
                "amount0": amount0,
                "amount1": amount1,
                "transaction_hash": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create liquidity pool: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to create liquidity pool: {str(e)}")
            raise

    async def list_nft(
        self,
        marketplace_address: str,
        nft_contract: str,
        token_id: int,
        price: int,
        is_auction: bool = False,
        auction_duration: int = 86400,  # 1 day
        royalty_percentage: int = 250,  # 2.5%
        royalty_receiver: Optional[str] = None
    ) -> Dict[str, Any]:
        """List an NFT for sale or auction."""
        try:
            if not self.contract_manager:
                raise ConnectionError("Not connected to any network")
                
            royalty_receiver = royalty_receiver or self.wallet_manager.get_active_address()
            
            result = await self.contract_manager.send_transaction(
                marketplace_address,
                "createListing",
                nft_contract,
                token_id,
                price,
                is_auction,
                auction_duration,
                royalty_percentage,
                royalty_receiver
            )
            
            if self.voice_processor:
                action = "auction" if is_auction else "sale"
                await self.voice_processor.respond_with_voice(
                    f"NFT listed for {action} at price {price}"
                )
                
            return {
                "listing_created": True,
                "nft_contract": nft_contract,
                "token_id": token_id,
                "price": price,
                "is_auction": is_auction,
                "transaction_hash": result
            }
            
        except Exception as e:
            logger.error(f"Failed to list NFT: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to list NFT: {str(e)}")
            raise

    async def handle_voice_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Handle voice commands for blockchain operations."""
        try:
            command = command.lower()
            
            # Create contract commands
            if "create" in command:
                words = command.split()
                contract_type = "token"  # default
                
                if "nft" in words:
                    contract_type = "nft"
                elif "dao" in words:
                    contract_type = "dao"
                elif "vesting" in words:
                    contract_type = "vesting"
                elif "multisig" in words:
                    contract_type = "multisig"
                elif "dex" in words:
                    contract_type = "dex"
                elif "marketplace" in words:
                    contract_type = "marketplace"
                    
                name_index = words.index("called") + 1 if "called" in words else -1
                if name_index >= 0 and name_index < len(words):
                    contract_name = words[name_index]
                    
                    if contract_type == "dex":
                        # Extract fee if provided
                        fee = 30  # default 0.3%
                        if "fee" in words:
                            fee = int(float(words[words.index("fee") + 1]) * 100)
                            
                        result = await self.create_dex(contract_name, fee)
                        return {
                            "action": "dex_created",
                            "name": contract_name,
                            "fee": fee,
                            "address": result["address"]
                        }
                        
                    elif contract_type == "marketplace":
                        # Extract payment token and fee
                        payment_token = None
                        fee = 250  # default 2.5%
                        
                        if "token" in words:
                            payment_token = words[words.index("token") + 1]
                        if "fee" in words:
                            fee = int(float(words[words.index("fee") + 1]) * 100)
                            
                        result = await self.create_marketplace(
                            contract_name,
                            payment_token or await self.deploy_payment_token(contract_name),
                            fee
                        )
                        return {
                            "action": "marketplace_created",
                            "name": contract_name,
                            "fee": fee,
                            "address": result["address"]
                        }
                        
                    elif contract_type == "dao":
                        # Extract token address if provided
                        token_address = None
                        if "token" in words and words.index("token") + 1 < len(words):
                            token_address = words[words.index("token") + 1]
                            
                        result = await self.create_dao(
                            contract_name,
                            token_address or await self.deploy_governance_token(contract_name),
                            {}  # Use default settings
                        )
                        return {
                            "action": "dao_created",
                            "name": contract_name,
                            "addresses": result
                        }
                        
                    elif contract_type == "multisig":
                        # Extract owners and confirmations
                        owners = [self.wallet_manager.get_active_address()]  # Start with active wallet
                        required = 1
                        
                        if "owners" in words:
                            owner_addresses = command.split("owners")[1].split("required")[0].strip().split()
                            owners.extend(owner_addresses)
                            
                        if "required" in words:
                            required = int(words[words.index("required") + 1])
                            
                        result = await self.create_multisig(contract_name, owners, required)
                        return {
                            "action": "multisig_created",
                            "name": contract_name,
                            "address": result["address"]
                        }
                        
                    else:
                        contract_path = await self.generate_contract(contract_name, contract_type)
                        return {
                            "action": "contract_created",
                            "name": contract_name,
                            "type": contract_type,
                            "path": contract_path
                        }
                        
            # Pool creation command
            elif "create pool" in command:
                words = command.split()
                dex_address = None
                token0 = None
                token1 = None
                amount0 = 0
                amount1 = 0
                fee = 30  # default 0.3%
                
                if "dex" in words:
                    dex_address = words[words.index("dex") + 1]
                if "token0" in words:
                    token0 = words[words.index("token0") + 1]
                if "token1" in words:
                    token1 = words[words.index("token1") + 1]
                if "amount0" in words:
                    amount0 = int(words[words.index("amount0") + 1])
                if "amount1" in words:
                    amount1 = int(words[words.index("amount1") + 1])
                if "fee" in words:
                    fee = int(float(words[words.index("fee") + 1]) * 100)
                    
                result = await self.create_liquidity_pool(
                    dex_address,
                    token0,
                    token1,
                    amount0,
                    amount1,
                    fee
                )
                return {
                    "action": "pool_created",
                    "dex": dex_address,
                    "token0": token0,
                    "token1": token1,
                    "amounts": [amount0, amount1]
                }
                
            # NFT listing command
            elif "list nft" in command:
                words = command.split()
                marketplace = None
                nft_contract = None
                token_id = None
                price = None
                is_auction = "auction" in command
                duration = 86400  # default 1 day
                royalty = 250  # default 2.5%
                
                if "marketplace" in words:
                    marketplace = words[words.index("marketplace") + 1]
                if "contract" in words:
                    nft_contract = words[words.index("contract") + 1]
                if "token" in words:
                    token_id = int(words[words.index("token") + 1])
                if "price" in words:
                    price = int(words[words.index("price") + 1])
                if "duration" in words:
                    duration = int(words[words.index("duration") + 1]) * 86400  # convert days to seconds
                if "royalty" in words:
                    royalty = int(float(words[words.index("royalty") + 1]) * 100)
                    
                result = await self.list_nft(
                    marketplace,
                    nft_contract,
                    token_id,
                    price,
                    is_auction,
                    duration,
                    royalty
                )
                return {
                    "action": "nft_listed",
                    "marketplace": marketplace,
                    "nft_contract": nft_contract,
                    "token_id": token_id,
                    "price": price,
                    "is_auction": is_auction
                }
                
            return None

        except Exception as e:
            logger.error(f"Failed to handle voice command: {str(e)}")
            if self.voice_processor:
                await self.voice_processor.respond_with_voice(f"Failed to process command: {str(e)}")
            return None 