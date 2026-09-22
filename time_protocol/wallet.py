from .crypto import KeyPair
from .transaction import Transaction, TxInput, TxOutput


class Wallet:
    """
    Basic wallet: manages a key pair, tracks address, signs transactions.
    
    Usage:
        wallet = Wallet()                    # Random new wallet
        wallet = Wallet(label="alice")       # With a label
        wallet = Wallet(key_pair=kp)         # From existing keypair
    """
    
    def __init__(self, key_pair=None, label: str = ""):
        self.key_pair = key_pair or KeyPair()
        self.address = self.key_pair.address
        self.label = label

    @property
    def public_key(self) -> str:
        return self.key_pair.public_key.to_string().hex()

    @property
    def private_key(self) -> str:
        return self.key_pair.private_key.to_string().hex()

    def get_balance(self, ledger) -> float:
        """Return balance for this wallet's address."""
        return ledger.get_balance(self.address)

    def get_utxos(self, ledger) -> list:
        """Return all UTXOs owned by this wallet."""
        return ledger.get_utxos_for(self.address)

    def create_transaction(self, recipient: str, amount: float, ledger, fee: float = 0.0) -> Transaction:
        """Build and sign a transaction spending from this wallet."""
        available_utxos = self.get_utxos(ledger)
        total = sum(u.amount for u in available_utxos)

        if total < amount + fee:
            raise ValueError(
                f"Insufficient funds: have {total}, need {amount + fee}"
            )

        # Select UTXOs (simple: take until we have enough)
        inputs = []
        accumulated = 0.0
        pubkey_hex = self.public_key

        for u in available_utxos:
            inputs.append(TxInput(
                txid=u.txid,
                output_index=u.output_index,
                pubkey=pubkey_hex,
                signature=""
            ))
            accumulated += u.amount
            if accumulated >= amount + fee:
                break

        # Outputs: recipient + change (if any)
        outputs = [TxOutput(amount=amount, recipient_address=recipient)]
        change = accumulated - amount - fee
        if change > 0:
            outputs.append(TxOutput(amount=change, recipient_address=self.address))

        tx = Transaction(inputs=inputs, outputs=outputs)

        # Sign each input over the transaction's signing payload
        signing_data = tx.get_signing_payload()
        for i, tx_input in enumerate(tx.inputs):
            tx.inputs[i].signature = self.key_pair.sign(signing_data)

        return tx

    def save(self, filepath: str, password: str = ""):
        import json, hashlib
        data = {
            "private_key": self.private_key,
            "address": self.address,
            "label": self.label,
        }
        raw = json.dumps(data).encode()
        if password:
            key = hashlib.sha256(password.encode()).digest()
            encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
            with open(filepath, "wb") as f:
                f.write(b"TIME_WALLET_V1_" + encrypted)
        else:
            with open(filepath, "w") as f:
                f.write(json.dumps(data))

    @classmethod
    def load(cls, filepath: str, password: str = "") -> "Wallet":
        import json, hashlib, ecdsa
        from .crypto import KeyPair as KP
        with open(filepath, "rb") as f:
            content = f.read()

        if content.startswith(b"TIME_WALLET_V1_"):
            if not password:
                raise ValueError("Password required")
            encrypted = content[len(b"TIME_WALLET_V1_"):]
            key = hashlib.sha256(password.encode()).digest()
            raw = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
            data = json.loads(raw.decode())
        else:
            data = json.loads(content.decode())

        sk = ecdsa.SigningKey.from_string(
            bytes.fromhex(data["private_key"]),
            curve=ecdsa.SECP256k1
        )
        kp = KP(private_key=sk)
        return cls(key_pair=kp, label=data.get("label", ""))

    def to_dict(self, include_private: bool = False) -> dict:
        data = {
            "address": self.address,
            "public_key": self.public_key,
            "label": self.label,
        }
        if include_private:
            data["private_key"] = self.private_key
        return data

    def __repr__(self) -> str:
        label_str = f" label={self.label!r}" if self.label else ""
        return f"Wallet({self.address[:16]}...{label_str})"
