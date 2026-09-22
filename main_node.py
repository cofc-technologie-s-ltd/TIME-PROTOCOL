import time
import sys
from core.ledger.state_trie import StateLedger
from network.p2p.gossip import P2PGossipNetwork
from services.api.node_api import NodeAPIServer
from services.gateway.fix_gateway import FIXGateway

class TimeProtocolNode:
    def __init__(self, port=8080):
        self.port = port
        self.ledger = StateLedger()
        self.network = P2PGossipNetwork("node_primary", port)
        self.fix_gateway = FIXGateway()
        self.api_server = NodeAPIServer(self, port=port)
        self.is_mining = False

    def start(self):
        print(f"[*] Starting TIME Protocol Production Node...")
        print(f"[*] Ledger State Root: {self.ledger.get_state_root()[:16]}...")
        self.api_server.start()
        print(f"[+] REST API & Institutional FIX Gateway active on http://127.0.0.1:{self.port}")
        print(f"[+] P2P Gossip Network initialized on port {self.port}")

    def stop(self):
        self.api_server.stop()
        print("[-] TIME Protocol Node shutdown complete.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    node = TimeProtocolNode(port=port)
    node.start()
    try:
        print("[*] Node is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.stop()
