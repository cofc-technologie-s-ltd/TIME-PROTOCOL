import unittest
import socket
import json
import time
from core.p2p.kademlia_dht import KademliaNode
from core.consensus.pbft_engine import PBFTConsensusEngine
from core.p2p.node_server import DistributedNodeServer
from cryptography.hazmat.primitives.asymmetric import ed25519

class TestNetworkIntegration(unittest.TestCase):
    def test_tcp_node_server_communication(self):
        port = 9250
        dht = KademliaNode("127.0.0.1", port)
        priv_key = ed25519.Ed25519PrivateKey.generate()
        pbft = PBFTConsensusEngine("node_test", priv_key, {})
        
        server = DistributedNodeServer("127.0.0.1", port, dht, pbft)
        server.start()
        time.sleep(0.2) # Give server time to bind
        
        # Connect via real TCP client socket and send PING
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", port))
        client.sendall(json.dumps({"type": "PING"}).encode('utf-8'))
        
        resp_data = client.recv(4096)
        client.close()
        server.stop()
        
        response = json.loads(resp_data.decode('utf-8'))
        self.assertEqual(response.get("status"), "pong")

    def test_tcp_dht_storage_over_network(self):
        port = 9251
        dht = KademliaNode("127.0.0.1", port)
        priv_key = ed25519.Ed25519PrivateKey.generate()
        pbft = PBFTConsensusEngine("node_test2", priv_key, {})
        
        server = DistributedNodeServer("127.0.0.1", port, dht, pbft)
        server.start()
        time.sleep(0.2)
        
        # Store key via TCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", port))
        client.sendall(json.dumps({"type": "DHT_STORE", "key": "agent", "value": "Aleksey"}).encode('utf-8'))
        client.recv(4096)
        client.close()
        
        # Retrieve key via TCP
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(("127.0.0.1", port))
        client2.sendall(json.dumps({"type": "DHT_FIND", "key": "agent"}).encode('utf-8'))
        resp_data = client2.recv(4096)
        client2.close()
        server.stop()
        
        response = json.loads(resp_data.decode('utf-8'))
        self.assertEqual(response.get("status"), "found")
        self.assertEqual(response.get("value"), "Aleksey")

if __name__ == "__main__":
    unittest.main()
