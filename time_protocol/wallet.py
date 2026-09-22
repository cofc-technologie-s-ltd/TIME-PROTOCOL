from .crypto import KeyPair
from .transaction import Transaction, TxInput, TxOutput

class Wallet:
    def __init__(self):
        self.key_pair = KeyPair()
        self.address = self.key_pair.address

    def get_utxos(self, ledger):
        return ledger.get_utxos_for(self.address)

    def get_balance(self, ledger) -> float:
        return sum(u.amount for u in self.get_utxos(ledger))

    def create_transaction(self, recipient: str, amount: float, ledger, fee: float = 0.0) -> Transaction:
        available_utxos = self.get_utxos(ledger)
        total = sum(u.amount for u in available_utxos)
        
        required_amount = amount + fee
        if total < required_amount:
            raise ValueError("Insufficient funds")

        inputs = []
        accumulated = 0
        for u in available_utxos:
            inputs.append(TxInput(u.txid, u.output_index, pubkey=self.key_pair.public_key.to_string().hex()))
            accumulated += u.amount
            if accumulated >= required_amount:
                break

        outputs = [TxOutput(amount, recipient)]
        change = accumulated - required_amount
        if change > 0:
            outputs.append(TxOutput(change, self.address))

        tx = Transaction(inputs, outputs)
        return tx
