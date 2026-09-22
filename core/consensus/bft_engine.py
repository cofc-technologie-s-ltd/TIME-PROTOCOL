from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64

class RealBFTEngine:
    """
    BFT Consensus Engine with strict Ed25519 cryptographic signature verification.
    """
    def __init__(self, validator_private_key: ed25519.Ed25519PrivateKey):
        self.private_key = validator_private_key
        self.public_key = validator_private_key.public_key()
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.authorized_validators = {
            pub_bytes.hex(): 1.0  # Full voting power
        }

    def sign_block(self, block_data: dict) -> str:
        message = str(block_data).encode('utf-8')
        signature = self.private_key.sign(message)
        return base64.b64encode(signature).decode('utf-8')

    def verify_signature(self, pub_key_hex: str, block_data: dict, signature_b64: str) -> bool:
        try:
            pub_bytes = bytes.fromhex(pub_key_hex)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            sig_bytes = base64.b64decode(signature_b64)
            message = str(block_data).encode('utf-8')
            pub_key.verify(sig_bytes, message)
            return True
        except Exception:
            return False
