"""Tests for Background Mining Service."""

import unittest
import time
from time_protocol import Node
from time_protocol.mining import MiningService


class TestMiningService(unittest.TestCase):

    def test_start_stop(self):
        """Service starts, mines, and stops."""
        node = Node(difficulty=1, target_block_time=0.01, retarget_interval=100)
        node.difficulty_manager.MAX_DIFFICULTY = 2  # Keep tests fast
        
        service = MiningService(node)
        self.assertFalse(service.is_running())
        
        result = service.start("TEST_MINER")
        self.assertEqual(result["status"], "STARTED")
        
        # Let it mine for a moment
        time.sleep(1.5)
        
        status = service.status()
        self.assertTrue(status["running"])
        self.assertGreater(status["blocks_mined"], 0)
        
        stop_result = service.stop()
        self.assertEqual(stop_result["status"], "STOPPED")
        self.assertFalse(service.is_running())

    def test_already_running(self):
        """Starting an already-running service returns ALREADY_RUNNING."""
        node = Node(difficulty=1, target_block_time=0.01, retarget_interval=100)
        node.difficulty_manager.MAX_DIFFICULTY = 2
        
        service = MiningService(node)
        service.start("MINER")
        time.sleep(0.2)
        
        second = service.start("MINER")
        self.assertEqual(second["status"], "ALREADY_RUNNING")
        
        service.stop()

    def test_stop_when_not_running(self):
        """Stopping a stopped service returns NOT_RUNNING."""
        node = Node(difficulty=1)
        service = MiningService(node)
        
        result = service.stop()
        self.assertEqual(result["status"], "NOT_RUNNING")

    def test_status_fields(self):
        """Status returns all expected fields."""
        node = Node(difficulty=1, target_block_time=0.01, retarget_interval=100)
        node.difficulty_manager.MAX_DIFFICULTY = 2
        
        service = MiningService(node)
        service.start("MINER")
        time.sleep(0.5)
        
        status = service.status()
        self.assertIn("running", status)
        self.assertIn("blocks_mined", status)
        self.assertIn("current_height", status)
        self.assertIn("current_difficulty", status)
        self.assertIn("last_block_time", status)
        self.assertIn("uptime", status)
        
        service.stop()

    def test_on_block_callback(self):
        """Callback fires for each mined block."""
        node = Node(difficulty=1, target_block_time=0.01, retarget_interval=100)
        node.difficulty_manager.MAX_DIFFICULTY = 2
        
        mined = []
        def callback(block):
            mined.append(block.index)
        
        service = MiningService(node, on_block_mined=callback)
        service.start("MINER")
        time.sleep(1.0)
        service.stop()
        
        self.assertGreater(len(mined), 0)


if __name__ == '__main__':
    unittest.main()
