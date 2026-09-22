import unittest
import urllib.request
import json
from core.ledger.state_trie import StateLedger
from network.p2p.gossip import P2PGossipNetwork
from services.api.node_api import NodeAPIServer

class MockNode:
    def __init__(self):
        self.ledger = StateLedger()
        self.network = P2PGossipNetwork("node_alpha", 8080)
        self.is_mining = False

class TestV3FullIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = MockNode()
        cls.api_server = NodeAPIServer(cls.node, port=8999)
        cls.api_server.start()

    @classmethod
    def tearDownClass(cls):
        cls.api_server.stop()

    def test_ledger_state_and_root(self):
        ledger = StateLedger()
        ledger.set_balance("alice", 500.0)
        self.assertEqual(ledger.get_balance("alice"), 500.0)
        root1 = ledger.get_state_root()
        self.assertNotEqual(root1, "")

    def test_p2p_gossip_network(self):
        net = P2PGossipNetwork("node_1", 9000)
        added = net.add_peer("127.0.0.1", 9001)
        self.assertTrue(added)
        stats = net.get_stats()
        self.assertEqual(stats["peers_count"], 1)

    def test_rest_api_endpoints(self):
        # Test Status
        req = urllib.request.urlopen("http://127.0.0.1:8999/api/status")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["status"], "ok")

        # Test Mine
        req_mine = urllib.request.Request(
            "http://127.0.0.1:8999/api/mine",
            data=json.dumps({"miner": "test"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        res_mine = urllib.request.urlopen(req_mine)
        mine_data = json.loads(res_mine.read().decode('utf-8'))
        self.assertTrue(mine_data["mined"])

if __name__ == "__main__":
    unittest.main()
