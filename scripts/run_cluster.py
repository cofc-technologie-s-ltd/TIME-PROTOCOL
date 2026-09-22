import os
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
