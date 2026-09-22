import unittest
import json
import urllib.request
import threading
from time_protocol.node import Node
from time_protocol.rpc_server import run_production_server

class TestProductionSovereignLedger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.node = Node(difficulty=1)
        cls.server = run_production_server(cls.node, "127.0.0.1", 9999)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_genesis_and_chain(self):
        req = urllib.request.urlopen("http://127.0.0.1:9999/api/v1/chain")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["status"], "ONLINE")
        self.assertEqual(data["length"], 1)

    def test_master_vault_balance(self):
        req = urllib.request.urlopen("http://127.0.0.1:9999/api/v1/balance/SOVEREIGN_MASTER_VAULT")
        data = json.loads(req.read().decode('utf-8'))
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["balance"], 3000000000.0)

    def test_block_mining(self):
        req = urllib.request.Request(
            "http://127.0.0.1:9999/api/v1/mine",
            data=json.dumps({"miner_address": "VALIDATOR_NODE_01"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            self.assertEqual(data["status"], "SUCCESS")
            self.assertEqual(data["mined_block"]["index"], 1)

if __name__ == '__main__':
    unittest.main()
