"""
TIME Protocol - Multi-Signature Wallets
M-of-N signature schemes for shared control.
"""

import hashlib
from .crypto import KeyPair


class MultiSigError(Exception):
    pass


class MultiSigInput:
    """Fake input structure to match Transaction API."""
    
    def __init__(self, pubkey: str, signature: str, txid: str = "MULTISIG"):
        self.pubkey = pubkey
        self.signature = signature
        self.txid = txid
        self.output_index = 0
    
    def to_dict(self):
        return {
            "txid": self.txid,
            "output_index": self.output_index,
            "pubkey": self.pubkey,
            "signature": self.signature,
        }


class MultiSigOutput:
    """Fake output structure to match Transaction API."""
    
    def __init__(self, amount: float, recipient_address: str):
        self.amount = amount
        self.recipient_address = recipient_address
    
    def to_dict(self):
        return {
            "amount": self.amount,
            "recipient_address": self.recipient_address,
        }


class MultiSigTransaction:
    """
    A multisig transaction with all signatures attached.
    Mimics the Transaction API for compatibility.
    """
    
    def __init__(self, txid, recipient, amount, required, total, signatures, public_keys, fee=0.0):
        self.txid = txid
        self.recipient = recipient
        self.amount = amount
        self.required = required
        self.total = total
        self.signatures = signatures
        self.public_keys = public_keys
        self.fee = fee
        
        # Build inputs list to match Transaction API
        # First input has the multisig metadata
        multisig_meta = f"multisig:{required}|{','.join(public_keys)}|{','.join(signatures)}"
        self.inputs = [
            MultiSigInput(
                pubkey=multisig_meta,
                signature=signatures[0] if signatures else "",
            )
        ]
        
        # Build outputs list
        self.outputs = [
            MultiSigOutput(amount=amount, recipient_address=recipient)
        ]
    
    def to_dict(self):
        return {
            "txid": self.txid,
            "recipient": self.recipient,
            "amount": self.amount,
            "required": self.required,
            "total": self.total,
            "signatures": self.signatures,
            "public_keys": self.public_keys,
            "fee": self.fee,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
        }


class MultiSigWallet:
    """
    M-of-N Multi-Signature Wallet.
    
    Usage:
        wallet = MultiSigWallet(required=2, keypairs=[kp1, kp2, kp3])
        tx = wallet.create_transaction("RECIPIENT", 10.0)
    """
    
    def __init__(self, required: int, keypairs: list):
        if required < 1:
            raise MultiSigError("Required signatures must be >= 1")
        if required > len(keypairs):
            raise MultiSigError(f"Required ({required}) > Total keys ({len(keypairs)})")
        
        self.required = required
        self.keypairs = keypairs
        self.total = len(keypairs)
        self.address = self._compute_address()
    
    def _compute_address(self) -> str:
        pub_keys = sorted(kp.public_key.to_string().hex() for kp in self.keypairs)
        combined = f"{self.required}-of-{self.total}:" + ":".join(pub_keys)
        addr_hash = hashlib.sha256(combined.encode()).hexdigest()
        return "MULTI" + addr_hash[:40]
    
    def create_transaction(self, recipient: str, amount: float, ledger=None, fee: float = 0.0):
        """Create a multisig transaction with all signatures."""
        txid_data = f"{self.address}:{recipient}:{amount}:{fee}"
        txid = hashlib.sha256(txid_data.encode()).hexdigest()
        
        signatures = []
        public_keys = []
        for kp in self.keypairs:
            sig = kp.sign(txid)
            signatures.append(sig)
            public_keys.append(kp.public_key.to_string().hex())
        
        return MultiSigTransaction(
            txid=txid,
            recipient=recipient,
            amount=amount,
            required=self.required,
            total=self.total,
            signatures=signatures,
            public_keys=public_keys,
            fee=fee,
        )
    
    def to_dict(self):
        return {
            "address": self.address,
            "required": self.required,
            "total": self.total,
            "public_keys": [kp.public_key.to_string().hex() for kp in self.keypairs],
        }


def create_2_of_3(keypairs=None) -> MultiSigWallet:
    """Create a 2-of-3 multisig wallet."""
    if keypairs is None:
        keypairs = [KeyPair() for _ in range(3)]
    return MultiSigWallet(required=2, keypairs=keypairs)


def create_3_of_5(keypairs=None) -> MultiSigWallet:
    """Create a 3-of-5 multisig wallet."""
    if keypairs is None:
        keypairs = [KeyPair() for _ in range(5)]
    return MultiSigWallet(required=3, keypairs=keypairs)
