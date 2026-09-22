import time
from typing import List, Dict, Any
from .crypto import hash_data, MerkleTree
from .transaction import Transaction

class Block:
    def __init__(self, index: int, previous_hash: str, transactions: List[Transaction], nonce: int = 0, timestamp: float = None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.nonce = nonce
        self.timestamp = timestamp or time.time()
        self.merkle_root = MerkleTree(self.transactions).root
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "timestamp": self.timestamp
        }
        return hash_data(str(block_data))

    def mine(self, difficulty: int):
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def is_valid(self, previous_block: 'Block' = None) -> bool:
        if previous_block and self.index != previous_block.index + 1:
            return False
        if previous_block and self.previous_hash != previous_block.hash:
            return False
        if self.hash != self.calculate_hash():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Block':
        txs = [Transaction.from_dict(t) for t in d["transactions"]]
        block = cls(d["index"], d["previous_hash"], txs, d["nonce"], d["timestamp"])
        block.hash = d["hash"]
        block.merkle_root = d["merkle_root"]
        return block
