"""
TIME Protocol - HD Wallets (BIP32/BIP44 style)
Hierarchical Deterministic wallets - one seed, infinite addresses.
"""

import hmac
import hashlib
from typing import List, Tuple
from .crypto import KeyPair


class HDWallet:
    """
    Hierarchical Deterministic Wallet.
    
    One master seed → infinite child keys.
    Deterministic: same seed always produces same keys.
    
    Simplified BIP32-like implementation:
    - master_key = HMAC-SHA512(seed)
    - child_key = HMAC-SHA512(parent_key + index)
    """
    
    HARDENED_OFFSET = 0x80000000
    
    def __init__(self, seed: bytes = None):
        if seed is None:
            seed = bytes(32)  # Default zero seed for reproducibility
        
        self.seed = seed
        self.master_private = self._derive_master(seed)
        self._cache = {}
    
    @classmethod
    def from_mnemonic(cls, mnemonic: str) -> "HDWallet":
        """Create HD wallet from a mnemonic phrase."""
        seed = hashlib.pbkdf2_hmac(
            'sha512',
            mnemonic.encode(),
            b'time_protocol_salt',
            iterations=2048,
            dklen=64,
        )
        return cls(seed)
    
    @classmethod
    def random(cls) -> "HDWallet":
        """Create HD wallet with random seed."""
        import secrets
        seed = secrets.token_bytes(32)
        return cls(seed)
    
    def _derive_master(self, seed: bytes) -> bytes:
        """Derive master private key from seed."""
        h = hmac.new(b"TIME_Protocol_seed", seed, hashlib.sha512).digest()
        return h[:32]
    
    def _derive_child(self, parent_private: bytes, index: int) -> bytes:
        """Derive child private key from parent + index."""
        data = parent_private + index.to_bytes(4, byteorder='big')
        h = hmac.new(b"TIME_Protocol_child", data, hashlib.sha512).digest()
        return h[:32]
    
    def derive_path(self, path: str) -> KeyPair:
        """
        Derive a key along a BIP44-style path.
        Format: "m/44'/0'/0'/0/0"
        """
        if path in self._cache:
            return self._cache[path]
        
        if not path.startswith("m"):
            raise ValueError(f"Path must start with 'm/', got: {path}")
        
        parts = path.split("/")[1:]  # Remove "m"
        current = self.master_private
        
        for part in parts:
            if part.endswith("'") or part.endswith("h"):
                index = int(part[:-1]) + self.HARDENED_OFFSET
            else:
                index = int(part)
            current = self._derive_child(current, index)
        
        kp = KeyPair(private_key=bytes.fromhex(current.hex()))
        self._cache[path] = kp
        return kp
    
    def derive_address(self, index: int, account: int = 0, change: int = 0) -> KeyPair:
        """
        Convenience: derive using BIP44-like path.
        m / 44' / 0' / account' / change / index
        """
        path = f"m/44'/0'/{account}'/{change}/{index}"
        return self.derive_path(path)
    
    def get_addresses(self, count: int = 5) -> List[Tuple[int, str]]:
        """Generate the first N receiving addresses."""
        result = []
        for i in range(count):
            kp = self.derive_address(i)
            result.append((i, kp.address))
        return result
    
    def to_dict(self) -> dict:
        return {
            "seed": self.seed.hex(),
            "master_private": self.master_private.hex(),
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "HDWallet":
        wallet = cls(bytes.fromhex(d["seed"]))
        return wallet
