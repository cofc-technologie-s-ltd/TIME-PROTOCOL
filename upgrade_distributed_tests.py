import os

os.makedirs("tests", exist_ok=True)

# 1. Distributed Core Unit Tests (tests/test_distributed_core.py)
with open("tests/test_distributed_core.py", "w", encoding="utf-8") as f:
    f.write('''import unittest
from core.p2p.kademlia_dht import KademliaNode
from core.consensus.pbft_engine import PBFTConsensusEngine
from cryptography.hazmat.primitives.asymmetric import ed25519

class TestDistributedCore(unittest.TestCase):
    def test_kademlia_dht_routing_and_storage(self):
        node = KademliaNode("127.0.0.1", 9000, node_id="0000000000000000000000000000000000000001")
        
        # Add peers
        node.add_peer("0000000000000000000000000000000000000002", "127.0.0.1", 9001)
        node.add_peer("ffffffffffffffffffffffffffffffffffffffff", "127.0.0.1", 9002)
        
        # Test closest nodes lookup
        closest = node.find_closest_nodes(int("0000000000000000000000000000000000000003", 16), count=1)
        self.assertEqual(len(closest), 1)
        self.assertEqual(closest[0][2], 9001)  # Closer peer port
        
        # Test DHT key-value storage
        node.store_value("test_key", "test_value")
        self.assertEqual(node.get_value("test_key"), "test_value")
        self.assertIsNone(node.get_value("non_existent"))

    def test_pbft_consensus_flow(self):
        priv_key_1 = ed25519.Ed25519PrivateKey.generate()
        priv_key_2 = ed25519.Ed25519PrivateKey.generate()
        
        engine1 = PBFTConsensusEngine("node1", priv_key_1, {"val1": 1.0, "val2": 1.0})
        engine2 = PBFTConsensusEngine("node2", priv_key_2, {"val1": 1.0, "val2": 1.0})
        
        pub1 = engine1.get_public_key_hex()
        pub2 = engine2.get_public_key_hex()
        
        # Re-initialize with correct public keys in validator set
        engine1.validators = {pub1: 1.0, pub2: 1.0}
        engine2.validators = {pub1: 1.0, pub2: 1.0}
        
        # Phase 1: Pre-Prepare
        block = {"index": 1, "data": "tx_batch_1"}
        pre_prepare_msg = engine1.create_pre_prepare(block)
        
        # Phase 2: Prepare
        prepare_sig = engine2.sign_message(pre_prepare_msg)
        quorum_reached = engine1.process_prepare(pub2, pre_prepare_msg, prepare_sig)
        
        # With 2 validators, f=0, required quorum = (2*2)/3 + 1 = 1 (or based on formula: (2*2)//3 + 1 = 2? Wait: total=2, 2*2=4, //3 = 1, +1 = 2). 
        # Let's verify quorum behavior: total=2 -> required_quorum = ((2*2)//3) + 1 = 2. 
        # Node 1 itself needs to also process prepare to reach quorum of 2.
        self.assertFalse(quorum_reached) # Only 1 vote so far (node2)
        
        self_prepare_sig = engine1.sign_message(pre_prepare_msg)
        quorum_reached = engine1.process_prepare(pub1, pre_prepare_msg, self_prepare_sig)
        self.assertTrue(quorum_reached) # Now 2 votes (node1 + node2) -> Quorum met!

if __name__ == "__main__":
    unittest.main()
''')

# 2. Updated Cluster Runner using Kademlia & PBFT
with open("scripts/run_cluster.py", "w", encoding="utf-8") as f:
    f.write('''import os
import time
from core.p2p.kademlia_dht import KademliaNode
from core.consensus.pbft_engine import PBFTConsensusEngine
from cryptography.hazmat.primitives.asymmetric import ed25519

def main():
    node_id = os.environ.get("NODE_ID", "1")
    port = int(os.environ.get("NODE_PORT", 9091))
    
    print(f"[+] Initializing Distributed TIME-PROTOCOL Node #{node_id} on port {port}...")
    
    # Initialize Kademlia DHT and PBFT Engine
    dht_node = KademliaNode("0.0.0.0", port)
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_hex = priv_key.public_key().public_bytes(
        encoding=ed25519.serialization.Encoding.Raw,
        format=ed25519.serialization.PublicFormat.Raw
    ).hex() if hasattr(ed25519, 'serialization') else ""
    
    pbft = PBFTConsensusEngine(f"node_{node_id}", priv_key, {})
    
    print(f"[+] Node #{node_id} active. DHT ID: {hex(dht_node.node_id)}")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print(f"[-] Distributed Node #{node_id} shut down gracefully.")

if __name__ == "__main__":
    main()
''')

print("[+] Successfully added distributed core tests and cluster integration!")
