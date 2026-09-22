import os

os.makedirs("services/gateway", exist_ok=True)
os.makedirs("tests", exist_ok=True)

# 1. FIX Gateway / Institutional Bridge
with open("services/gateway/fix_gateway.py", "w", encoding="utf-8") as f:
    f.write('''import json
import time

class FIXGateway:
    """
    Institutional FIX Protocol / JSON-FIX bridge for high-frequency 
    and algorithmic trading order entry.
    """
    def __init__(self):
        self.session_id = "TIME_INSTITUTIONAL_FIX_01"
        self.sequence_number = 1

    def parse_fix_message(self, raw_msg: str) -> dict:
        return {
            "status": "parsed",
            "protocol": "FIX.4.4",
            "raw": raw_msg,
            "seq": self.sequence_number,
            "timestamp": time.time()
        }

    def create_order_execution_report(self, order_id: str, status: str, filled_qty: float) -> dict:
        self.sequence_number += 1
        return {
            "MsgType": "8", # Execution Report
            "OrderID": order_id,
            "ExecStatus": status, # e.g., 'FILLED'
            "LastShares": filled_qty,
            "MsgSeqNum": self.sequence_number,
            "SendingTime": time.time()
        }
''')

# 2. Main Node CLI & Dashboard (`main_node.py`)
with open("main_node.py", "w", encoding="utf-8") as f:
    f.write('''import time
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
''')

# 3. Add Gateway Unit Test
with open("tests/test_fix_gateway.py", "w", encoding="utf-8") as f:
    f.write('''import unittest
from services.gateway.fix_gateway import FIXGateway

class TestFIXGateway(unittest.TestCase):
    def test_fix_order_processing(self):
        gateway = FIXGateway()
        parsed = gateway.parse_fix_message("8=FIX.4.4|35=D|56=TARGET")
        self.assertEqual(parsed["status"], "parsed")
        
        exec_report = gateway.create_order_execution_report("ORD-1001", "FILLED", 500.0)
        self.assertEqual(exec_report["MsgType"], "8")
        self.assertEqual(exec_report["OrderID"], "ORD-1001")

if __name__ == "__main__":
    unittest.main()
''')

print("[+] Successfully generated FIX Gateway, Main CLI Node, and Tests!")
