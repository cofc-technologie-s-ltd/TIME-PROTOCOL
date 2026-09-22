import hashlib
import random
import socket
import json

class KademliaNode:
    """
    Pure Python implementation of Kademlia DHT for decentralized peer discovery.
    Uses 160-bit integer space and XOR metric.
    """
    def __init__(self, host: str, port: int, node_id: str = None):
        self.host = host
        self.port = port
        if not node_id:
            raw_id = f"{host}:{port}:{random.random()}"
            self.node_id = int(hashlib.sha1(raw_id.encode()).hexdigest(), 16)
        else:
            self.node_id = int(node_id, 16) if isinstance(node_id, str) else node_id
            
        self.routing_table = {}  # bucket_index -> list of (node_id, host, port)
        self.storage = {}        # Key-value local store for DHT

    def xor_distance(self, id1: int, id2: int) -> int:
        return id1 ^ id2

    def add_peer(self, peer_id: str, host: str, port: int):
        pid = int(peer_id, 16) if isinstance(peer_id, str) else peer_id
        if pid == self.node_id:
            return
        dist = self.xor_distance(self.node_id, pid)
        bucket_idx = dist.bit_length() - 1
        if bucket_idx < 0:
            bucket_idx = 0
            
        if bucket_idx not in self.routing_table:
            self.routing_table[bucket_idx] = []
            
        # Avoid duplicates, keep bucket size max 20 (k-parameter)
        existing = [p for p in self.routing_table[bucket_idx] if p[0] == pid]
        if not existing:
            if len(self.routing_table[bucket_idx]) >= 20:
                self.routing_table[bucket_idx].pop(0) # LRU drop
            self.routing_table[bucket_idx].append((pid, host, port))

    def find_closest_nodes(self, target_id: int, count: int = 3):
        all_peers = []
        for bucket in self.routing_table.values():
            all_peers.extend(bucket)
            
        all_peers.sort(key=lambda p: self.xor_distance(p[0], target_id))
        return all_peers[:count]

    def store_value(self, key: str, value: str):
        self.storage[key] = value

    def get_value(self, key: str):
        return self.storage.get(key, None)
