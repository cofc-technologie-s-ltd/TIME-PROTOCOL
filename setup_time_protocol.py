import os

def create_project_structure():
    files = {
        "time_protocol/__init__.py": '''from .crypto import hash_data, double_hash, hash_object, KeyPair, MerkleTree
from .transaction import TxInput, TxOutput, Transaction, TransactionBuilder
from .block import Block
from .ledger import UTXO, Ledger
from .node import Node
from .p2p import P2PNode
from .rpc_server import run_production_server, ProductionRPCHandler

# Aliases for legacy test compatibility
run_rpc_server = run_production_server
Wallet = KeyPair
''',
        "time_protocol/crypto.py": '''import hashlib
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
''',
        "time_protocol/transaction.py": '''import time
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
''',
        "time_protocol/block.py": '''import time
from typing import List, Dict, Any
from .crypto import hash_data, MerkleTree
from .transaction import Transaction

class Block:
    def __init__(self, index: int, previous_hash: str, transactions: List[Transaction], nonce: int = 0, timestamp: float = None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.nonce = nonce
        self.timestamp = timestamp or time.time()
        self.merkle_root = MerkleTree(self.transactions).root
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "timestamp": self.timestamp
        }
        return hash_data(str(block_data))

    def mine(self, difficulty: int):
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def is_valid(self, previous_block: 'Block' = None) -> bool:
        if previous_block and self.index != previous_block.index + 1:
            return False
        if previous_block and self.previous_hash != previous_block.hash:
            return False
        if self.hash != self.calculate_hash():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Block':
        txs = [Transaction.from_dict(t) for t in d["transactions"]]
        block = cls(d["index"], d["previous_hash"], txs, d["nonce"], d["timestamp"])
        block.hash = d["hash"]
        block.merkle_root = d["merkle_root"]
        return block
''',
        "time_protocol/ledger.py": '''from typing import List, Dict
from .block import Block

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

    def add_block(self, block: Block) -> bool:
        if self.chain and not block.is_valid(self.latest_block):
            return False
        self.chain.append(block)
        for tx in block.transactions:
            for inp in tx.inputs:
                if inp.txid != "COINBASE":
                    key = f"{inp.txid}:{inp.output_index}"
                    self.utxo_set.pop(key, None)
            for idx, out in enumerate(tx.outputs):
                key = f"{tx.txid}:{idx}"
                self.utxo_set[key] = UTXO(tx.txid, idx, out.amount, out.recipient_address)
        return True

    def get_balance(self, address: str) -> float:
        return sum(utxo.amount for utxo in self.utxo_set.values() if utxo.address == address)
''',
        "time_protocol/node.py": '''from .ledger import Ledger
from .block import Block
from .transaction import TransactionBuilder, Transaction

class Node:
    def __init__(self, difficulty: int = 2):
        self.ledger = Ledger()
        self.difficulty = difficulty
        self.mempool: list = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_tx = TransactionBuilder.create_coinbase("SOVEREIGN_MASTER_VAULT", 3000000000.0)
        genesis_block = Block(index=0, previous_hash="0" * 64, transactions=[genesis_tx])
        genesis_block.mine(self.difficulty)
        self.ledger.add_block(genesis_block)

    def add_transaction_to_mempool(self, tx: Transaction) -> bool:
        self.mempool.append(tx)
        return True

    def mine_pending_transactions(self, miner_address: str) -> Block:
        reward_tx = TransactionBuilder.create_coinbase(miner_address, 50.0)
        all_txs = [reward_tx] + self.mempool
        new_block = Block(
            index=self.ledger.latest_block.index + 1,
            previous_hash=self.ledger.latest_block.hash,
            transactions=all_txs
        )
        new_block.mine(self.difficulty)
        self.ledger.add_block(new_block)
        self.mempool = []
        return new_block
''',
        "time_protocol/p2p.py": '''import socket
import threading
import json
import logging
from .block import Block
from .node import Node

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] P2P: %(message)s')

class P2PNode:
    def __init__(self, host: str, port: int, node: Node):
        self.host = host
        self.port = port
        self.node = node
        self.peers = []
        self.server_socket = None
        self.is_running = False
        self.thread = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.is_running = True
        self.thread = threading.Thread(target=self._accept_connections, daemon=True)
        self.thread.start()
        logging.info(f"Enterprise P2P Node active on {self.host}:{self.port}")

    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        logging.info("Enterprise P2P Node stopped.")

    def _accept_connections(self):
        while self.is_running:
            try:
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_peer, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_peer(self, sock: socket.socket):
        try:
            data = sock.recv(4096)
            if data:
                message = json.loads(data.decode('utf-8'))
                response = self._process_message(message)
                sock.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logging.error(f"Error handling peer connection: {e}")
        finally:
            sock.close()

    def _process_message(self, msg: dict) -> dict:
        msg_type = msg.get("type")
        if msg_type == "GET_CHAIN":
            return {
                "status": "SUCCESS",
                "chain": [b.to_dict() for b in self.node.ledger.chain]
            }
        elif msg_type == "NEW_BLOCK":
            block_data = msg.get("payload")
            block = Block.from_dict(block_data)
            if self.node.ledger.add_block(block):
                return {"status": "SUCCESS", "message": "Block appended and verified"}
            return {"status": "ERROR", "message": "Invalid block rejected"}
        return {"status": "UNKNOWN_MESSAGE"}
''',
        "time_protocol/rpc_server.py": '''from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from .node import Node

class ProductionRPCHandler(BaseHTTPRequestHandler):
    node_instance: Node = None

    def do_GET(self):
        if self.path == "/api/v1/chain":
            self._send_json({
                "status": "ONLINE",
                "length": len(self.node_instance.ledger.chain),
                "chain": [b.to_dict() for b in self.node_instance.ledger.chain]
            })
        elif self.path.startswith("/api/v1/balance/"):
            address = self.path.split("/")[-1]
            balance = self.node_instance.ledger.get_balance(address)
            self._send_json({"status": "SUCCESS", "address": address, "balance": balance})
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode('utf-8'))
        except Exception:
            self._send_json({"error": "Invalid JSON Payload"}, status=400)
            return

        if self.path == "/api/v1/mine":
            miner_address = data.get("miner_address", "SOVEREIGN_MASTER_VAULT")
            block = self.node_instance.mine_pending_transactions(miner_address)
            self._send_json({"status": "SUCCESS", "mined_block": block.to_dict()})
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data: dict, status: int = 200):
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        return

def run_production_server(node: Node, host: str = "0.0.0.0", port: int = 8080):
    ProductionRPCHandler.node_instance = node
    server = HTTPServer((host, port), ProductionRPCHandler)
    logging.info(f"Production Sovereign REST API active on http://{host}:{port}")
    return server
''',
        "tests/__init__.py": "",
    }

    for filepath, content in files.items():
        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[CREATED/UPDATED] {filepath}")

if __name__ == "__main__":
    print("Initializing Time Protocol Enterprise Framework...")
    create_project_structure()
    print("All architecture and module bindings updated successfully!")

