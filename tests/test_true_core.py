import unittest
from core.ledger.state_trie import RealStateLedger
from network.p2p.tcp_node import RealP2PNode
from core.consensus.bft_engine import RealBFTEngine
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class TestTrueCoreEngine(unittest.TestCase):
    def test_ledger_no_collisions(self):
        ledger = RealStateLedger()
        alice = "a"*64
        bob = "b"*64
        ledger.set_balance(alice, 1000.0)
        
        success = ledger.apply_transaction(alice, bob, 250.0, "dummy_sig")
        self.assertTrue(success)
        self.assertEqual(ledger.get_balance(alice), 750.0)
        self.assertEqual(ledger.get_balance(bob), 250.0)
        self.assertNotEqual(ledger.get_state_root(), "")

    def test_bft_cryptographic_verification(self):
        priv_key = ed25519.Ed25519PrivateKey.generate()
        engine = RealBFTEngine(priv_key)
        
        block = {"index": 1, "txs": 10}
        sig = engine.sign_block(block)
        
        pub_hex = priv_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()
        
        is_valid = engine.verify_signature(pub_hex, block, sig)
        self.assertTrue(is_valid)

    def test_tcp_p2p_loopback(self):
        node = RealP2PNode("127.0.0.1", 9091)
        node.start()
        
        response = node.connect_to_peer("127.0.0.1", 9091, {"type": "PING"})
        self.assertEqual(response.get("status"), "received")
        node.stop()

if __name__ == "__main__":
    unittest.main()
