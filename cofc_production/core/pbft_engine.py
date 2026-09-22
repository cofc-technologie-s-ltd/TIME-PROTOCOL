import base64
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
