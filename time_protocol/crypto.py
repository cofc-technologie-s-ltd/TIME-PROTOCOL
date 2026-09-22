"""
TIME Protocol - Cryptographic Core
Real, working cryptography using Python's hashlib and ecdsa.
"""

import hashlib
import json
import ecdsa


def hash_data(data: str) -> str:
    """SHA-256 hash of a string."""
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def double_hash(data: str) -> str:
    """SHA256(SHA256(data)) - for block hashing."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    h1 = hashlib.sha256(data).digest()
    return hashlib.sha256(h1).hexdigest()


def hash_object(obj) -> str:
    """Deterministic hash of a dictionary or object with to_dict()."""
    if hasattr(obj, 'to_dict'):
        d = obj.to_dict()
    else:
        d = obj
    return hash_data(json.dumps(d, sort_keys=True, default=str))


class KeyPair:
    """
    ECDSA key pair on SECP256k1 curve (same as Bitcoin/Ethereum).
    Real, working implementation.
    """
    
    def __init__(self, private_key=None):
        """
        Create a KeyPair.
        
        Args:
            private_key: Can be:
                - None: generate new random key
                - ecdsa.SigningKey: use it directly
                - bytes: raw private key bytes (32 bytes)
                - str: hex-encoded private key
        """
        if private_key is None:
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        elif isinstance(private_key, ecdsa.SigningKey):
            self.private_key = private_key
        elif isinstance(private_key, bytes):
            # Raw bytes - convert to SigningKey
            if len(private_key) != 32:
                raise ValueError(f"Private key must be 32 bytes, got {len(private_key)}")
            self.private_key = ecdsa.SigningKey.from_string(
                private_key, curve=ecdsa.SECP256k1
            )
        elif isinstance(private_key, str):
            # Hex string
            key_bytes = bytes.fromhex(private_key)
            self.private_key = ecdsa.SigningKey.from_string(
                key_bytes, curve=ecdsa.SECP256k1
            )
        else:
            raise TypeError(f"Unsupported private_key type: {type(private_key)}")
        
        self.public_key = self.private_key.get_verifying_key()
    
    @property
    def private_key_hex(self) -> str:
        return self.private_key.to_string().hex()
    
    @property
    def public_key_hex(self) -> str:
        return self.public_key.to_string().hex()
    
    def get_address(self) -> str:
        """Generate a wallet address from the public key."""
        pub_bytes = self.public_key.to_string()
        sha = hashlib.sha256(pub_bytes).digest()
        addr_hash = hashlib.sha256(sha).hexdigest()
        return "TIME" + addr_hash[:40]
    
    @property
    def address(self) -> str:
        """Alias for get_address()."""
        return self.get_address()
    
    def sign(self, message) -> str:
        """Sign a message (string or bytes). Returns hex signature."""
        if isinstance(message, str):
            message = message.encode('utf-8')
        signature = self.private_key.sign(message)
        return signature.hex()
    
    def verify(self, message, signature_hex: str) -> bool:
        """Verify a signature over a message."""
        try:
            if isinstance(message, str):
                message = message.encode('utf-8')
            sig = bytes.fromhex(signature_hex)
            return self.public_key.verify(sig, message)
        except Exception:
            return False
    
    def to_dict(self) -> dict:
        return {
            "public_key": self.public_key_hex,
            "address": self.get_address(),
        }
    
    @classmethod
    def from_private_hex(cls, hex_str: str) -> "KeyPair":
        return cls(private_key=hex_str)
    
    def __repr__(self):
        return f"KeyPair(address={self.address[:16]}...)"


class CryptoError(Exception):
    """Base exception for cryptographic operations."""
    pass


class MerkleTree:
    """
    Merkle tree for efficient transaction verification.
    """
    
    def __init__(self, transactions):
        self.transactions = transactions
        self.root = self._build_tree(transactions)
    
    def _build_tree(self, txs):
        if not txs:
            return hash_data("")
        
        # Use txid if the item exposes it, otherwise hash stringified item
        if hasattr(txs[0], 'txid'):
            layer = [tx.txid for tx in txs]
        else:
            layer = [hash_data(str(tx)) for tx in txs]
        
        while len(layer) > 1:
            next_layer = []
            for i in range(0, len(layer), 2):
                left = layer[i]
                right = layer[i + 1] if i + 1 < len(layer) else left
                combined = left + right
                next_layer.append(hash_data(combined))
            layer = next_layer
        
        return layer[0]
    
    def get_proof(self, index: int) -> list:
        """Get Merkle proof for a leaf."""
        if index < 0 or index >= len(self.transactions):
            raise CryptoError(f"Index {index} out of range")
        
        proof = []
        current_level = self._get_leaf_hashes()
        current_index = index
        
        while len(current_level) > 1:
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                position = "right"
            else:
                sibling_index = current_index - 1
                position = "left"
            
            if sibling_index < len(current_level):
                proof.append({
                    "hash": current_level[sibling_index],
                    "position": position
                })
            
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]
                next_level.append(hash_data(combined))
            
            current_level = next_level
            current_index = current_index // 2
        
        return proof
    
    def _get_leaf_hashes(self):
        if hasattr(self.transactions[0], 'txid'):
            return [tx.txid for tx in self.transactions]
        return [hash_data(str(tx)) for tx in self.transactions]
    
    @staticmethod
    def verify_proof(leaf, proof: list, root: str) -> bool:
        """Verify a Merkle proof."""
        current = hash_data(str(leaf)) if not isinstance(leaf, str) else leaf
        
        for step in proof:
            sibling = step["hash"]
            if step["position"] == "right":
                combined = current + sibling
            else:
                combined = sibling + current
            current = hash_data(combined)
        
        return current == root
