import hashlib
import hmac
import json

class PostQuantumSigner:
    @staticmethod
    def sign_payload(payload_dict: dict, secret_key: str) -> str:
        message_bytes = json.dumps(payload_dict, sort_keys=True).encode('utf-8')
        return hmac.new(secret_key.encode('utf-8'), message_bytes, hashlib.sha3_512).hexdigest()

    @staticmethod
    def verify_payload(payload_dict: dict, signature: str, secret_key: str) -> bool:
        expected = PostQuantumSigner.sign_payload(payload_dict, secret_key)
        return hmac.compare_digest(expected, signature)
