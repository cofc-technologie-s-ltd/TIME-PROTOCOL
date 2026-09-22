from .ledger import Ledger
from .block import Block
from .transaction import TransactionBuilder
from .difficulty import DifficultyManager


class Node:
    def __init__(self, difficulty: int = 2, target_block_time: float = 10.0,
                 retarget_interval: int = 10):
        self.ledger = Ledger()
        self.difficulty = difficulty
        self.difficulty_manager = DifficultyManager(
            target_block_time=target_block_time,
            retarget_interval=retarget_interval,
        )
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_tx = TransactionBuilder.create_coinbase("GENESIS_ADDRESS", 1000.0)
        genesis_block = Block(
            index=0,
            previous_hash="0" * 64,
            transactions=[genesis_tx],
            difficulty=self.difficulty,
        )
        genesis_block.mine()
        self.ledger.add_block(genesis_block)

    def _next_difficulty(self) -> int:
        return self.difficulty_manager.calculate_next_difficulty(self.ledger.chain)

    def mine_pending_transactions(self, miner_address: str, transactions: list) -> Block:
        reward_tx = TransactionBuilder.create_coinbase(miner_address, 50.0)
        all_txs = [reward_tx] + transactions
        next_difficulty = self._next_difficulty()

        new_block = Block(
            index=self.ledger.latest_block.index + 1,
            previous_hash=self.ledger.latest_block.hash,
            transactions=all_txs,
            difficulty=next_difficulty,
        )
        new_block.mine()
        self.ledger.add_block(new_block)
        self.difficulty = next_difficulty
        return new_block

    def get_mining_info(self) -> dict:
        return {
            "height": self.ledger.height,
            "current_difficulty": self.ledger.latest_block.difficulty if self.ledger.chain else self.difficulty,
            "difficulty_manager": self.difficulty_manager.get_retarget_info(self.ledger.chain),
            "estimated_hashrate": self.difficulty_manager.format_hashrate(
                self.difficulty_manager.estimate_hashrate(self.ledger.chain)
            ),
        }

    def clear_chain(self):
        self.ledger = Ledger()

    def is_chain_valid(self) -> bool:
        return self.ledger.is_chain_valid()

    def __repr__(self) -> str:
        return f"Node(height={self.ledger.height}, difficulty={self.difficulty})"
