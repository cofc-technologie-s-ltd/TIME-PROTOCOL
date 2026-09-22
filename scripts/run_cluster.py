import os
import time
from network.p2p.tcp_node import RealP2PNode
from core.ledger.state_trie import RealStateLedger
from cryptography.hazmat.primitives.asymmetric import ed25519

def main():
    node_id = os.environ.get("NODE_ID", "1")
    port = int(os.environ.get("NODE_PORT", 9091))
    
    print(f"[+] Starting TIME-PROTOCOL Production Node #{node_id} on port {port}...")
    ledger = RealStateLedger()
    priv_key = ed25519.Ed25519PrivateKey.generate()
    
    node = RealP2PNode("0.0.0.0", port)
    node.start()
    print(f"[+] Node #{node_id} is running and listening for P2P/TCP traffic.")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        node.stop()
        print(f"[-] Node #{node_id} stopped gracefully.")

if __name__ == "__main__":
    main()
