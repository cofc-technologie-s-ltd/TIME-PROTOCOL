import hashlib
import json

class ProductionStateLedger:
    def __init__(self):
        self.accounts = {}
        self.latest_block_index = 0

    def get_balance(self, pub_key: str) -> float:
        return self.accounts.get(pub_key, {}).get("balance", 0.0)

    def set_balance(self, pub_key: str, balance: float):
        if pub_key not in self.accounts:
            self.accounts[pub_key] = {"balance": 0.0, "nonce": 0}
        self.accounts[pub_key]["balance"] = balance

    def apply_transaction(self, sender: str, recipient: str, amount: float, signature: str) -> bool:
        if amount <= 0:
            return False
        sender_bal = self.get_balance(sender)
        if sender_bal < amount:
            return False
        self.set_balance(sender, sender_bal - amount)
        self.set_balance(recipient, self.get_balance(recipient) + amount)
        self.accounts[sender]["nonce"] += 1
        self.latest_block_index += 1
        return True

    def get_state_root(self) -> str:
        state_str = json.dumps(self.accounts, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()
