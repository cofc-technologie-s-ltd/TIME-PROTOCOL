import time
from typing import Dict, Any, List
from time_ledger import SecureTimeLedger
from time_consensus import TimeConsensusManager

class TimeClusterNode:
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.ledger = SecureTimeLedger()
        self.peers: Dict[str, str] = {}
        self.consensus = TimeConsensusManager(node_id, self, quorum_threshold=1)

    def register_peer(self, peer_id: str, endpoint: str):
        self.peers[peer_id] = endpoint

    def process_transaction(self, address: str, balance: int, nonce: int, staked: int) -> bool:
        return self.ledger.update_account(address, balance, nonce, staked)

class TimeClusterOrchestrator:
    def __init__(self, node_count: int = 3):
        self.nodes: List[TimeClusterNode] = []
        for i in range(node_count):
            node_id = f"VALIDATOR_NODE_{i+1}"
            port = 8000 + i
            self.nodes.append(TimeClusterNode(node_id, port))

        for node in self.nodes:
            for peer in self.nodes:
                if node.node_id != peer.node_id:
                    node.register_peer(peer.node_id, f"http://localhost:{peer.port}")

    def get_cluster_status(self) -> Dict[str, Any]:
        return {
            "active_nodes": len(self.nodes),
            "nodes": [n.node_id for n in self.nodes],
            "timestamp": time.time()
        }
