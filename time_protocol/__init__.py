"""
TIME Protocol - A complete, working blockchain implementation.
"""

__version__ = "3.0.0"

# Core
from .crypto import KeyPair, MerkleTree, hash_data, hash_object, double_hash
from .transaction import Transaction, TxInput, TxOutput, TransactionBuilder
from .block import Block
from .ledger import Ledger, UTXO
from .wallet import Wallet

# Difficulty & Mining
from .difficulty import DifficultyManager
from .mining import MiningService, AutoSaveMiningService

# Node & Network
from .node import Node
from .p2p import P2PNode
from .rpc_server import run_rpc_server
from .sync import BlockSynchronizer

# Persistence
from .storage import Storage, PersistentNode

# Advanced features
from .multisig import MultiSigWallet, create_2_of_3, create_3_of_5
from .discovery import PeerDiscovery, PeerInfo

# Web
from .web.explorer import run_explorer

__all__ = [
    # Core
    "KeyPair", "MerkleTree", "hash_data", "hash_object", "double_hash",
    "Transaction", "TxInput", "TxOutput", "TransactionBuilder",
    "Block", "Ledger", "UTXO", "Wallet",
    # Difficulty & Mining
    "DifficultyManager", "MiningService", "AutoSaveMiningService",
    # Node & Network
    "Node", "P2PNode", "run_rpc_server", "BlockSynchronizer",
    # Persistence
    "Storage", "PersistentNode",
    # Advanced
    "MultiSigWallet", "create_2_of_3", "create_3_of_5",
    "PeerDiscovery", "PeerInfo",
    # Web
    "run_explorer",
]
