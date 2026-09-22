import hashlib
import json

class RealStateLedger:
    """
    Cryptographic State Ledger utilizing full public keys (hex) as account identifiers.
    Eliminates capacity limits and modulo collisions entirely.
    """
    def __init__(self):
        # Maps public_key_hex -> account state (balance, nonce, etc.)
        self.accounts = {}
        self.latest_block_index = 0  # Compatibility attribute for API/nodes

    def get_balance(self, pub_key: str) -> float:
        return self.accounts.get(pub_key, {}).get("balance", 0.0)

    def get_nonce(self, pub_key: str) -> int:
        return self.accounts.get(pub_key, {}).get("nonce", 0)

    def set_balance(self, pub_key: str, balance: float):
        if pub_key not in self.accounts:
            self.accounts[pub_key] = {"balance": 0.0, "nonce": 0}
        self.accounts[pub_key]["balance"] = balance

    def apply_transaction(self, sender: str, recipient: str, amount: float, signature: str) -> bool:
        if amount <= 0:
            return False
        
        sender_balance = self.get_balance(sender)
        if sender_balance < amount:
            return False

        # Update balances
        self.set_balance(sender, sender_balance - amount)
        self.set_balance(recipient, self.get_balance(recipient) + amount)
        
        # Increment sender nonce & block index simulation
        self.accounts[sender]["nonce"] += 1
        self.latest_block_index += 1
        return True

    def get_state_root(self) -> str:
        state_str = json.dumps(self.accounts, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

# Backward compatibility alias for older integration tests
StateLedger = RealStateLedger
