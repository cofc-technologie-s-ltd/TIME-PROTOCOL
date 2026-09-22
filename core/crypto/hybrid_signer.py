import json
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
