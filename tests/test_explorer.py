"""
Tests for the Web Explorer.
Verifies all endpoints return valid responses.
"""

import unittest
import threading
import urllib.request
import json
from time_protocol import Node, Wallet, run_explorer


class TestWebExplorer(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Create node with some blocks and a transaction
        cls.node = Node(difficulty=1)
        cls.alice = Wallet()
        cls.bob = Wallet()
        
        cls.node.mine_pending_transactions(cls.alice.address, [])
        tx = cls.alice.create_transaction(
            ledger=cls.node.ledger,
            recipient=cls.bob.address,
            amount=10.0,
            fee=0.0
        )
        cls.node.mine_pending_transactions(cls.alice.address, [tx])
        
        # Start explorer on test port
        cls.server = run_explorer(cls.node, "127.0.0.1", 8090)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
    
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
    
    def test_index_page(self):
        """Home page should render and contain key elements."""
        req = urllib.request.urlopen("http://127.0.0.1:8090/")
        html = req.read().decode('utf-8')
        self.assertIn("TIME Protocol Explorer", html)
        self.assertIn("Latest Blocks", html)
        self.assertIn("VALID", html)
    
    def test_block_page(self):
        """Block page should show block details."""
        req = urllib.request.urlopen("http://127.0.0.1:8090/block/1")
        html = req.read().decode('utf-8')
        self.assertIn("Block #1", html)
        self.assertIn("Hash", html)
        self.assertIn("Nonce", html)
    
    def test_address_page(self):
        """Address page should show balance and UTXOs."""
        req = urllib.request.urlopen(f"http://127.0.0.1:8090/address/{self.alice.address}")
        html = req.read().decode('utf-8')
        self.assertIn(self.alice.address, html)
        self.assertIn("Current Balance", html)
    
    def test_api_stats(self):
        """API /api/stats should return valid JSON."""
        req = urllib.request.urlopen("http://127.0.0.1:8090/api/stats")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["height"], 2)
        self.assertTrue(data["chain_valid"])
    
    def test_api_chain(self):
        """API /api/chain should return full chain."""
        req = urllib.request.urlopen("http://127.0.0.1:8090/api/chain")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["length"], 3)  # genesis + 2 mined
        self.assertIn("chain", data)
    
    def test_api_balance(self):
        """API /api/balance/<addr> should return balance."""
        req = urllib.request.urlopen(f"http://127.0.0.1:8090/api/balance/{self.bob.address}")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["balance"], 10.0)
    
    def test_404_page(self):
        """Unknown paths should return 404."""
        try:
            urllib.request.urlopen("http://127.0.0.1:8090/nonexistent")
            self.fail("Expected 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)


if __name__ == '__main__':
    unittest.main()
