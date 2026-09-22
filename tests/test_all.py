import unittest
import json
import urllib.request
import threading
from time_protocol import Node, P2PNode, run_rpc_server

class TestP2PNetwork(unittest.TestCase):
    
    def test_p2p_node_connection(self):
        node1 = Node(difficulty=2)
        node2 = Node(difficulty=2)
        
        p2p1 = P2PNode("127.0.0.1", 6000, node1)
        p2p2 = P2PNode("127.0.0.1", 6001, node2)
        
        p2p1.start()
        p2p2.start()
        
        connected = p2p2.connect_to_peer("127.0.0.1", 6000)
        self.assertTrue(connected)
        self.assertIn(("127.0.0.1", 6000), p2p2.peers)
        
        p2p1.stop()
        p2p2.stop()


class TestRPCServer(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.node = Node(difficulty=1)
        cls.server = run_rpc_server(cls.node, "127.0.0.1", 8546)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_chain(self):
        req = urllib.request.urlopen("http://127.0.0.1:8546/chain")
        data = json.loads(req.read().decode('utf-8'))
        self.assertIn("chain", data)
        self.assertEqual(data["length"], 1)

    def test_mine_block(self):
        req = urllib.request.Request(
            "http://127.0.0.1:8546/mine",
            data=json.dumps({"miner_address": "TEST_MINER"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            self.assertEqual(data["status"], "SUCCESS")
            self.assertEqual(data["block"]["index"], 1)

if __name__ == '__main__':
    unittest.main()
