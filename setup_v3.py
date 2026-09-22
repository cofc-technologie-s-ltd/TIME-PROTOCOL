import os

os.makedirs("core/crypto", exist_ok=True)
os.makedirs("core/consensus", exist_ok=True)
os.makedirs("tests", exist_ok=True)

# 1. Write hybrid_signer.py
with open("core/crypto/hybrid_signer.py", "w", encoding="utf-8") as f:
    f.write('''import json
import hashlib
from typing import Dict, Any
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class ProductionTransaction:
    def __init__(self, sender: str, recipient: str, amount: float, nonce: int, timestamp: float):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.nonce = nonce
        self.timestamp = timestamp
        self.txid: str = ""
        self.signature: Dict[str, Any] = {}

    def serialize_payload(self) -> bytes:
        payload = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "nonce": self.nonce,
            "timestamp": self.timestamp
        }
        return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def compute_txid(self) -> str:
        raw = self.serialize_payload()
        self.txid = hashlib.sha3_256(raw).hexdigest()
        return self.txid

class HybridCryptoEngine:
    @staticmethod
    def generate_keypair():
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return {
            "private_key": priv_bytes.hex(),
            "public_key": pub_bytes.hex(),
            "_obj_priv": private_key,
            "_obj_pub": public_key
        }

    @staticmethod
    def sign_transaction(tx: ProductionTransaction, priv_hex: str) -> Dict[str, Any]:
        priv_bytes = bytes.fromhex(priv_hex)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        
        payload_bytes = tx.serialize_payload()
        signature_bytes = private_key.sign(payload_bytes)
        
        tx.compute_txid()
        tx.signature = {
            "algorithm": "Ed25519",
            "sig": signature_bytes.hex(),
            "public_key": private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex()
        }
        return tx.signature

    @staticmethod
    def verify_transaction(tx: ProductionTransaction) -> bool:
        try:
            sig_hex = tx.signature.get("sig")
            pub_hex = tx.signature.get("public_key")
            if not sig_hex or not pub_hex:
                return False
                
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
            pub_key.verify(bytes.fromhex(sig_hex), tx.serialize_payload())
            return True
        except Exception:
            return False
''')

# 2. Write bft.py
with open("core/consensus/bft.py", "w", encoding="utf-8") as f:
    f.write('''import hashlib
from typing import List, Dict, Any

class BFTMessage:
    def __init__(self, stage: str, view: int, block_hash: str, validator_id: str, signature: str):
        self.stage = stage
        self.view = view
        self.block_hash = block_hash
        self.validator_id = validator_id
        self.signature = signature

class ProductionBFTConsensus:
    def __init__(self, validator_id: str, validators: List[str]):
        self.validator_id = validator_id
        self.validators = validators
        self.view = 0
        self.state: Dict[str, Dict[str, List[BFTMessage]]] = {}

    def threshold(self) -> int:
        n = len(self.validators)
        return (2 * n) // 3 + 1

    def create_proposal(self, block_data: Dict[str, Any]) -> str:
        raw = str(block_data).encode('utf-8')
        return hashlib.sha3_256(raw).hexdigest()

    def process_message(self, msg: BFTMessage) -> bool:
        if msg.block_hash not in self.state:
            self.state[msg.block_hash] = {"prepare": [], "precommit": [], "commit": []}
            
        stage_list = self.state[msg.block_hash][msg.stage]
        if not any(v.validator_id == msg.validator_id for v in stage_list):
            stage_list.append(msg)
            
        return len(stage_list) >= self.threshold()

    def has_consensus(self, block_hash: str, stage: str) -> bool:
        if block_hash not in self.state:
            return False
        return len(self.state[block_hash][stage]) >= self.threshold()
''')

# 3. Write test script
with open("tests/test_production_core.py", "w", encoding="utf-8") as f:
    f.write('''import unittest
import time
from core.crypto.hybrid_signer import ProductionTransaction, HybridCryptoEngine
from core.consensus.bft import ProductionBFTConsensus, BFTMessage

class TestProductionCore(unittest.TestCase):
    def test_crypto_signing_and_verification(self):
        kp = HybridCryptoEngine.generate_keypair()
        tx = ProductionTransaction(
            sender="alice",
            recipient="bob",
            amount=150.0,
            nonce=1,
            timestamp=time.time()
        )
        HybridCryptoEngine.sign_transaction(tx, kp["private_key"])
        self.assertTrue(HybridCryptoEngine.verify_transaction(tx))
        self.assertNotEqual(tx.txid, "")

    def test_bft_consensus_threshold(self):
        validators = ["node1", "node2", "node3", "node4"]
        bft = ProductionBFTConsensus("node1", validators)
        # Threshold for 4 nodes should be (2*4)//3 + 1 = 3
        self.assertEqual(bft.threshold(), 3)
        
        block_hash = bft.create_proposal({"data": "test_block"})
        
        # Add 3 precommit messages (reaches threshold)
        for v in ["node1", "node2", "node3"]:
            msg = BFTMessage("precommit", 0, block_hash, v, "sig")
            reached = bft.process_message(msg)
            
        self.assertTrue(bft.has_consensus(block_hash, "precommit"))

if __name__ == "__main__":
    unittest.main()
''')

print("[+] Successfully generated v3 core structure and tests!")
