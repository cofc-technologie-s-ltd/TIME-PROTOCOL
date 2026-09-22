"""
Complete integration test suite for TIME Protocol.
Tests all modules working together.
"""

import unittest
import os
import tempfile
import time
from time_protocol import Node, Wallet, P2PNode
from time_protocol.sync import BlockSynchronizer


class TestFullIntegration(unittest.TestCase):
    
    def test_multi_node_network(self):
        """Test 3 nodes mining and syncing."""
        nodes = [Node(difficulty=2) for _ in range(3)]
        
        # Node 0 mines 2 blocks
        for i in range(2):
            nodes[0].mine_pending_transactions(f"MINER_0", [])
        self.assertEqual(nodes[0].ledger.latest_block.index, 2)
        
        # Node 2 is empty, syncs from node 0
        p2p_source = P2PNode("127.0.0.1", 7200, nodes[0])
        p2p_target = P2PNode("127.0.0.1", 7201, nodes[2])
        
        p2p_source.start()
        p2p_target.start()
        
        try:
            sync = BlockSynchronizer(p2p_target, nodes[2].ledger)
            result = sync.sync_with_peer("127.0.0.1", 7200)
            
            self.assertEqual(result["status"], "SYNCED")
            self.assertEqual(nodes[2].ledger.latest_block.index, 2)
            self.assertTrue(nodes[2].ledger.is_chain_valid())
        finally:
            p2p_source.stop()
            p2p_target.stop()
    
    def test_wallet_transaction_flow(self):
        """Complete flow: mine -> send -> verify balance."""
        alice = Wallet()
        bob = Wallet()
        
        node = Node(difficulty=2)
        
        # Mine to Alice
        node.mine_pending_transactions(alice.address, [])
        alice_balance_before = alice.get_balance(node.ledger)
        self.assertGreater(alice_balance_before, 0)
        
        # Alice sends to Bob
        tx = alice.create_transaction(
            ledger=node.ledger,
            recipient=bob.address,
            amount=10.0,
            fee=1000
        )
        node.mine_pending_transactions(alice.address, [tx])
        
        bob_balance = bob.get_balance(node.ledger)
        self.assertEqual(bob_balance, 10.0)
    
    def test_chain_persistence(self):
        """Save and reload the same chain."""
        node1 = Node(difficulty=2)
        node1.mine_pending_transactions("MINER_A", [])
        node1.mine_pending_transactions("MINER_B", [])
        
        # Serialize chain
        chain_dicts = [b.to_dict() for b in node1.ledger.chain]
        
        # Deserialize into a new node
        from time_protocol import Block
        node2 = Node(difficulty=2)
        node2.ledger.chain = []
        node2.ledger.utxo_set = {}
        for block_dict in chain_dicts:
            block = Block.from_dict(block_dict)
            node2.ledger.add_block(block)
        
        self.assertEqual(
            node1.ledger.latest_block.index,
            node2.ledger.latest_block.index
        )
        self.assertEqual(
            node1.ledger.latest_block.hash,
            node2.ledger.latest_block.hash
        )
        self.assertTrue(node2.ledger.is_chain_valid())


if __name__ == '__main__':
    unittest.main()
