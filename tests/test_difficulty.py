"""Tests for Difficulty Adjustment."""

import unittest
import time
from time_protocol import Node
from time_protocol.block import Block
from time_protocol.transaction import TransactionBuilder
from time_protocol.difficulty import DifficultyManager


def make_chain(intervals, base_difficulty=2, start_time=None):
    """
    Helper: build a synthetic chain with specific block intervals.
    
    intervals: list of time deltas between consecutive blocks
               e.g. [10.0, 10.0, 10.0] creates 4 blocks
    """
    now = start_time or time.time()
    chain = []
    
    # Block 0 (genesis)
    tx = TransactionBuilder.create_coinbase("MINER_0", 50.0)
    b0 = Block(
        index=0,
        previous_hash="0" * 64,
        transactions=[tx],
        timestamp=now,
        difficulty=base_difficulty,
    )
    chain.append(b0)
    
    # Following blocks with the given intervals
    current_time = now
    for i, delta in enumerate(intervals, start=1):
        current_time += delta
        tx = TransactionBuilder.create_coinbase(f"MINER_{i}", 50.0)
        b = Block(
            index=i,
            previous_hash=chain[-1].hash,
            transactions=[tx],
            timestamp=current_time,
            difficulty=base_difficulty,
        )
        chain.append(b)
    
    return chain


class TestDifficultyManager(unittest.TestCase):

    def test_should_retarget(self):
        dm = DifficultyManager(retarget_interval=10)
        self.assertFalse(dm.should_retarget(5))
        self.assertFalse(dm.should_retarget(9))
        self.assertTrue(dm.should_retarget(10))
        self.assertTrue(dm.should_retarget(20))
        self.assertTrue(dm.should_retarget(30))
        self.assertFalse(dm.should_retarget(11))

    def test_calculate_first_retarget_on_target(self):
        """Chain with exact target timing → difficulty unchanged."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        # 5 blocks with intervals of 10s each → 6 blocks total, next_index=6
        # But we need index 5 to be the retarget point.
        # Actually: retarget happens when NEXT block's index % interval == 0.
        # next_index = chain[-1].index + 1
        # For next_index = 5 (retarget), chain[-1].index must be 4.
        # Build 5 blocks (0-4) with 10s intervals
        chain = make_chain([10.0] * 4, base_difficulty=2)
        # Wait - we need 5 blocks (0-4) → 4 intervals
        # Actually chain[-1].index = 4, next_index = 5 → retarget
        self.assertEqual(len(chain), 5)
        self.assertEqual(chain[-1].index, 4)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertEqual(new_diff, 2)

    def test_fast_blocks_raise_difficulty(self):
        """
        Chain that mined 5 blocks in 1/4 the expected time → difficulty should rise.
        """
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        # Build 5 blocks (0-4) with 2.5s intervals (= 4x too fast)
        chain = make_chain([2.5] * 4, base_difficulty=2)
        # actual_time = 10s, expected_time = 5 * 10 = 50s
        # ratio = 10/50 = 0.2 → clamped to 0.25
        # new_diff = 2 / 0.25 = 8
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertGreater(new_diff, 2, f"Expected > 2, got {new_diff}")
        self.assertLessEqual(new_diff, dm.MAX_DIFFICULTY)

    def test_slow_blocks_lower_difficulty(self):
        """
        Chain that mined 5 blocks in 4x the expected time → difficulty should fall.
        """
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        # Build 5 blocks (0-4) with 40s intervals (= 4x too slow)
        chain = make_chain([40.0] * 4, base_difficulty=5)
        # actual_time = 160s, expected_time = 50s
        # ratio = 160/50 = 3.2 → clamped to 4.0 (within bounds)
        # new_diff = 5 / 3.2 = 1 (int)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertLess(new_diff, 5, f"Expected < 5, got {new_diff}")
        self.assertGreaterEqual(new_diff, dm.MIN_DIFFICULTY)

    def test_difficulty_bounds(self):
        """Difficulty never goes outside [MIN, MAX]."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        
        # Extremely fast chain - difficulty shouldn't exceed MAX
        chain_fast = make_chain([0.001] * 4, base_difficulty=dm.MAX_DIFFICULTY)
        new_diff = dm.calculate_next_difficulty(chain_fast)
        self.assertLessEqual(new_diff, dm.MAX_DIFFICULTY)
        
        # Extremely slow chain - difficulty shouldn't go below MIN
        chain_slow = make_chain([10000.0] * 4, base_difficulty=1)
        new_diff = dm.calculate_next_difficulty(chain_slow)
        self.assertGreaterEqual(new_diff, dm.MIN_DIFFICULTY)

    def test_no_retarget_before_interval(self):
        """Before the retarget interval, difficulty should not change."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=10)
        # Build only 5 blocks → next_index = 5, no retarget yet
        chain = make_chain([1.0] * 4, base_difficulty=3)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertEqual(new_diff, 3)

    def test_retarget_info(self):
        """get_retarget_info should return valid data."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=10)
        chain = make_chain([5.0] * 3, base_difficulty=3)
        
        info = dm.get_retarget_info(chain)
        self.assertEqual(info["current_difficulty"], 3)
        self.assertIn("blocks_until_retarget", info)
        self.assertIn("average_block_time", info)
        self.assertGreater(info["average_block_time"], 0)
        self.assertEqual(info["target_block_time"], 10.0)
        self.assertEqual(info["retarget_interval"], 10)


class TestNodeDifficulty(unittest.TestCase):

    def test_node_retargets_at_interval(self):
        """Node should retarget automatically at the configured interval."""
        node = Node(difficulty=2, target_block_time=0.001, retarget_interval=5)
        
        # Mine 10 blocks - enough for 2 retargets
        for i in range(10):
            node.mine_pending_transactions("MINER", [])
        
        # Chain should remain valid
        self.assertTrue(node.ledger.is_chain_valid())
        
        # Difficulty should have changed at some point (given fast target)
        difficulties = [b.difficulty for b in node.ledger.chain]
        self.assertGreater(len(set(difficulties)), 1, 
                          f"Difficulty never changed: {difficulties}")

    def test_node_mining_info(self):
        """get_mining_info should return rich data."""
        node = Node(difficulty=2)
        node.mine_pending_transactions("MINER", [])
        
        info = node.get_mining_info()
        self.assertIn("height", info)
        self.assertIn("current_difficulty", info)
        self.assertIn("difficulty_manager", info)
        self.assertIn("estimated_hashrate", info)

    def test_chain_valid_after_multiple_retargets(self):
        """Chain should remain valid through multiple retargets."""
        node = Node(difficulty=1, target_block_time=0.01, retarget_interval=5)
        
        # Mine enough blocks for 3 retargets
        for i in range(16):
            node.mine_pending_transactions("MINER", [])
        
        self.assertTrue(node.ledger.is_chain_valid())
        self.assertGreater(node.ledger.height, 10)


if __name__ == '__main__':
    unittest.main()
