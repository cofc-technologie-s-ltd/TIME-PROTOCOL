"""
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
