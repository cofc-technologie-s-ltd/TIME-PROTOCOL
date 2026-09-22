"""
TIME Protocol - Multi-Signature Wallets
Implements M-of-N signature schemes for shared control.
"""

import hashlib
import time
from typing import List, Optional
from .crypto import KeyPair, hash_data, CryptoError


class MultiSigError(Exception):
    """Multi-signature errors."""
    pass


class MultiSigWallet:
    """
    M-of-N Multi-Signature Wallet.
    
    To spend funds, M out of N authorized keys must sign the transaction.
    This is useful for:
    - Corporate accounts (require CFO + CEO approval)
    - Escrow services (buyer + seller + arbitrator)
    - Personal security (multiple devices)
    """
    
    def __init__(self, required: int, keypairs: List[KeyPair]):
        if required < 1:
            raise MultiSigError("Required signatures must be >= 1")
        if required > len(keypairs):
            raise MultiSigError(f"Required ({required}) > Total keys ({len(keypairs)})")
        
        self.required = required
        self.keypairs = keypairs
        self.total = len(keypairs)
        self.address = self._compute_address()
    
    def _compute_address(self) -> str:
        """
        Deterministic address from all public keys.
        Anyone can derive the same address from the public keys.
        """
        # Sort public keys to ensure deterministic ordering
        pub_keys = sorted(kp.public_key.to_string().hex() for kp in self.keypairs)
        combined = f"{self.required}-of-{self.total}:" + ":".join(pub_keys)
        addr_hash = hashlib.sha256(combined.encode()).hexdigest()
        return "MULTI" + addr_hash[:40]
    
    @classmethod
    def from_public_keys(cls, required: int, public_keys_hex: List[str]) -> "MultiSigWallet":
        """
        Create a MultiSigWallet from just public keys.
        This is how other nodes verify a multisig address without having private keys.
        """
        # We need fake KeyPairs to compute the same address
        # The address computation only uses public keys
        class FakeKP:
            def __init__(self, pub_hex):
                self.public_key = type('obj', (object,), {
                    'to_string': lambda self: bytes.fromhex(pub_hex)
                })()
        
        fake_kps = [FakeKP(pk) for pk in public_keys_hex]
        
        wallet = cls.__new__(cls)
        wallet.required = required
        wallet.keypairs = fake_kps
        wallet.total = len(fake_kps)
        wallet.address = wallet._compute_address()
        return wallet
    
    def create_transaction(self, recipient: str, amount: float, ledger, fee: float = 0.0):
        """
        Create a multisig transaction requiring M signatures.
        """
        from .transaction import Transaction, TxInput, TxOutput
        
        available_utxos = ledger.get_utxos_for(self.address)
        total = sum(u.amount for u in available_utxos)
        
        if total < amount + fee:
            raise MultiSigError(f"Insufficient funds: have {total}, need {amount + fee}")
        
        # Select UTXOs
        inputs = []
        accumulated = 0.0
        for u in available_utxos:
            inputs.append(TxInput(
                txid=u.txid,
                output_index=u.output_index,
                pubkey="",  # Will be filled with all public keys
                signature=""  # Will be filled with all signatures
            ))
            accumulated += u.amount
            if accumulated >= amount + fee:
                break
        
        # Outputs
        outputs = [TxOutput(amount=amount, recipient_address=recipient)]
        change = accumulated - amount - fee
        if change > 0:
            outputs.append(TxOutput(amount=change, recipient_address=self.address))
        
        tx = Transaction(inputs=inputs, outputs=outputs)
        
        # Sign with each keypair
        signing_payload = tx.get_signing_payload()
        signatures = []
        pub_keys = []
        
        for kp in self.keypairs:
            sig = kp.sign(signing_payload)
            signatures.append(sig)
            pub_keys.append(kp.public_key.to_string().hex())
        
        # Store metadata on the first input
        # Format: "multisig:required|pubkey1,pubkey2,...|sig1,sig2,..."
        meta = f"multisig:{self.required}|{','.join(pub_keys)}|{','.join(signatures)}"
        tx.inputs[0].pubkey = meta
        
        return tx
    
    def verify_transaction(self, tx, ledger) -> bool:
        """
        Verify that a multisig transaction has enough valid signatures.
        """
        from .crypto import KeyPair as KP
        from ecdsa import VerifyingKey, SECP256k1
        
        try:
            # Parse multisig metadata
            meta = tx.inputs[0].pubkey
            if not meta.startswith("multisig:"):
                raise MultiSigError("Not a multisig transaction")
            
            parts = meta.split("|")
            required = int(parts[0].split(":")[1])
            pub_keys = parts[1].split(",")
            signatures = parts[2].split(",")
            
            if required > len(signatures):
                return False
            
            # Verify each signature against its public key
            signing_payload = tx.get_signing_payload()
            valid_sigs = 0
            
            for i, (pub_hex, sig_hex) in enumerate(zip(pub_keys, signatures)):
                try:
                    vk = VerifyingKey.from_string(bytes.fromhex(pub_hex), curve=SECP256k1)
                    if vk.verify(bytes.fromhex(sig_hex), signing_payload.encode() if isinstance(signing_payload, str) else signing_payload):
                        valid_sigs += 1
                except Exception:
                    pass
            
            return valid_sigs >= required
        except Exception as e:
            return False
    
    def info(self) -> dict:
        return {
            "type": "multisig",
            "required": self.required,
            "total": self.total,
            "address": self.address,
            "public_keys": [kp.public_key.to_string().hex() for kp in self.keypairs],
        }


# Convenience constructors
def create_2_of_3() -> MultiSigWallet:
    """Create a 2-of-3 multisig wallet (common for escrow)."""
    return MultiSigWallet(required=2, keypairs=[KeyPair() for _ in range(3)])


def create_3_of_5() -> MultiSigWallet:
    """Create a 3-of-5 multisig wallet (corporate)."""
    return MultiSigWallet(required=3, keypairs=[KeyPair() for _ in range(5)])
