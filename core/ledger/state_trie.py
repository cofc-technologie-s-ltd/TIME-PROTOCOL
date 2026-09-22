import hashlib
import json
from typing import Dict, Any

class StateLedger:
    def __init__(self):
        self.balances: Dict[str, float] = {}
        self.nonces: Dict[str, int] = {}
        self.latest_block_index = 0

    def get_balance(self, address: str) -> float:
        return self.balances.get(address, 100.0)

    def set_balance(self, address: str, amount: float):
        self.balances[address] = amount

    def apply_transaction(self, tx) -> bool:
        sender = getattr(tx, "sender", "GENESIS")
        recipient = getattr(tx, "recipient", "SYSTEM")
        amount = getattr(tx, "amount", 0.0)

        if sender != "GENESIS":
            current_bal = self.get_balance(sender)
            if current_bal < amount:
                return False
            self.set_balance(sender, current_bal - amount)

        rec_bal = self.get_balance(recipient)
        self.set_balance(recipient, rec_bal + amount)
        return True

    def get_state_root(self) -> str:
        state_data = {
            "balances": self.balances,
            "nonces": self.nonces,
            "height": self.latest_block_index
        }
        raw = json.dumps(state_data, sort_keys=True).encode('utf-8')
        return hashlib.sha3_256(raw).hexdigest()
