from .ledger import Ledger
from .block import Block
from .transaction import TransactionBuilder


class Node:
    def __init__(self, difficulty: int = 2):
        self.ledger = Ledger()
        self.difficulty = difficulty
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_tx = TransactionBuilder.create_coinbase("GENESIS_ADDRESS", 1000.0)
        genesis_block = Block(
            index=0,
            previous_hash="0" * 64,
            transactions=[genesis_tx]
        )
        genesis_block.mine(self.difficulty)
        self.ledger.add_block(genesis_block)

    def mine_pending_transactions(self, miner_address: str, transactions: list) -> Block:
        reward_tx = TransactionBuilder.create_coinbase(miner_address, 50.0)
        all_txs = [reward_tx] + transactions
        new_block = Block(
            index=self.ledger.latest_block.index + 1,
            previous_hash=self.ledger.latest_block.hash,
            transactions=all_txs
        )
        new_block.mine(self.difficulty)
        self.ledger.add_block(new_block)
        return new_block

    def clear_chain(self):
        """Clear the entire chain. Used when loading from disk."""
        self.ledger = Ledger()
    
    def is_chain_valid(self) -> bool:
        """Convenience: proxy to ledger's validation."""
        return self.ledger.is_chain_valid()
    
    def __repr__(self) -> str:
        return f"Node(height={self.ledger.height}, difficulty={self.difficulty})"
