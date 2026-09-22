"""
TIME Protocol - Network Discovery
Bootstrap nodes, peer exchange, and automatic reconnection.
"""

import time
import json
import socket
import threading
from typing import List, Tuple, Optional, Set


# Well-known bootstrap nodes (in a real deployment, these would be real servers)
DEFAULT_BOOTSTRAP_NODES = [
    ("127.0.0.1", 8001),
    ("127.0.0.1", 8002),
    ("127.0.0.1", 8003),
]


class PeerInfo:
    """Metadata about a known peer."""
    
    def __init__(self, host: str, port: int, last_seen: float = None):
        self.host = host
        self.port = port
        self.last_seen = last_seen or time.time()
        self.failures = 0
        self.connection_attempts = 0
    
    @property
    def address(self) -> Tuple[str, int]:
        return (self.host, self.port)
    
    def mark_seen(self):
        self.last_seen = time.time()
        self.failures = 0
    
    def mark_failed(self):
        self.failures += 1
        self.connection_attempts += 1
    
    def should_retry(self, max_failures: int = 5) -> bool:
        return self.failures < max_failures
    
    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "last_seen": self.last_seen,
            "failures": self.failures,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "PeerInfo":
        p = cls(d["host"], d["port"], d.get("last_seen"))
        p.failures = d.get("failures", 0)
        return p
    
    def __repr__(self):
        return f"PeerInfo({self.host}:{self.port})"


class PeerDiscovery:
    """
    Manages peer discovery and connection.
    
    Responsibilities:
    - Track known peers
    - Retry failed connections
    - Exchange peer lists with connected nodes
    - Remove stale peers
    """
    
    MAX_KNOWN_PEERS = 100
    PEER_TIMEOUT = 3600 * 24   # 24 hours
    RETRY_INTERVAL = 30         # Retry failed connections every 30s
    
    def __init__(self, own_port: int, bootstrap_nodes: List[Tuple[str, int]] = None):
        self.own_port = own_port
        self.known_peers: dict = {}    # (host, port) -> PeerInfo
        self.bootstrap = bootstrap_nodes or list(DEFAULT_BOOTSTRAP_NODES)
        
        # Add bootstrap peers
        for host, port in self.bootstrap:
            if port != own_port:  # Don't add ourselves
                self.add_peer(host, port)
    
    # ---------- Peer management ----------
    
    def add_peer(self, host: str, port: int) -> bool:
        """Add a peer to known peers. Returns True if newly added."""
        if port == self.own_port and host in ("127.0.0.1", "localhost"):
            return False  # Don't add ourselves
        
        key = (host, port)
        if key in self.known_peers:
            return False
        
        if len(self.known_peers) >= self.MAX_KNOWN_PEERS:
            # Remove oldest
            oldest = min(self.known_peers.values(), key=lambda p: p.last_seen)
            del self.known_peers[oldest.address]
        
        self.known_peers[key] = PeerInfo(host, port)
        return True
    
    def remove_peer(self, host: str, port: int) -> bool:
        """Remove a peer."""
        return self.known_peers.pop((host, port), None) is not None
    
    def mark_peer_seen(self, host: str, port: int):
        """Mark a peer as recently connected."""
        if (host, port) in self.known_peers:
            self.known_peers[(host, port)].mark_seen()
    
    def mark_peer_failed(self, host: str, port: int):
        """Mark a peer connection as failed."""
        if (host, port) in self.known_peers:
            self.known_peers[(host, port)].mark_failed()
    
    def get_active_peers(self) -> List[PeerInfo]:
        """Get all peers we should try to connect to."""
        now = time.time()
        active = []
        for peer in self.known_peers.values():
            # Skip stale peers
            if now - peer.last_seen > self.PEER_TIMEOUT:
                continue
            # Skip too many failures
            if not peer.should_retry():
                continue
            active.append(peer)
        return active
    
    def get_peer_list(self) -> List[dict]:
        """Serialize peer list for sharing with other nodes."""
        return [p.to_dict() for p in self.known_peers.values()]
    
    def merge_peer_list(self, peer_dicts: List[dict]) -> int:
        """
        Merge a received peer list from another node.
        Returns number of new peers added.
        """
        added = 0
        for pd in peer_dicts:
            if self.add_peer(pd["host"], pd["port"]):
                added += 1
        return added
    
    # ---------- Connection testing ----------
    
    def test_connection(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """Test if a peer is reachable via TCP."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            return False
    
    def probe_peer(self, host: str, port: int) -> dict:
        """
        Test a peer by sending a GET_CHAIN request.
        Returns a dict with connection status and peer info.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect((host, port))
            
            # Send GET_CHAIN
            request = json.dumps({"type": "GET_CHAIN", "payload": None})
            s.sendall(request.encode('utf-8'))
            
            # Read response
            response = s.recv(65536)
            s.close()
            
            data = json.loads(response.decode('utf-8'))
            
            if data.get("type") == "CHAIN_RESPONSE":
                chain = data.get("payload", [])
                self.mark_peer_seen(host, port)
                return {
                    "status": "OK",
                    "peer": f"{host}:{port}",
                    "height": len(chain) - 1 if chain else 0,
                }
            else:
                self.mark_peer_failed(host, port)
                return {"status": "INVALID_RESPONSE", "peer": f"{host}:{port}"}
        except Exception as e:
            self.mark_peer_failed(host, port)
            return {"status": "FAILED", "peer": f"{host}:{port}", "error": str(e)}
    
    def discover_all(self) -> dict:
        """
        Probe all known peers to find active ones.
        Returns summary of the discovery process.
        """
        results = []
        active_count = 0
        
        for peer in self.get_active_peers():
            result = self.probe_peer(peer.host, peer.port)
            result["last_seen"] = peer.last_seen
            results.append(result)
            if result["status"] == "OK":
                active_count += 1
        
        return {
            "total_probed": len(results),
            "active": active_count,
            "failed": len(results) - active_count,
            "results": results,
            "known_peers": len(self.known_peers),
        }
    
    def bootstrap_from_bootstrap_nodes(self) -> dict:
        """
        Bootstrap discovery by probing default bootstrap nodes.
        """
        added = 0
        for host, port in self.bootstrap:
            if port == self.own_port and host in ("127.0.0.1", "localhost"):
                continue
            if self.add_peer(host, port):
                added += 1
        
        return {
            "bootstrap_nodes": len(self.bootstrap),
            "newly_added": added,
            "total_known": len(self.known_peers),
        }
    
    # ---------- Status ----------
    
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
