"""Tests for Difficulty Adjustment."""

import unittest
import time
from time_protocol import Node
from time_protocol.block import Block
from time_protocol.transaction import TransactionBuilder
from time_protocol.difficulty import DifficultyManager


class TestDifficultyManager(unittest.TestCase):

    def test_should_retarget(self):
        dm = DifficultyManager(retarget_interval=10)
        self.assertFalse(dm.should_retarget(5))
        self.assertFalse(dm.should_retarget(9))
        self.assertTrue(dm.should_retarget(10))
        self.assertTrue(dm.should_retarget(20))
        self.assertTrue(dm.should_retarget(30))
        self.assertFalse(dm.should_retarget(11))

    def test_calculate_first_retarget(self):
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        now = time.time()
        chain = []
        for i in range(6):
            tx = TransactionBuilder.create_coinbase(f"MINER_{i}", 50.0)
            b = Block(
                index=i,
                previous_hash="0" * 64 if i == 0 else chain[-1].hash,
                transactions=[tx],
                timestamp=now + (i * 10.0),
                difficulty=2,
            )
            chain.append(b)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertEqual(new_diff, 2)

    def test_fast_blocks_raise_difficulty(self):
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        now = time.time()
        chain = []
        for i in range(6):
            tx = TransactionBuilder.create_coinbase(f"MINER_{i}", 50.0)
            b = Block(
                index=i,
                previous_hash="0" * 64 if i == 0 else chain[-1].hash,
                transactions=[tx],
                timestamp=now + (i * 2.5),
                difficulty=2,
            )
            chain.append(b)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertGreater(new_diff, 2)
        self.assertLessEqual(new_diff, dm.MAX_DIFFICULTY)

    def test_slow_blocks_lower_difficulty(self):
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        now = time.time()
        chain = []
        for i in range(6):
            tx = TransactionBuilder.create_coinbase(f"MINER_{i}", 50.0)
            b = Block(
                index=i,
                previous_hash="0" * 64 if i == 0 else chain[-1].hash,
                transactions=[tx],
                timestamp=now + (i * 40.0),
                difficulty=5,
            )
            chain.append(b)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertLess(new_diff, 5)
        self.assertGreaterEqual(new_diff, dm.MIN_DIFFICULTY)

    def test_difficulty_bounds(self):
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        now = time.time()
        chain_fast = []
        for i in range(6):
            tx = TransactionBuilder.create_coinbase("M", 50.0)
            b = Block(
                index=i,
                previous_hash="0" * 64 if i == 0 else chain_fast[-1].hash,
                transactions=[tx],
                timestamp=now + (i * 0.001),
                difficulty=dm.MAX_DIFFICULTY,
            )
            chain_fast.append(b)
        new_diff = dm.calculate_next_difficulty(chain_fast)
        self.assertLessEqual(new_diff, dm.MAX_DIFFICULTY)

    def test_retarget_info(self):
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=10)
        now = time.time()
        chain = []
        for i in range(4):
            tx = TransactionBuilder.create_coinbase("M", 50.0)
            b = Block(
                index=i,
                previous_hash="0" * 64 if i == 0 else chain[-1].hash,
                transactions=[tx],
                timestamp=now + (i * 5.0),
                difficulty=3,
            )
            chain.append(b)
        info = dm.get_retarget_info(chain)
        self.assertEqual(info["current_difficulty"], 3)
        self.assertIn("blocks_until_retarget", info)
        self.assertIn("average_block_time", info)


class TestNodeDifficulty(unittest.TestCase):

    def test_node_retargets_at_interval(self):
        node = Node(difficulty=2, target_block_time=0.001, retarget_interval=5)
        for i in range(5):
            node.mine_pending_transactions("MINER", [])
        block = node.mine_pending_transactions("MINER", [])
        self.assertGreaterEqual(block.difficulty, 2)
        self.assertTrue(node.ledger.is_chain_valid())

    def test_node_mining_info(self):
        node = Node(difficulty=2)
        node.mine_pending_transactions("MINER", [])
        info = node.get_mining_info()
        self.assertIn("height", info)
        self.assertIn("current_difficulty", info)
        self.assertIn("difficulty_manager", info)
        self.assertIn("estimated_hashrate", info)

    def test_chain_valid_after_retarget(self):
        node = Node(difficulty=1, target_block_time=0.01, retarget_interval=5)
        for i in range(16):
            node.mine_pending_transactions("MINER", [])
        self.assertTrue(node.ledger.is_chain_valid())
        self.assertGreater(node.ledger.height, 10)


if __name__ == '__main__':
    unittest.main()
