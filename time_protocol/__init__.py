"""
TIME Protocol - Complete Blockchain Implementation
"""

__version__ = "5.0.0"

# Core
from .crypto import KeyPair, MerkleTree, hash_data, hash_object, double_hash
from .transaction import Transaction, TxInput, TxOutput, TransactionBuilder
from .block import Block
from .ledger import Ledger, UTXO
from .wallet import Wallet

# Difficulty & Mining
from .difficulty import DifficultyManager
from .mining import MiningService, AutoSaveMiningService
from .parallel_miner import ParallelMiner, ParallelMiningService

# Node & Network
from .node import Node
from .p2p import P2PNode
from .p2p_real import RealP2PNode
from .rpc_server import run_rpc_server
from .sync import BlockSynchronizer

# Persistence
from .storage import Storage, PersistentNode

# Advanced features
from .multisig import MultiSigWallet, MultiSigTransaction, create_2_of_3, create_3_of_5
from .discovery import PeerDiscovery, PeerInfo
from .hd_wallet import HDWallet

# v5.0: Consensus & Contracts
from .pos_consensus import ProofOfStakeConsensus, Validator
from .smart_contracts import ContractVM, Contract, ContractStorage

# Monitoring & Docs
from .metrics import MetricsCollector
from .logging_config import setup_logging
from .openapi import get_openapi_json, get_swagger_ui_html
from .difficulty_chart import generate_difficulty_chart, generate_blocktime_chart

# Web
from .web.explorer import run_explorer

__all__ = [
    # Core
    "KeyPair", "MerkleTree", "hash_data", "hash_object", "double_hash",
    "Transaction", "TxInput", "TxOutput", "TransactionBuilder",
    "Block", "Ledger", "UTXO", "Wallet",
    # Difficulty & Mining
    "DifficultyManager", "MiningService", "AutoSaveMiningService",
    "ParallelMiner", "ParallelMiningService",
    # Node & Network
    "Node", "P2PNode", "RealP2PNode", "run_rpc_server", "BlockSynchronizer",
    # Persistence
    "Storage", "PersistentNode",
    # Advanced
    "MultiSigWallet", "MultiSigTransaction", "create_2_of_3", "create_3_of_5",
    "PeerDiscovery", "PeerInfo", "HDWallet",
    # v5.0
    "ProofOfStakeConsensus", "Validator",
    "ContractVM", "Contract", "ContractStorage",
    # Monitoring
    "MetricsCollector", "setup_logging",
    "get_openapi_json", "get_swagger_ui_html",
    "generate_difficulty_chart", "generate_blocktime_chart",
    # Web
    "run_explorer",
]
