from typing import List, Dict
from .block import Block
from .transaction import Transaction


class UTXO:
    def __init__(self, txid: str, output_index: int, amount: float, address: str):
        self.txid = txid
        self.output_index = output_index
        self.amount = amount
        self.address = address

    def to_dict(self) -> dict:
        return {
            "txid": self.txid,
            "output_index": self.output_index,
            "amount": self.amount,
            "address": self.address
        }


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
        """Add a block and update UTXO set based on its transactions."""
        self.chain.append(block)
        for tx in block.transactions:
            # Remove spent UTXOs (skip coinbase)
            for inp in tx.inputs:
                if inp.txid != "COINBASE":
                    key = f"{inp.txid}:{inp.output_index}"
                    self.utxo_set.pop(key, None)
            # Add new UTXOs
            for idx, out in enumerate(tx.outputs):
                key = f"{tx.txid}:{idx}"
                self.utxo_set[key] = UTXO(tx.txid, idx, out.amount, out.recipient_address)

    def get_balance(self, address: str) -> float:
        """Return total unspent balance for an address."""
        return sum(utxo.amount for utxo in self.utxo_set.values() if utxo.address == address)

    def get_utxos_for(self, address: str) -> List[UTXO]:
        """Return all UTXOs owned by an address."""
        return [u for u in self.utxo_set.values() if u.address == address]

    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain from genesis to tip."""
        if not self.chain:
            return False

        # Genesis must be index 0
        if self.chain[0].index != 0:
            return False

        # Validate every block against its predecessor
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check index continuity
            if current.index != previous.index + 1:
                return False

            # Check hash linkage
            if current.previous_hash != previous.hash:
                return False

            # Check block internal validity
            if not current.is_valid(previous):
                return False

        # Ensure no block hash was tampered with
        for block in self.chain:
            if block.hash != block.calculate_hash():
                return False

        return True
