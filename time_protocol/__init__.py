"""
TIME Protocol - A real, working blockchain implementation.
"""

__version__ = "2.5.0"

from .crypto import KeyPair, MerkleTree, hash_data, hash_object, double_hash
from .transaction import Transaction, TxInput, TxOutput, TransactionBuilder
from .block import Block
from .ledger import Ledger, UTXO
from .wallet import Wallet
from .difficulty import DifficultyManager
from .mining import MiningService
from .node import Node
from .p2p import P2PNode
from .rpc_server import run_rpc_server
from .sync import BlockSynchronizer
from .storage import Storage, PersistentNode
from .web.explorer import run_explorer

__all__ = [
    "KeyPair", "MerkleTree", "hash_data", "hash_object", "double_hash",
    "Transaction", "TxInput", "TxOutput", "TransactionBuilder",
    "Block", "Ledger", "UTXO", "Wallet",
    "DifficultyManager", "MiningService",
    "Node", "P2PNode",
    "run_rpc_server", "BlockSynchronizer",
    "Storage", "PersistentNode",
    "run_explorer",
]
