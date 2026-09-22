import base64
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class PBFTConsensusEngine:
    """
    Practical Byzantine Fault Tolerance (PBFT) consensus engine.
    Implements Pre-Prepare, Prepare, and Commit phases with Ed25519 signatures.
    """
    def __init__(self, node_id: str, private_key: ed25519.Ed25519PrivateKey, validator_set: dict):
        self.node_id = node_id
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self.validators = validator_set  # pub_key_hex -> voting_power
        self.view = 0
        self.sequence = 0
        
        # State tracking per sequence
        self.prepare_votes = {}  # seq -> set of validator pub_keys
        self.commit_votes = {}   # seq -> set of validator pub_keys

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
        
        # Check quorum (2f + 1 where total validators = n, f = (n-1)//3)
        total_validators = len(self.validators)
        required_quorum = ((total_validators * 2) // 3) + 1
        return len(self.prepare_votes[seq]) >= required_quorum

    def process_commit(self, pub_key_hex: str, message: dict, signature: str) -> bool:
        if not self.verify_signature(pub_key_hex, message, signature):
            return False
            
        seq = message.get("sequence")
        if seq not in self.commit_votes:
            self.commit_votes[seq] = set()
        self.commit_votes[seq].add(pub_key_hex)
        
        total_validators = len(self.validators)
        required_quorum = ((total_validators * 2) // 3) + 1
        return len(self.commit_votes[seq]) >= required_quorum
