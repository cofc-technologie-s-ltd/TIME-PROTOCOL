import hashlib
import ecdsa
import json

def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def double_hash(data: str) -> str:
    h1 = hashlib.sha256(data.encode('utf-8')).digest()
    return hashlib.sha256(h1).hexdigest()

def hash_object(obj) -> str:
    if hasattr(obj, 'to_dict'):
        d = obj.to_dict()
    else:
        d = obj
    return hash_data(json.dumps(d, sort_keys=True))

class KeyPair:
    def __init__(self, private_key=None):
        if private_key:
            self.private_key = private_key
        else:
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    def sign(self, message: str) -> str:
        signature = self.private_key.sign(message.encode('utf-8'))
        return signature.hex()

    def verify(self, message: str, signature_hex: str) -> bool:
        try:
            sig = bytes.fromhex(signature_hex)
            return self.public_key.verify(sig, message.encode('utf-8'))
        except Exception:
            return False

    @property
    def address(self) -> str:
        pub_bytes = self.public_key.to_string()
        return hashlib.new('ripemd160', hashlib.sha256(pub_bytes).digest()).hexdigest()

class MerkleTree:
    def __init__(self, transactions):
        self.transactions = transactions
        self.root = self._build_tree(transactions)

    def _build_tree(self, txs):
        if not txs:
            return hash_data("")
        
        if hasattr(txs[0], 'txid'):
            layer = [tx.txid for tx in txs]
        else:
            layer = [hash_data(str(tx)) for tx in txs]

        while len(layer) > 1:
            next_layer = []
            for i in range(0, len(layer), 2):
                left = layer[i]
                right = layer[i+1] if i+1 < len(layer) else left
                combined = left + right
                next_layer.append(hash_data(combined))
            layer = next_layer
        return layer[0]
