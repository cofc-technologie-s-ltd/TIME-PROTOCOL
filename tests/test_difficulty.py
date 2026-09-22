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
    Result: len(intervals) + 1 blocks (index 0 .. len(intervals))
    """
    now = start_time or time.time()
    chain = []
    
    # Block 0
    tx = TransactionBuilder.create_coinbase("MINER_0", 50.0)
    b0 = Block(
        index=0,
        previous_hash="0" * 64,
        transactions=[tx],
        timestamp=now,
        difficulty=base_difficulty,
    )
    chain.append(b0)
    
    # Following blocks
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
        """
        Chain with exact target timing → difficulty unchanged.
        retarget_interval = 5, need 6 blocks (indexes 0-5) so next_index=6
        Wait - retarget happens at index 5 (5 % 5 == 0).
        So we need chain[-1].index = 4, next_index = 5.
        And we need len(chain) >= retarget_interval + 1 = 6.
        But that means chain must have index 0-4, so 5 blocks.
        len(chain) = 5 < 6 → NOT ENOUGH.
        
        Actually: len(chain) must be >= 6 for retarget to work.
        So we need indexes 0-5, next_index = 6. 6 % 5 != 0 → NO retarget!
        
        Wait, this is confusing. Let me trace:
        - chain has indexes 0,1,2,3,4,5 → len = 6, chain[-1].index = 5
        - next_index = 6. 6 % 5 = 1 ≠ 0 → NO retarget.
        
        For retarget, need next_index % 5 == 0:
        - next_index = 5 → chain[-1].index = 4, len = 5. But 5 < 6 → no retarget.
        - next_index = 10 → chain[-1].index = 9, len = 10. 10 >= 6 → RETARGET.
        
        So the retarget happens at index 10 with window blocks 5-10.
        """
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        # Build 10 blocks (indexes 0-9), next_index = 10 → retarget
        chain = make_chain([10.0] * 9, base_difficulty=2)
        self.assertEqual(len(chain), 10)
        self.assertEqual(chain[-1].index, 9)
        
        # Window: chain[-(5+1):] = chain[-6:] = indexes 4-9
        # Timestamps: index 4 at t=40, index 9 at t=90 → 50s actual
        # Expected = 5 * 10 = 50s
        # ratio = 50/50 = 1.0 → new_diff = 2
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertEqual(new_diff, 2)

    def test_fast_blocks_raise_difficulty(self):
        """Chain with fast blocks → difficulty should rise."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        # 10 blocks (0-9) with 2.5s intervals → next_index=10 → retarget
        # Window indexes 4-9, timestamps 10, 12.5, 15, 17.5, 20, 22.5
        # actual = 22.5 - 10 = 12.5s, expected = 50s
        # ratio = 12.5/50 = 0.25 → clamped to 0.25
        # new_diff = 2 / 0.25 = 8 → clamped to 6
        chain = make_chain([2.5] * 9, base_difficulty=2)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertGreater(new_diff, 2, f"Expected > 2, got {new_diff}")
        self.assertLessEqual(new_diff, dm.MAX_DIFFICULTY)

    def test_slow_blocks_lower_difficulty(self):
        """Chain with slow blocks → difficulty should fall."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        # 10 blocks (0-9) with 40s intervals
        # Window indexes 4-9, timestamps 160, 200, 240, 280, 320, 360
        # actual = 360 - 160 = 200s, expected = 50s
        # ratio = 200/50 = 4.0 → within bounds
        # new_diff = 5 / 4.0 = 1 (int)
        chain = make_chain([40.0] * 9, base_difficulty=5)
        new_diff = dm.calculate_next_difficulty(chain)
        self.assertLess(new_diff, 5, f"Expected < 5, got {new_diff}")
        self.assertGreaterEqual(new_diff, dm.MIN_DIFFICULTY)

    def test_difficulty_bounds(self):
        """Difficulty never goes outside [MIN, MAX]."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=5)
        
        # Extremely fast → should clamp at MAX
        chain_fast = make_chain([0.001] * 9, base_difficulty=dm.MAX_DIFFICULTY)
        new_diff = dm.calculate_next_difficulty(chain_fast)
        self.assertLessEqual(new_diff, dm.MAX_DIFFICULTY)
        
        # Extremely slow → should clamp at MIN
        chain_slow = make_chain([10000.0] * 9, base_difficulty=1)
        new_diff = dm.calculate_next_difficulty(chain_slow)
        self.assertGreaterEqual(new_diff, dm.MIN_DIFFICULTY)

    def test_no_retarget_before_interval(self):
        """Before the retarget interval, difficulty should not change."""
        dm = DifficultyManager(target_block_time=10.0, retarget_interval=10)
        # 5 blocks (0-4), next_index = 5, 5 % 10 != 0 → no retarget
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
        # Use fast target so difficulty changes quickly, but low MAX to avoid hanging
        node = Node(difficulty=1, target_block_time=0.001, retarget_interval=5)
        
        # Mine 15 blocks to allow retargets (at indexes 10, 15)
        for i in range(15):
            node.mine_pending_transactions("MINER", [])
        
        # Chain should remain valid
        self.assertTrue(node.ledger.is_chain_valid())
        
        # Difficulty should have changed
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
        # Start with low difficulty, target very fast
        node = Node(difficulty=1, target_block_time=0.01, retarget_interval=5)
        
        # Mine 20 blocks (allows retargets at 10, 15, 20)
        for i in range(20):
            node.mine_pending_transactions("MINER", [])
        
        self.assertTrue(node.ledger.is_chain_valid())
        self.assertGreater(node.ledger.height, 10)


if __name__ == '__main__':
    unittest.main()
