from time_crypto import PostQuantumSigner

class CashProtocolAdapter:
    """
    Interoperability adapter linking CASH Protocol zero-fee monetary tokens 
    with TIME Protocol's post-quantum $O(1)$ consensus layer.
    """
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def wrap_cash_transfer(self, sender: str, recipient: str, cash_amount: int, nonce: int) -> dict:
        payload = {
            "protocol": "CASH_PROTOCOL_V1",
            "sender": sender,
            "recipient": recipient,
            "amount": cash_amount,
            "nonce": nonce
        }
        signature = PostQuantumSigner.sign_payload(payload, self.secret_key)
        return {
            "payload": payload,
            "signature": signature
        }

    def verify_cash_transfer(self, wrapped_packet: dict) -> bool:
        payload = wrapped_packet.get("payload", {})
        signature = wrapped_packet.get("signature", "")
        return PostQuantumSigner.verify_payload(payload, signature, self.secret_key)
