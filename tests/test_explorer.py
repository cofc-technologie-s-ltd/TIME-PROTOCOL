"""Tests for the Web Explorer (updated for v3.0 dashboard)."""

import unittest
import threading
import urllib.request
import json
from time_protocol import Node, Wallet, run_explorer


class TestWebExplorer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.node = Node(difficulty=1, target_block_time=0.01, retarget_interval=100)
        cls.node.difficulty_manager.MAX_DIFFICULTY = 2
        cls.alice = Wallet()
        cls.bob = Wallet()

        cls.node.mine_pending_transactions(cls.alice.address, [])
        tx = cls.alice.create_transaction(
            recipient=cls.bob.address,
            amount=10.0,
            ledger=cls.node.ledger,
            fee=0.0
        )
        cls.node.mine_pending_transactions(cls.alice.address, [tx])

        cls.server = run_explorer(cls.node, "127.0.0.1", 8097)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_index_page(self):
        """Home page should render."""
        req = urllib.request.urlopen("http://127.0.0.1:8097/")
        html = req.read().decode('utf-8')
        # Updated: new dashboard says "TIME Protocol" not "TIME Protocol Explorer"
        self.assertIn("TIME Protocol", html)
        self.assertIn("Live Dashboard", html)
        self.assertIn("Mining Control", html)

    def test_block_page(self):
        req = urllib.request.urlopen("http://127.0.0.1:8097/block/1")
        html = req.read().decode('utf-8')
        self.assertIn("Block #1", html)
        self.assertIn("Hash", html)
        self.assertIn("Nonce", html)

    def test_address_page(self):
        req = urllib.request.urlopen(f"http://127.0.0.1:8097/address/{self.alice.address}")
        html = req.read().decode('utf-8')
        self.assertIn(self.alice.address, html)
        self.assertIn("Current Balance", html)

    def test_api_stats(self):
        req = urllib.request.urlopen("http://127.0.0.1:8097/api/stats")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["height"], 2)
        self.assertTrue(data["chain_valid"])

    def test_api_chain(self):
        req = urllib.request.urlopen("http://127.0.0.1:8097/api/chain")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["length"], 3)
        self.assertIn("chain", data)

    def test_api_balance(self):
        req = urllib.request.urlopen(f"http://127.0.0.1:8097/api/balance/{self.bob.address}")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["balance"], 10.0)

    def test_404_page(self):
        try:
            urllib.request.urlopen("http://127.0.0.1:8097/nonexistent")
            self.fail("Expected 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)


if __name__ == '__main__':
    unittest.main()
