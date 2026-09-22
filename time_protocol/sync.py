"""
TIME Protocol - Block Synchronization
"""

import socket
import json
import logging
from typing import List, Optional

logger = logging.getLogger("TimeProtocolSync")


class BlockSynchronizer:
    def __init__(self, p2p_node=None, ledger=None):
        self.p2p = p2p_node
        self.ledger = ledger

    def request_chain_from_peer(self, host, port):
        """Fetch the full chain from a peer with proper chunk handling."""
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10.0)
            s.connect((host, port))
            
            # Send GET_CHAIN request
            request = json.dumps({"type": "GET_CHAIN", "payload": None})
            s.sendall(request.encode('utf-8'))
            
            # Receive response fully - wait for complete JSON
            chunks = b""
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                chunks += chunk
                # Try to parse - if valid JSON object with expected key, we're done
                try:
                    data = json.loads(chunks.decode('utf-8'))
                    if isinstance(data, dict) and data.get("type") == "CHAIN_RESPONSE":
                        return data.get("payload", [])
                    elif isinstance(data, dict) and "chain" in data:
                        return data["chain"]
                    elif isinstance(data, list):
                        return data
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
            
            return None
        except Exception as e:
            logger.debug(f"Fetch from {host}:{port} failed: {e}")
            return None
        finally:
            if s:
                try:
                    s.close()
                except Exception:
                    pass

    def sync_with_peer(self, host, port):
        remote_chain = self.request_chain_from_peer(host, port)
        
        if remote_chain is None:
            return {"status": "ERROR", "message": "Failed to fetch remote chain"}
        
        if not remote_chain:
            return {"status": "EMPTY", "message": "Remote chain is empty"}
        
        if self.ledger and len(remote_chain) <= len(self.ledger.chain):
            return {
                "status": "UP_TO_DATE",
                "local_height": self.ledger.height,
                "remote_height": len(remote_chain) - 1,
            }
        
        if self.ledger:
            from .block import Block
            try:
                new_chain = [Block.from_dict(bd) for bd in remote_chain]
                self.ledger.chain = []
                self.ledger.utxo_set = {}
                for block in new_chain:
                    self.ledger.add_block(block)
            except Exception as e:
                return {"status": "ERROR", "message": f"Chain parse failed: {e}"}
        
        return {
            "status": "SYNCED",
            "new_height": len(remote_chain) - 1,
        }

    def sync_all(self):
        results = []
        if self.p2p and hasattr(self.p2p, "peers"):
            for host, port in self.p2p.peers:
                result = self.sync_with_peer(host, port)
                result["peer"] = f"{host}:{port}"
                results.append(result)
        return results
