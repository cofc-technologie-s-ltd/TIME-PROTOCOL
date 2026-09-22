import time
from typing import List, Dict, Any
from .crypto import hash_data, KeyPair

class TxInput:
    def __init__(self, txid: str, output_index: int, signature: str = "", pubkey: str = ""):
        self.txid = txid
        self.output_index = output_index
        self.signature = signature
        self.pubkey = pubkey

    def to_dict(self) -> Dict[str, Any]:
        return {
            "txid": self.txid,
            "output_index": self.output_index,
            "signature": self.signature,
            "pubkey": self.pubkey
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'TxInput':
        return cls(d["txid"], d["output_index"], d["signature"], d["pubkey"])

class TxOutput:
    def __init__(self, amount: float, recipient_address: str):
        self.amount = amount
        self.recipient_address = recipient_address

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": self.amount,
            "recipient_address": self.recipient_address
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'TxOutput':
        return cls(d["amount"], d["recipient_address"])

class Transaction:
    def __init__(self, inputs: List[TxInput], outputs: List[TxOutput], timestamp: float = None):
        self.inputs = inputs
        self.outputs = outputs
        self.timestamp = timestamp or time.time()
        self.txid = self.calculate_txid()

    def calculate_txid(self) -> str:
        data = {
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "timestamp": self.timestamp
        }
        return hash_data(str(data))

    def sign_transaction(self, key_pair: KeyPair):
        for inp in self.inputs:
            if inp.txid != "COINBASE":
                inp.pubkey = key_pair.public_key.to_string().hex()
                inp.signature = key_pair.sign(self.txid)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "txid": self.txid,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Transaction':
        inputs = [TxInput.from_dict(i) for i in d["inputs"]]
        outputs = [TxOutput.from_dict(o) for o in d["outputs"]]
        tx = cls(inputs, outputs, d["timestamp"])
        tx.txid = d["txid"]
        return tx

class TransactionBuilder:
    @staticmethod
    def create_coinbase(recipient_address: str, amount: float) -> Transaction:
        coinbase_input = TxInput(txid="COINBASE", output_index=-1)
        output = TxOutput(amount=amount, recipient_address=recipient_address)
        return Transaction(inputs=[coinbase_input], outputs=[output])
