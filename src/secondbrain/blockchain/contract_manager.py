"""
Smart contract management system for blockchain operations.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.contract import Contract

logger = logging.getLogger(__name__)

class ContractManager:
    def __init__(self, web3: Web3, storage_path: Optional[str] = None):
        """Initialize contract manager with Web3 instance and optional storage path."""
        self.web3 = web3
        
        if storage_path is None:
            storage_path = str(Path.home() / '.secondbrain' / 'contracts')
            
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.contracts: Dict[str, Contract] = {}
        self._load_contracts()
        
    def _load_contracts(self):
        """Load existing contract ABIs and addresses from storage."""
        try:
            contracts_file = self.storage_path / 'contracts.json'
            if contracts_file.exists():
                with open(contracts_file, 'r') as f:
                    stored_contracts = json.load(f)
                    
                for name, data in stored_contracts.items():
                    contract = self.web3.eth.contract(
                        address=data['address'],
                        abi=data['abi']
                    )
                    self.contracts[name] = contract
                    
        except Exception as e:
            logger.error(f"Failed to load contracts: {str(e)}")
            
    def _save_contracts(self):
        """Save contract information to storage."""
        try:
            contract_data = {
                name: {
                    'address': contract.address,
                    'abi': contract.abi
                }
                for name, contract in self.contracts.items()
            }
            
            with open(self.storage_path / 'contracts.json', 'w') as f:
                json.dump(contract_data, f)
                
        except Exception as e:
            logger.error(f"Failed to save contracts: {str(e)}")
            
    def deploy_contract(self, 
                       name: str, 
                       abi: List[Dict[str, Any]], 
                       bytecode: str,
                       *args) -> Dict[str, Any]:
        """Deploy a new contract with constructor arguments."""
        try:
            contract = self.web3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Estimate gas
            gas_estimate = contract.constructor(*args).estimate_gas()
            
            # Deploy contract
            tx_hash = contract.constructor(*args).transact({
                'gas': int(gas_estimate * 1.2)  # Add 20% buffer
            })
            
            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Create contract instance
            deployed_contract = self.web3.eth.contract(
                address=tx_receipt.contractAddress,
                abi=abi
            )
            
            self.contracts[name] = deployed_contract
            self._save_contracts()
            
            return {
                "name": name,
                "address": deployed_contract.address,
                "transaction_hash": tx_hash.hex()
            }
            
        except Exception as e:
            logger.error(f"Failed to deploy contract: {str(e)}")
            raise
            
    def load_contract(self, 
                     name: str, 
                     address: str, 
                     abi: List[Dict[str, Any]]) -> Dict[str, str]:
        """Load an existing contract by address and ABI."""
        try:
            contract = self.web3.eth.contract(address=address, abi=abi)
            self.contracts[name] = contract
            self._save_contracts()
            
            return {
                "name": name,
                "address": address
            }
            
        except Exception as e:
            logger.error(f"Failed to load contract: {str(e)}")
            raise
            
    def get_contract(self, name: str) -> Optional[Contract]:
        """Get contract instance by name."""
        return self.contracts.get(name)
        
    def list_contracts(self) -> List[Dict[str, str]]:
        """List all managed contracts."""
        return [
            {
                "name": name,
                "address": contract.address
            }
            for name, contract in self.contracts.items()
        ]
        
    def remove_contract(self, name: str) -> bool:
        """Remove a contract from management."""
        if name not in self.contracts:
            return False
            
        del self.contracts[name]
        self._save_contracts()
        return True
        
    async def call_contract(self, 
                          name: str, 
                          method: str, 
                          *args, 
                          **kwargs) -> Any:
        """Call a contract method (read-only)."""
        contract = self.get_contract(name)
        if not contract:
            raise ValueError(f"Contract '{name}' not found")
            
        try:
            contract_method = getattr(contract.functions, method)
            return await contract_method(*args).call(**kwargs)
        except Exception as e:
            logger.error(f"Contract call failed: {str(e)}")
            raise
            
    async def send_transaction(self, 
                             name: str, 
                             method: str, 
                             *args, 
                             **kwargs) -> str:
        """Send a contract transaction (state-changing)."""
        contract = self.get_contract(name)
        if not contract:
            raise ValueError(f"Contract '{name}' not found")
            
        try:
            contract_method = getattr(contract.functions, method)
            
            # Estimate gas
            gas_estimate = await contract_method(*args).estimate_gas(**kwargs)
            
            # Send transaction
            tx_hash = await contract_method(*args).transact({
                **kwargs,
                'gas': int(gas_estimate * 1.2)  # Add 20% buffer
            })
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise 