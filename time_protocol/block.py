import time
from typing import List, Dict, Any
from .crypto import hash_data, MerkleTree
from .transaction import Transaction


class Block:
    def __init__(self, index: int, previous_hash: str,
                 transactions: List[Transaction], nonce: int = 0,
                 timestamp: float = None, difficulty: int = 2):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.nonce = nonce
        self.timestamp = timestamp or time.time()
        self.difficulty = difficulty
        self.merkle_root = MerkleTree(self.transactions).root
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "difficulty": self.difficulty,
        }
        return hash_data(str(block_data))

    def mine(self, difficulty: int = None) -> int:
        if difficulty is not None:
            self.difficulty = difficulty
        target = "0" * self.difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.nonce

    def is_valid(self, previous_block: 'Block' = None) -> bool:
        if self.index < 0:
            return False
        target = "0" * self.difficulty
        if not self.hash.startswith(target):
            return False
        if self.hash != self.calculate_hash():
            return False
        if previous_block:
            if self.index != previous_block.index + 1:
                return False
            if self.previous_hash != previous_block.hash:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "difficulty": self.difficulty,
            "merkle_root": self.merkle_root,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Block':
        txs = [Transaction.from_dict(t) for t in d["transactions"]]
        block = cls(
            index=d["index"],
            previous_hash=d["previous_hash"],
            transactions=txs,
            nonce=d["nonce"],
            timestamp=d["timestamp"],
            difficulty=d.get("difficulty", 2),
        )
        block.hash = d["hash"]
        block.merkle_root = d["merkle_root"]
        return block
