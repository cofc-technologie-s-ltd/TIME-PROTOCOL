"""
Tests for SQLite persistence layer.
Verifies save/load/restore of blockchain state.
"""

import unittest
import os
import tempfile
import time
from time_protocol import Node, Wallet
from time_protocol.storage import Storage, PersistentNode


class TestStorage(unittest.TestCase):
    
    def setUp(self):
        # Use temp DB for each test
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.tmp.close()
        self.db_path = self.tmp.name
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_save_and_load_empty(self):
        """Storage should handle empty state gracefully."""
        storage = Storage(self.db_path)
        self.assertEqual(storage.get_block_count(), 0)
        self.assertEqual(storage.get_latest_block_index(), -1)
        
        chain = storage.load_chain()
        self.assertEqual(chain, [])
    
    def test_save_and_load_chain(self):
        """Save a chain to disk and load it back."""
        node = Node(difficulty=1)
        node.mine_pending_transactions("MINER_A", [])
        node.mine_pending_transactions("MINER_B", [])
        
        original_height = node.ledger.height
        original_hash = node.ledger.latest_block.hash
        
        # Save
        storage = Storage(self.db_path)
        storage.save_chain(node.ledger.chain)
        
        self.assertEqual(storage.get_block_count(), 3)  # genesis + 2
        self.assertEqual(storage.get_latest_block_index(), 2)
        
        # Load into a new node
        loaded_blocks = storage.load_chain()
        new_node = Node(difficulty=1)
        new_node.clear_chain()
        for block in loaded_blocks:
            new_node.ledger.add_block(block)
        
        # Compare
        self.assertEqual(new_node.ledger.height, len(new_node.ledger.chain) - 1)
        self.assertEqual(new_node.ledger.latest_block.hash, original_hash)
        self.assertGreaterEqual(len(new_node.ledger.chain), 1)
    
    def test_persistent_node_save_load(self):
        """PersistentNode should save and restore the full state."""
        # Create node with activity
        node1 = Node(difficulty=1)
        pnode1 = PersistentNode(node1, self.db_path)
        
        alice = Wallet()
        node1.mine_pending_transactions(alice.address, [])
        tx = alice.create_transaction(
            recipient="RECIPIENT_ADDRESS",
            amount=10.0,
            ledger=node1.ledger,
            fee=0.0
        )
        node1.mine_pending_transactions(alice.address, [tx])
        
        original_balance = node1.ledger.get_balance(alice.address)
        original_height = node1.ledger.height
        
        # Save
        pnode1.save()
        
        # New node - load from disk
        node2 = Node(difficulty=1)
        pnode2 = PersistentNode(node2, self.db_path)
        loaded = pnode2.load()
        
        self.assertTrue(loaded)
        self.assertEqual(node2.ledger.height, original_height)
        self.assertEqual(node2.ledger.get_balance(alice.address), original_balance)
        self.assertTrue(node2.ledger.is_chain_valid())
    
    def test_persistent_node_load_empty(self):
        """Loading from an empty DB should return False."""
        node = Node(difficulty=1)
        pnode = PersistentNode(node, self.db_path)
        loaded = pnode.load()
        self.assertFalse(loaded)
    
    def test_export_import_json(self):
        """Export chain to JSON and re-import."""
        node = Node(difficulty=1)
        node.mine_pending_transactions("TEST_MINER", [])
        
        storage = Storage(self.db_path)
        storage.save_chain(node.ledger.chain)
        
        # Export
        json_path = self.db_path + ".json"
        try:
            storage.export_json(json_path)
            self.assertTrue(os.path.exists(json_path))
            
            # Clear and re-import
            storage.clear()
            self.assertEqual(storage.get_block_count(), 0)
            
            count = storage.import_json(json_path)
            self.assertEqual(count, 2)  # genesis + 1
            self.assertEqual(storage.get_block_count(), 2)
        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)
    
    def test_storage_stats(self):
        """Stats should return valid info."""
        node = Node(difficulty=1)
        node.mine_pending_transactions("MINER", [])
        
        storage = Storage(self.db_path)
        storage.save_chain(node.ledger.chain)
        
        stats = storage.stats()
        self.assertEqual(stats["block_count"], 2)
        self.assertEqual(stats["max_index"], 1)
        self.assertGreater(stats["db_size_bytes"], 0)


if __name__ == '__main__':
    unittest.main()
