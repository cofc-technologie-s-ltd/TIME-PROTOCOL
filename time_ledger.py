import threading
from typing import Dict, Any, Optional

class SecureTimeLedger:
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def get_account(self, address: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.accounts.get(address, {"balance": 0, "nonce": 0})

    def update_account(self, address: str, balance: int, nonce: int) -> bool:
        with self.lock:
            current = self.accounts.get(address, {"balance": 0, "nonce": -1})
            if nonce <= current["nonce"] and current["nonce"] != -1:
                return False
            self.accounts[address] = {"balance": balance, "nonce": nonce}
            return True

    def close(self):
        with self.lock:
            self.accounts.clear()
