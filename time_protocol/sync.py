"""
TIME Protocol - Block Synchronization
Real block sync protocol for new nodes joining the network.
Handles initial blockchain download (IBD) and chain reorganization.
"""

import logging
from typing import List, Optional, Tuple
from .block import Block
from .ledger import Ledger
from .p2p import P2PNode

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] SYNC: %(message)s')


class SyncError(Exception):
    """Sync-related errors."""
    pass


class BlockSynchronizer:
    """
    Manages synchronization of blockchain state between nodes.
    Implements a simplified version of Bitcoin's IBD (Initial Block Download).
    """
    
    def __init__(self, p2p_node: P2PNode, ledger: Ledger):
        self.p2p = p2p_node
        self.ledger = ledger
        self.is_syncing = False
        self.sync_peer: Optional[Tuple[str, int]] = None
    
    def request_chain_from_peer(self, host: str, port: int) -> Optional[List[dict]]:
        """
        Request the full chain from a specific peer.
        Returns the peer's chain as a list of block dicts, or None on error.
        """
        import socket
        import json
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((host, port))
            
            request = json.dumps({"type": "GET_CHAIN", "payload": None})
            s.sendall(request.encode('utf-8'))
            
            # Receive response in chunks
            chunks = []
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                # Try to parse - if valid JSON, we're done
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
            logging.error(f"Failed to request chain from {host}:{port}: {e}")
            return None
    
    def is_chain_better(self, remote_chain: List[dict]) -> bool:
        """
        Determine if remote chain is better than ours.
        Criteria: longer chain wins (in absence of difficulty adjustment).
        """
        return len(remote_chain) > len(self.ledger.chain)
    
    def validate_chain(self, remote_chain: List[dict]) -> bool:
        """
        Validate a full chain from a peer.
        Checks all blocks are properly linked and PoW is valid.
        """
        if not remote_chain:
            return False
        
        try:
            # Parse all blocks
            blocks = [Block.from_dict(b) for b in remote_chain]
            
            # Validate genesis
            if blocks[0].index != 0:
                logging.warning("Remote chain genesis block has wrong index")
                return False
            
            # Validate each block links to previous
            for i in range(1, len(blocks)):
                current = blocks[i]
                previous = blocks[i - 1]
                
                if current.index != previous.index + 1:
                    logging.warning(f"Chain break: block {current.index} != {previous.index + 1}")
                    return False
                
                if current.previous_hash != previous.hash:
                    logging.warning(f"Chain break at block {i}: hash mismatch")
                    return False
                
                if not current.is_valid(previous):
                    logging.warning(f"Invalid block at index {i}")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Chain validation failed: {e}")
            return False
    
    def replace_chain(self, remote_chain: List[dict]) -> bool:
        """
        Replace local chain with a validated remote chain.
        This is the "longest chain wins" rule.
        """
        if not self.validate_chain(remote_chain):
            return False
        
        logging.info(f"Replacing local chain ({len(self.ledger.chain)} blocks) "
                     f"with remote chain ({len(remote_chain)} blocks)")
        
        # Rebuild ledger from remote chain
        new_ledger = Ledger()
        new_ledger.chain = []
        new_ledger.utxo_set = {}
        
        for block_dict in remote_chain:
            block = Block.from_dict(block_dict)
            new_ledger.add_block(block)
        
        # Swap in the new chain
        self.ledger.chain = new_ledger.chain
        self.ledger.utxo_set = new_ledger.utxo_set
        
        return True
    
    def sync_with_peer(self, host: str, port: int) -> dict:
        """
        Perform a full sync with a specific peer.
        Returns a status report.
        """
        self.is_syncing = True
        self.sync_peer = (host, port)
        
        try:
            logging.info(f"Starting sync with {host}:{port}")
            remote_chain = self.request_chain_from_peer(host, port)
            
            if remote_chain is None:
                return {"status": "ERROR", "message": "Failed to fetch remote chain"}
            
            if not self.is_chain_better(remote_chain):
                return {
                    "status": "UP_TO_DATE",
                    "local_height": len(self.ledger.chain) - 1,
                    "remote_height": len(remote_chain) - 1
                }
            
            if not self.validate_chain(remote_chain):
                return {"status": "ERROR", "message": "Remote chain failed validation"}
            
            success = self.replace_chain(remote_chain)
            
            if success:
                return {
                    "status": "SYNCED",
                    "new_height": len(self.ledger.chain) - 1,
                    "blocks_added": len(remote_chain) - len(self.ledger.chain) + len(remote_chain),
                }
            else:
                return {"status": "ERROR", "message": "Chain replacement failed"}
        
        finally:
            self.is_syncing = False
            self.sync_peer = None
    
    def sync_with_all_peers(self) -> List[dict]:
        """Try syncing with all known peers, return results."""
        results = []
        for host, port in self.p2p.peers:
            result = self.sync_with_peer(host, port)
            result["peer"] = f"{host}:{port}"
            results.append(result)
        return results
