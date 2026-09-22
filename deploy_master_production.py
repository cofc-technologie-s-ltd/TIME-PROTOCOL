import os
import unittest
import sys

# 1. Create directory hierarchy
dirs = [
    "cofc_production/core",
    "cofc_production/network",
    "cofc_production/services/gateway",
    "cofc_production/services/iso20022",
    "cofc_production/tests"
]
for d in dirs:
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "__init__.py"), "w", encoding="utf-8") as f:
        f.write("# COFC Production Package\n")

with open("cofc_production/__init__.py", "w", encoding="utf-8") as f:
    f.write("# COFC Production Root\n")

# 2. State Ledger
with open("cofc_production/core/state_ledger.py", "w", encoding="utf-8") as f:
    f.write('''import hashlib
import json

class ProductionStateLedger:
    def __init__(self):
        self.accounts = {}
        self.latest_block_index = 0

    def get_balance(self, pub_key: str) -> float:
        return self.accounts.get(pub_key, {}).get("balance", 0.0)

    def set_balance(self, pub_key: str, balance: float):
        if pub_key not in self.accounts:
            self.accounts[pub_key] = {"balance": 0.0, "nonce": 0}
        self.accounts[pub_key]["balance"] = balance

    def apply_transaction(self, sender: str, recipient: str, amount: float, signature: str) -> bool:
        if amount <= 0:
            return False
        sender_bal = self.get_balance(sender)
        if sender_bal < amount:
            return False
        self.set_balance(sender, sender_bal - amount)
        self.set_balance(recipient, self.get_balance(recipient) + amount)
        self.accounts[sender]["nonce"] += 1
        self.latest_block_index += 1
        return True

    def get_state_root(self) -> str:
        state_str = json.dumps(self.accounts, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()
''')

# 3. Kademlia DHT
with open("cofc_production/network/kademlia_dht.py", "w", encoding="utf-8") as f:
    f.write('''import hashlib
import random

class ProductionKademliaDHT:
    def __init__(self, host: str, port: int, node_id: str = None):
        self.host = host
        self.port = port
        if not node_id:
            raw_id = f"{host}:{port}:{random.random()}"
            self.node_id = int(hashlib.sha1(raw_id.encode()).hexdigest(), 16)
        else:
            self.node_id = int(node_id, 16) if isinstance(node_id, str) else node_id
        self.routing_table = {}
        self.storage = {}

    def xor_distance(self, id1: int, id2: int) -> int:
        return id1 ^ id2

    def add_peer(self, peer_id: str, host: str, port: int):
        pid = int(peer_id, 16) if isinstance(peer_id, str) else peer_id
        if pid == self.node_id:
            return
        dist = self.xor_distance(self.node_id, pid)
        bucket_idx = max(0, dist.bit_length() - 1)
        if bucket_idx not in self.routing_table:
            self.routing_table[bucket_idx] = []
        existing = [p for p in self.routing_table[bucket_idx] if p[0] == pid]
        if not existing:
            if len(self.routing_table[bucket_idx]) >= 20:
                self.routing_table[bucket_idx].pop(0)
            self.routing_table[bucket_idx].append((pid, host, port))

    def find_closest_nodes(self, target_id: int, count: int = 3):
        all_peers = []
        for bucket in self.routing_table.values():
            all_peers.extend(bucket)
        all_peers.sort(key=lambda p: self.xor_distance(p[0], target_id))
        return all_peers[:count]

    def store_value(self, key: str, value: str):
        self.storage[key] = value

    def get_value(self, key: str):
        return self.storage.get(key, None)
''')

# 4. PBFT Engine
with open("cofc_production/core/pbft_engine.py", "w", encoding="utf-8") as f:
    f.write('''import base64
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class ProductionPBFT:
    def __init__(self, node_id: str, private_key: ed25519.Ed25519PrivateKey, validator_set: dict):
        self.node_id = node_id
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self.validators = validator_set
        self.view = 0
        self.sequence = 0
        self.prepare_votes = {}
        self.commit_votes = {}

    def get_public_key_hex(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()

    def sign_message(self, message: dict) -> str:
        msg_bytes = json.dumps(message, sort_keys=True).encode('utf-8')
        sig = self.private_key.sign(msg_bytes)
        return base64.b64encode(sig).decode('utf-8')

    def verify_signature(self, pub_key_hex: str, message: dict, signature_b64: str) -> bool:
        try:
            pub_bytes = bytes.fromhex(pub_key_hex)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            sig_bytes = base64.b64decode(signature_b64)
            msg_bytes = json.dumps(message, sort_keys=True).encode('utf-8')
            pub_key.verify(sig_bytes, msg_bytes)
            return True
        except Exception:
            return False

    def create_pre_prepare(self, block_data: dict) -> dict:
        self.sequence += 1
        msg = {
            "type": "PRE-PREPARE",
            "view": self.view,
            "sequence": self.sequence,
            "block": block_data,
            "node_id": self.node_id
        }
        msg["signature"] = self.sign_message(msg)
        return msg

    def process_prepare(self, pub_key_hex: str, message: dict, signature: str) -> bool:
        if not self.verify_signature(pub_key_hex, message, signature):
            return False
        seq = message.get("sequence")
        if seq not in self.prepare_votes:
            self.prepare_votes[seq] = set()
        self.prepare_votes[seq].add(pub_key_hex)
        total = len(self.validators)
        quorum = ((total * 2) // 3) + 1 if total > 0 else 1
        return len(self.prepare_votes[seq]) >= quorum
''')

# 5. TCP Node Server
with open("cofc_production/network/node_server.py", "w", encoding="utf-8") as f:
    f.write('''import socket
import threading
import json

class ProductionNodeServer:
    def __init__(self, host: str, port: int, dht_node, pbft_engine):
        self.host = host
        self.port = port
        self.dht_node = dht_node
        self.pbft_engine = pbft_engine
        self.server_socket = None
        self.is_running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(15)
        self.is_running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                conn, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            data = conn.recv(8192)
            if not data:
                return
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get("type")
            resp = {"status": "error", "reason": "unknown"}

            if msg_type == "PING":
                resp = {"status": "pong", "node_id": str(self.dht_node.node_id)}
            elif msg_type == "DHT_STORE":
                self.dht_node.store_value(message["key"], message["value"])
                resp = {"status": "stored"}
            elif msg_type == "DHT_FIND":
                val = self.dht_node.get_value(message["key"])
                resp = {"status": "found", "value": val}
            elif msg_type == "PBFT_PRE_PREPARE":
                resp = {"status": "acknowledged"}

            conn.sendall(json.dumps(resp).encode('utf-8'))
        except Exception as e:
            try:
                conn.sendall(json.dumps({"status": "error", "details": str(e)}).encode('utf-8'))
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

# 6. FIX Gateway
with open("cofc_production/services/gateway/fix_gateway.py", "w", encoding="utf-8") as f:
    f.write('''import time

class ProductionFIXGateway:
    def __init__(self):
        self.session_id = "COFC_FIX_PRODUCTION"
        self.seq_num = 1

    def parse_order(self, raw: str) -> dict:
        return {"status": "parsed", "protocol": "FIX.4.4", "raw": raw, "seq": self.seq_num, "time": time.time()}

    def execution_report(self, order_id: str, qty: float) -> dict:
        self.seq_num += 1
        return {"MsgType": "8", "OrderID": order_id, "Status": "FILLED", "Qty": qty, "Seq": self.seq_num}
''')

# 7. ISO 20022 Gateway
with open("cofc_production/services/iso20022/iso_gateway.py", "w", encoding="utf-8") as f:
    f.write('''import xml.etree.ElementTree as ET
import uuid
import time

class ProductionISOGateway:
    def __init__(self, bic: str):
        self.bic = bic

    def generate_pacs_008(self, debtor: str, creditor: str, amount: float, ccy: str = "USD") -> str:
        root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10")
        fi = ET.SubElement(root, "FIToFIPmtStsRpt")
        hdr = ET.SubElement(fi, "GrpHdr")
        ET.SubElement(hdr, "MsgId").text = str(uuid.uuid4())
        ET.SubElement(hdr, "CreDtTm").text = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        tx = ET.SubElement(fi, "TxInfAndSts")
        amt = ET.SubElement(tx, "IntrBkSttlmAmt", Ccy=ccy)
        amt.text = f"{amount:.2f}"
        dbtr = ET.SubElement(tx, "Dbtr")
        ET.SubElement(dbtr, "Name").text = debtor
        cdtr = ET.SubElement(tx, "Cdtr")
        ET.SubElement(cdtr, "Name").text = creditor
        return ET.tostring(root, encoding='utf-8').decode('utf-8')
''')

# 8. Test Suite
with open("cofc_production/tests/test_production_suite.py", "w", encoding="utf-8") as f:
    f.write('''import unittest
import socket
import json
import time
from cofc_production.core.state_ledger import ProductionStateLedger
from cofc_production.network.kademlia_dht import ProductionKademliaDHT
from cofc_production.core.pbft_engine import ProductionPBFT
from cofc_production.network.node_server import ProductionNodeServer
from cofc_production.services.gateway.fix_gateway import ProductionFIXGateway
from cofc_production.services.iso20022.iso_gateway import ProductionISOGateway
from cryptography.hazmat.primitives.asymmetric import ed25519

class TestProductionSuite(unittest.TestCase):
    def test_ledger_transfers(self):
        ledger = ProductionStateLedger()
        a, b = "alice_pub", "bob_pub"
        ledger.set_balance(a, 5000.0)
        success = ledger.apply_transaction(a, b, 1200.0, "sig")
        self.assertTrue(success)
        self.assertEqual(ledger.get_balance(a), 3800.0)
        self.assertEqual(ledger.get_balance(b), 1200.0)
        self.assertNotEqual(ledger.get_state_root(), "")

    def test_kademlia_routing(self):
        dht = ProductionKademliaDHT("127.0.0.1", 9300, node_id="1"*40)
        dht.add_peer("2"*40, "127.0.0.1", 9301)
        dht.store_value("asset", "gold_vault")
        self.assertEqual(dht.get_value("asset"), "gold_vault")

    def test_pbft_consensus(self):
        priv = ed25519.Ed25519PrivateKey.generate()
        pbft = ProductionPBFT("node1", priv, {})
        pub = pbft.get_public_key_hex()
        pbft.validators = {pub: 1.0}
        msg = pbft.create_pre_prepare({"index": 1})
        sig = pbft.sign_message(msg)
        quorum = pbft.process_prepare(pub, msg, sig)
        self.assertTrue(quorum)

    def test_tcp_network_server(self):
        port = 9350
        dht = ProductionKademliaDHT("127.0.0.1", port)
        priv = ed25519.Ed25519PrivateKey.generate()
        pbft = ProductionPBFT("node_net", priv, {})
        server = ProductionNodeServer("127.0.0.1", port, dht, pbft)
        server.start()
        time.sleep(0.2)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", port))
        s.sendall(json.dumps({"type": "PING"}).encode('utf-8'))
        resp = json.loads(s.recv(4096).decode('utf-8'))
        s.close()
        server.stop()
        self.assertEqual(resp.get("status"), "pong")

    def test_gateways(self):
        fix = ProductionFIXGateway()
        report = fix.execution_report("ORD-999", 100.0)
        self.assertEqual(report["Status"], "FILLED")

        iso = ProductionISOGateway("COFCIL01XXX")
        xml = iso.generate_pacs_008("Aleksey", "Treasury", 50000.00)
        self.assertIn("pacs.008.001.10", xml)
        self.assertIn("50000.00", xml)

if __name__ == "__main__":
    unittest.main()
''')

print("[+] Successfully generated cofc_production module and test suite!")
