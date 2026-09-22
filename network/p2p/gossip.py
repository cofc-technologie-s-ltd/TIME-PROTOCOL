import json
from typing import List, Dict, Set, Tuple

class P2PGossipNetwork:
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.peers: Set[Tuple[str, int]] = set()
        self.message_log: List[Dict[str, Any]] = []

    def add_peer(self, host: str, port: int) -> bool:
        addr = (host, port)
        if addr not in self.peers and port != self.port:
            self.peers.add(addr)
            return True
        return False

    def broadcast(self, topic: str, payload: dict) -> int:
        msg = {"topic": topic, "sender": self.node_id, "payload": payload}
        self.message_log.append(msg)
        return len(self.peers)

    def get_stats(self) -> dict:
        return {
            "node_id": self.node_id,
            "port": self.port,
            "peers_count": len(self.peers),
            "peers": list(self.peers)
        }
