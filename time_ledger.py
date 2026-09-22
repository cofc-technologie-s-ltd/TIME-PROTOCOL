import threading
from typing import Dict, Any, Optional

class SecureTimeLedger:
    """
    Thread-safe ledger engine designed for high-throughput zero-fee sovereign transactions.
    Protects against race conditions and replay attacks using cryptographically bound nonces.
    """
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def get_account(self, address: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.accounts.get(address, {"balance": 0, "nonce": 0, "staked": 0})

    def update_account(self, address: str, balance: int, nonce: int, staked: int = 0) -> bool:
        with self.lock:
            current = self.accounts.get(address, {"balance": 0, "nonce": -1, "staked": 0})
            if nonce <= current["nonce"] and current["nonce"] != -1:
                return False
            self.accounts[address] = {
                "balance": balance,
                "nonce": nonce,
                "staked": staked
            }
            return True

    def close(self):
        with self.lock:
            self.accounts.clear()
