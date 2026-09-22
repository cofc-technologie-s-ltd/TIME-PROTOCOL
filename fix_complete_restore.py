import os

# ============================================================
# 1. multisig.py - Multi-Signature Wallets
# ============================================================
with open("time_protocol/multisig.py", "w") as f:
    f.write('''"""
TIME Protocol - Multi-Signature Wallets
M-of-N signature schemes for shared control.
"""

import hashlib
from .crypto import KeyPair


class MultiSigError(Exception):
    pass


class MultiSigTransaction:
    """A multisig transaction with all signatures attached."""
    
    def __init__(self, txid, recipient, amount, required, total, signatures, public_keys, fee=0.0):
        self.txid = txid
        self.recipient = recipient
        self.amount = amount
        self.required = required
        self.total = total
        self.signatures = signatures
        self.public_keys = public_keys
        self.fee = fee
    
    def to_dict(self):
        return {
            "txid": self.txid,
            "recipient": self.recipient,
            "amount": self.amount,
            "required": self.required,
            "total": self.total,
            "signatures": self.signatures,
            "public_keys": self.public_keys,
            "fee": self.fee,
        }


class MultiSigWallet:
    """
    M-of-N Multi-Signature Wallet.
    
    Usage:
        wallet = MultiSigWallet(required=2, keypairs=[kp1, kp2, kp3])
        tx = wallet.create_transaction("RECIPIENT", 10.0)
    """
    
    def __init__(self, required: int, keypairs: list):
        if required < 1:
            raise MultiSigError("Required signatures must be >= 1")
        if required > len(keypairs):
            raise MultiSigError(f"Required ({required}) > Total keys ({len(keypairs)})")
        
        self.required = required
        self.keypairs = keypairs
        self.total = len(keypairs)
        self.address = self._compute_address()
    
    def _compute_address(self) -> str:
        pub_keys = sorted(kp.public_key.to_string().hex() for kp in self.keypairs)
        combined = f"{self.required}-of-{self.total}:" + ":".join(pub_keys)
        addr_hash = hashlib.sha256(combined.encode()).hexdigest()
        return "MULTI" + addr_hash[:40]
    
    def create_transaction(self, recipient: str, amount: float, ledger=None, fee: float = 0.0):
        """Create a multisig transaction with all signatures."""
        txid_data = f"{self.address}:{recipient}:{amount}:{fee}"
        txid = hashlib.sha256(txid_data.encode()).hexdigest()
        
        # Sign with all keypairs (in real impl, only enough to satisfy required)
        signatures = []
        public_keys = []
        for kp in self.keypairs:
            sig = kp.sign(txid)
            signatures.append(sig)
            public_keys.append(kp.public_key.to_string().hex())
        
        return MultiSigTransaction(
            txid=txid,
            recipient=recipient,
            amount=amount,
            required=self.required,
            total=self.total,
            signatures=signatures,
            public_keys=public_keys,
            fee=fee,
        )


def create_2_of_3(keypairs=None) -> MultiSigWallet:
    """Create a 2-of-3 multisig wallet."""
    if keypairs is None:
        keypairs = [KeyPair() for _ in range(3)]
    return MultiSigWallet(required=2, keypairs=keypairs)


def create_3_of_5(keypairs=None) -> MultiSigWallet:
    """Create a 3-of-5 multisig wallet."""
    if keypairs is None:
        keypairs = [KeyPair() for _ in range(5)]
    return MultiSigWallet(required=3, keypairs=keypairs)
''')
print("[+] Restored multisig.py")

# ============================================================
# 2. discovery.py - Peer Discovery
# ============================================================
with open("time_protocol/discovery.py", "w") as f:
    f.write('''"""
TIME Protocol - Peer Discovery
Bootstrap nodes, peer exchange, and automatic reconnection.
"""

import time
import socket
from typing import List, Tuple, Optional


DEFAULT_BOOTSTRAP_NODES = [
    ("127.0.0.1", 8001),
    ("127.0.0.1", 8002),
    ("127.0.0.1", 8003),
]


class PeerInfo:
    def __init__(self, host: str, port: int, last_seen: float = None):
        self.host = host
        self.port = port
        self.last_seen = last_seen or time.time()
        self.failures = 0

    @property
    def address(self) -> Tuple[str, int]:
        return (self.host, self.port)

    def mark_seen(self):
        self.last_seen = time.time()
        self.failures = 0

    def mark_failed(self):
        self.failures += 1

    def should_retry(self, max_failures: int = 5) -> bool:
        return self.failures < max_failures

    def to_dict(self) -> dict:
        return {"host": self.host, "port": self.port, "last_seen": self.last_seen, "failures": self.failures}


class PeerDiscovery:
    """
    Manages peer discovery and connection.
    
    Usage:
        d = PeerDiscovery(own_port=9001, bootstrap_nodes=[])
        d.add_peer("1.2.3.4", 9002)
        stats = d.stats()
    """
    
    MAX_KNOWN_PEERS = 100
    PEER_TIMEOUT = 3600 * 24
    
    def __init__(self, own_port: int, bootstrap_nodes: Optional[List[Tuple[str, int]]] = None):
        self.own_port = own_port
        self.known_peers: dict = {}
        
        # Distinguish None (default) from [] (empty)
        if bootstrap_nodes is None:
            self.bootstrap = list(DEFAULT_BOOTSTRAP_NODES)
        else:
            self.bootstrap = list(bootstrap_nodes)
        
        # Add bootstrap peers (skip self)
        for host, port in self.bootstrap:
            self.add_peer(host, port)
    
    def add_peer(self, host: str, port: int) -> bool:
        """Add peer. Returns True if newly added."""
        # Don't add ourselves
        if port == self.own_port and host in ("127.0.0.1", "localhost", "0.0.0.0"):
            return False
        
        key = (host, port)
        if key in self.known_peers:
            return False
        
        if len(self.known_peers) >= self.MAX_KNOWN_PEERS:
            oldest = min(self.known_peers.values(), key=lambda p: p.last_seen)
            del self.known_peers[oldest.address]
        
        self.known_peers[key] = PeerInfo(host, port)
        return True
    
    def remove_peer(self, host: str, port: int) -> bool:
        return self.known_peers.pop((host, port), None) is not None
    
    def mark_peer_seen(self, host: str, port: int):
        if (host, port) in self.known_peers:
            self.known_peers[(host, port)].mark_seen()
    
    def mark_peer_failed(self, host: str, port: int):
        if (host, port) in self.known_peers:
            self.known_peers[(host, port)].mark_failed()
    
    def get_active_peers(self) -> List[PeerInfo]:
        return [p for p in self.known_peers.values() if p.should_retry()]
    
    def get_peer_list(self) -> List[dict]:
        return [p.to_dict() for p in self.known_peers.values()]
    
    def merge_peer_list(self, peer_dicts: List[dict]) -> int:
        """Merge peer list. Returns count of newly added peers."""
        added = 0
        for pd in peer_dicts:
            if self.add_peer(pd["host"], pd["port"]):
                added += 1
        return added
    
    def stats(self) -> dict:
        """Return discovery statistics."""
        now = time.time()
        active = 0
        stale = 0
        dead = 0
        
        for peer in self.known_peers.values():
            if not peer.should_retry():
                dead += 1
            elif now - peer.last_seen > self.PEER_TIMEOUT:
                stale += 1
            else:
                active += 1
        
        return {
            "total_known": len(self.known_peers),
            "active": active,
            "stale": stale,
            "dead": dead,
            "bootstrap_count": len(self.bootstrap),
        }
    
    def __repr__(self):
        return f"PeerDiscovery(known={len(self.known_peers)}, bootstrap={len(self.bootstrap)})"
''')
print("[+] Restored discovery.py")

# ============================================================
# 3. sync.py - Block Synchronization
# ============================================================
with open("time_protocol/sync.py", "w") as f:
    f.write('''"""
TIME Protocol - Block Synchronization
Real block sync between nodes.
"""

import socket
import json
import logging
from typing import List, Optional

logger = logging.getLogger("TimeProtocolSync")


class BlockSynchronizer:
    """
    Synchronizes the blockchain between nodes.
    Handles initial sync and chain replacement (longest chain wins).
    """
    
    def __init__(self, p2p_node=None, ledger=None):
        self.p2p = p2p_node
        self.ledger = ledger
    
    def request_chain_from_peer(self, host: str, port: int) -> Optional[List[dict]]:
        """Fetch the full chain from a peer."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10.0)
            s.connect((host, port))
            
            request = json.dumps({"type": "GET_CHAIN", "payload": None})
            s.sendall(request.encode('utf-8'))
            
            chunks = []
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                try:
                    data = json.loads(b"".join(chunks).decode('utf-8'))
                    if data.get("type") == "CHAIN_RESPONSE":
                        s.close()
                        return data.get("payload", [])
                except json.JSONDecodeError:
                    continue
            
            s.close()
            return None
        except Exception as e:
            logger.debug(f"Failed to fetch from {host}:{port}: {e}")
            return None
    
    def sync_with_peer(self, host: str, port: int) -> dict:
        """Sync our chain with a specific peer."""
        remote_chain = self.request_chain_from_peer(host, port)
        
        if remote_chain is None:
            return {"status": "ERROR", "message": "Failed to fetch remote chain"}
        
        if self.ledger and len(remote_chain) <= len(self.ledger.chain):
            return {
                "status": "UP_TO_DATE",
                "local_height": self.ledger.height,
                "remote_height": len(remote_chain) - 1,
            }
        
        if self.ledger:
            # Replace local chain
            from .block import Block
            new_chain = [Block.from_dict(bd) for bd in remote_chain]
            
            self.ledger.chain = []
            self.ledger.utxo_set = {}
            for block in new_chain:
                self.ledger.add_block(block)
        
        return {
            "status": "SYNCED",
            "new_height": len(remote_chain) - 1,
            "blocks_added": len(remote_chain) - (len(self.ledger.chain) if self.ledger else 0),
        }
    
    def sync_all(self) -> List[dict]:
        """Sync with all known peers."""
        results = []
        if self.p2p and hasattr(self.p2p, "peers"):
            for host, port in self.p2p.peers:
                result = self.sync_with_peer(host, port)
                result["peer"] = f"{host}:{port}"
                results.append(result)
        return results
''')
print("[+] Restored sync.py")

# ============================================================
# 4. time_protocol/__init__.py - Final export list
# ============================================================
with open("time_protocol/__init__.py", "w") as f:
    f.write('''"""
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
''')
print("[+] Restored __init__.py")

# ============================================================
# 5. Delete problematic alias files
# ============================================================
for bad_file in ["time_protocol/peer_discovery.py", "fix_clean_sync.py", "fix_all_issues.py",
                  "fix_everything_final.py", "fix_sync_clean.py", "fix_sync_final_syntax.py",
                  "fix_dangling_try.py", "fix_indentation.py", "fix_sync_indentation_exact.py",
                  "fix_sync_file_cleanly.py", "fix_all_v3_components.py", "fix_v3_comprehensive.py",
                  "fix_v3_final_alignment.py", "fix_v3_perfect_match.py", "fix_v3_absolute_perfection.py",
                  "fix_v3_ultimate.py", "fix_final_syntax_and_storage.py", "fix_final_sync_and_tests.py"]:
    if os.path.exists(bad_file):
        os.remove(bad_file)
        print(f"[-] Removed {bad_file}")

print()
print("✅ COMPLETE RESTORE DONE")
