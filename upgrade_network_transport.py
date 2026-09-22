import os

os.makedirs("core/p2p", exist_ok=True)
os.makedirs("tests", exist_ok=True)

# 1. Real TCP Network Server for Nodes (core/p2p/node_server.py)
with open("core/p2p/node_server.py", "w", encoding="utf-8") as f:
    f.write('''import socket
import threading
import json

class DistributedNodeServer:
    """
    Real TCP network server handling incoming P2P, DHT, and PBFT consensus messages.
    """
    def __init__(self, host: str, port: int, dht_node, pbft_engine):
        self.host = host
        self.port = port
        self.dht_node = dht_node
        self.pbft_engine = pbft_engine
        self.server_socket = None
        self.is_running = False
        self._thread = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.is_running = True
        
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self):
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            data = conn.recv(4096)
            if not data:
                return
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get("type")
            
            response = {"status": "error", "reason": "unknown_message_type"}
            
            if msg_type == "PING":
                response = {"status": "pong", "node_id": str(self.dht_node.node_id)}
            elif msg_type == "DHT_STORE":
                self.dht_node.store_value(message["key"], message["value"])
                response = {"status": "stored"}
            elif msg_type == "DHT_FIND":
                val = self.dht_node.get_value(message["key"])
                response = {"status": "found", "value": val}
            elif msg_type == "PBFT_PRE_PREPARE":
                # Process pre-prepare and return acknowledgment
                response = {"status": "pre_prepare_received"}
                
            conn.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            try:
                err_resp = {"status": "error", "details": str(e)}
                conn.sendall(json.dumps(err_resp).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
''')

# 2. Network Integration Test (tests/test_network_integration.py)
with open("tests/test_network_integration.py", "w", encoding="utf-8") as f:
    f.write('''import unittest
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
''')

print("[+] Successfully added real TCP network server and integration tests!")
