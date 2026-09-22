from typing import List, Dict
from .block import Block
from .transaction import Transaction

class UTXO:
    def __init__(self, txid: str, output_index: int, amount: float, address: str):
        self.txid = txid
        self.output_index = output_index
        self.amount = amount
        self.address = address

class Ledger:
    def __init__(self):
        self.chain: List[Block] = []
        self.utxo_set: Dict[str, UTXO] = {}

    @property
    def latest_block(self) -> Block:
        return self.chain[-1] if self.chain else None

    @property
    def height(self) -> int:
        return len(self.chain) - 1 if self.chain else -1

    def add_block(self, block: Block):
        self.chain.append(block)
        for tx in block.transactions:
            for inp in tx.inputs:
                if inp.txid != "COINBASE":
                    key = f"{inp.txid}:{inp.output_index}"
                    self.utxo_set.pop(key, None)
            for idx, out in enumerate(tx.outputs):
                key = f"{tx.txid}:{idx}"
                self.utxo_set[key] = UTXO(tx.txid, idx, out.amount, out.recipient_address)

    def get_balance(self, address: str) -> float:
        return sum(utxo.amount for utxo in self.utxo_set.values() if utxo.address == address)

    def get_utxos_for(self, address: str) -> List[UTXO]:
        return [utxo for utxo in self.utxo_set.values() if utxo.address == address]

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if not current.is_valid(previous):
                return False
        return True
