import unittest
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
