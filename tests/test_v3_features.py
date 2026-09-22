"""Tests for v3.0 features: Web UI, Multisig, Discovery, AutoSave."""

import unittest
import os
import tempfile
import time
import threading
import urllib.request
import json
from time_protocol import (
    Node, Wallet, MultiSigWallet, create_2_of_3, create_3_of_5,
    PeerDiscovery, AutoSaveMiningService, Storage
)
from time_protocol.crypto import KeyPair


class TestMultiSig(unittest.TestCase):

    def test_create_2_of_3(self):
        wallet = create_2_of_3()
        self.assertEqual(wallet.required, 2)
        self.assertEqual(wallet.total, 3)
        self.assertTrue(wallet.address.startswith("MULTI"))

    def test_deterministic_address(self):
        kp1, kp2, kp3 = KeyPair(), KeyPair(), KeyPair()
        w1 = MultiSigWallet(2, [kp1, kp2, kp3])
        w2 = MultiSigWallet(2, [kp1, kp2, kp3])
        self.assertEqual(w1.address, w2.address)

    def test_invalid_required(self):
        with self.assertRaises(Exception):
            MultiSigWallet(4, [KeyPair(), KeyPair()])

    def test_multisig_transaction(self):
        wallet = create_2_of_3()
        node = Node(difficulty=1)
        node.difficulty_manager.MAX_DIFFICULTY = 2
        
        node.mine_pending_transactions(wallet.address, [])
        balance = node.ledger.get_balance(wallet.address)
        self.assertGreater(balance, 0)
        
        tx = wallet.create_transaction(
            recipient="RECIPIENT",
            amount=10.0,
            ledger=node.ledger,
            fee=0.0,
        )
        self.assertTrue(tx.txid)
        self.assertTrue(tx.inputs[0].pubkey.startswith("multisig:2|"))


class TestPeerDiscovery(unittest.TestCase):

    def test_add_peer(self):
        d = PeerDiscovery(own_port=9001, bootstrap_nodes=[])
        self.assertTrue(d.add_peer("1.2.3.4", 9002))
        self.assertFalse(d.add_peer("1.2.3.4", 9002))

    def test_dont_add_self(self):
        d = PeerDiscovery(own_port=9001, bootstrap_nodes=[])
        self.assertFalse(d.add_peer("127.0.0.1", 9001))

    def test_merge_peer_list(self):
        d = PeerDiscovery(own_port=9001, bootstrap_nodes=[])
        added = d.merge_peer_list([
            {"host": "1.1.1.1", "port": 9001},
            {"host": "2.2.2.2", "port": 9002},
        ])
        self.assertEqual(added, 2)
        self.assertEqual(len(d.known_peers), 2)

    def test_stats(self):
        d = PeerDiscovery(own_port=9001, bootstrap_nodes=[])
        d.add_peer("1.1.1.1", 9001)
        d.add_peer("2.2.2.2", 9002)
        stats = d.stats()
        self.assertEqual(stats["total_known"], 2)
        self.assertEqual(stats["active"], 2)


class TestAutoSaveMining(unittest.TestCase):

    def test_autosave_service(self):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        tmp.close()
        try:
            node = Node(difficulty=1, target_block_time=0.01, retarget_interval=1000)
            node.difficulty_manager.MAX_DIFFICULTY = 2
            
            storage = Storage(tmp.name)
            service = AutoSaveMiningService(node, storage=storage)
            
            service.start("TEST_MINER")
            time.sleep(1.0)
            service.stop()
            
            block_count = storage.get_block_count()
            self.assertGreater(block_count, 1)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


class TestWebAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from time_protocol import run_explorer
        cls.node = Node(difficulty=1, target_block_time=0.01, retarget_interval=100)
        cls.node.difficulty_manager.MAX_DIFFICULTY = 2
        cls.node.mine_pending_transactions("PRE_MINER", [])
        cls.node.mine_pending_transactions("PRE_MINER", [])
        
        cls.server = run_explorer(cls.node, "127.0.0.1", 8099)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        res = urllib.request.urlopen(f"http://127.0.0.1:8099{path}")
        return json.loads(res.read().decode())

    def _post(self, path, data):
        req = urllib.request.Request(
            f"http://127.0.0.1:8099{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode())

    def test_status_endpoint(self):
        data = self._get("/api/status")
        self.assertIn("height", data)
        self.assertIn("mining", data)
        self.assertGreaterEqual(data["height"], 2)

    def test_blocks_endpoint(self):
        data = self._get("/api/blocks?limit=5")
        self.assertIn("blocks", data)
        self.assertGreater(len(data["blocks"]), 0)

    def test_mining_status(self):
        data = self._get("/api/mining/status")
        self.assertIn("running", data)

    def test_start_stop_mining(self):
        start = self._post("/api/mining/start", {"miner_address": "API_TEST"})
        self.assertEqual(start["status"], "STARTED")
        time.sleep(0.5)
        
        status = self._get("/api/mining/status")
        self.assertTrue(status["running"])
        
        stop = self._post("/api/mining/stop", {})
        self.assertEqual(stop["status"], "STOPPED")

    def test_mine_one_block(self):
        result = self._post("/api/mine", {"miner_address": "ONE_SHOT"})
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("block", result)


if __name__ == '__main__':
    unittest.main()
