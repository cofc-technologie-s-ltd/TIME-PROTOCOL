import os

# 1. Update RealStateLedger to include latest_block_index for API compatibility
with open("core/ledger/state_trie.py", "w", encoding="utf-8") as f:
    f.write('''import hashlib
import json

class RealStateLedger:
    """
    Cryptographic State Ledger utilizing full public keys (hex) as account identifiers.
    Eliminates capacity limits and modulo collisions entirely.
    """
    def __init__(self):
        # Maps public_key_hex -> account state (balance, nonce, etc.)
        self.accounts = {}
        self.latest_block_index = 0  # Compatibility attribute for API/nodes

    def get_balance(self, pub_key: str) -> float:
        return self.accounts.get(pub_key, {}).get("balance", 0.0)

    def get_nonce(self, pub_key: str) -> int:
        return self.accounts.get(pub_key, {}).get("nonce", 0)

    def set_balance(self, pub_key: str, balance: float):
        if pub_key not in self.accounts:
            self.accounts[pub_key] = {"balance": 0.0, "nonce": 0}
        self.accounts[pub_key]["balance"] = balance

    def apply_transaction(self, sender: str, recipient: str, amount: float, signature: str) -> bool:
        if amount <= 0:
            return False
        
        sender_balance = self.get_balance(sender)
        if sender_balance < amount:
            return False

        # Update balances
        self.set_balance(sender, sender_balance - amount)
        self.set_balance(recipient, self.get_balance(recipient) + amount)
        
        # Increment sender nonce & block index simulation
        self.accounts[sender]["nonce"] += 1
        self.latest_block_index += 1
        return True

    def get_state_root(self) -> str:
        state_str = json.dumps(self.accounts, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

# Backward compatibility alias for older integration tests
StateLedger = RealStateLedger
''')

# 2. Fix serialization reference in test_true_core.py
with open("tests/test_true_core.py", "w", encoding="utf-8") as f:
    f.write('''import unittest
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
''')

print("[+] Successfully patched RealStateLedger compatibility and test serialization!")
