"""
TIME Protocol - Simple Smart Contracts
Minimal VM with storage, functions, and events.
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional


class ContractStorage:
    """Persistent storage for a contract."""
    
    def __init__(self, contract_address: str):
        self.contract_address = contract_address
        self.data: Dict[str, Any] = {}
        self.events: List[dict] = []
    
    def get(self, key: str, default=None):
        return self.data.get(key, default)
    
    def set(self, key: str, value):
        self.data[key] = value
    
    def emit_event(self, name: str, data: dict):
        event = {
            "contract": self.contract_address,
            "event": name,
            "data": data,
            "timestamp": time.time(),
        }
        self.events.append(event)
        return event
    
    def to_dict(self):
        return {
            "contract_address": self.contract_address,
            "data": self.data,
            "events_count": len(self.events),
        }


class Contract:
    """A deployed smart contract."""
    
    def __init__(self, address: str, owner: str, code: str, initial_state: dict = None):
        self.address = address
        self.owner = owner
        self.code = code
        self.storage = ContractStorage(address)
        self.created_at = time.time()
        
        if initial_state:
            for k, v in initial_state.items():
                self.storage.set(k, v)
    
    def to_dict(self):
        return {
            "address": self.address,
            "owner": self.owner,
            "code": self.code,
            "storage": self.storage.to_dict(),
            "created_at": self.created_at,
        }


class ContractVM:
    """
    Minimal smart contract VM.
    
    Contracts are Python expressions with context:
    - storage.get(key), storage.set(key, value)
    - event(name, data)
    """
    
    DEPLOY_FEE = 100.0
    CALL_FEE = 1.0
    
    def __init__(self, node):
        self.node = node
        self.contracts: Dict[str, Contract] = {}
    
    def deploy(self, owner: str, code: str, initial_state: dict = None) -> dict:
        address_data = f"{owner}:{code}:{time.time()}"
        address = "CONTRACT_" + hashlib.sha256(address_data.encode()).hexdigest()[:40]
        
        contract = Contract(address, owner, code, initial_state)
        self.contracts[address] = contract
        
        return {
            "status": "DEPLOYED",
            "address": address,
            "owner": owner,
            "fee": self.DEPLOY_FEE,
        }
    
    def call(self, caller: str, contract_address: str, method: str, args: dict = None) -> dict:
        if contract_address not in self.contracts:
            return {"status": "ERROR", "error": "Contract not found"}
        
        contract = self.contracts[contract_address]
        args = args or {}
        
        context = {
            "storage": contract.storage,
            "sender": caller,
            "balance_of": lambda addr: self.node.ledger.get_balance(addr),
            "event": lambda name, data: contract.storage.emit_event(name, data),
            "args": args,
        }
        
        try:
            methods = json.loads(contract.code) if contract.code.startswith("{") else {"default": contract.code}
            
            if method not in methods:
                return {"status": "ERROR", "error": f"Method not found: {method}"}
            
            expression = methods[method]
            result = eval(expression, {"__builtins__": {}}, context)
            
            return {
                "status": "SUCCESS",
                "result": result,
                "events": contract.storage.events[-5:],
                "fee": self.CALL_FEE,
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def get_contract(self, address: str) -> Optional[dict]:
        if address not in self.contracts:
            return None
        return self.contracts[address].to_dict()
    
    def list_contracts(self) -> List[dict]:
        return [c.to_dict() for c in self.contracts.values()]
    
    def get_stats(self) -> dict:
        return {
            "total_contracts": len(self.contracts),
            "total_events": sum(len(c.storage.events) for c in self.contracts.values()),
        }
