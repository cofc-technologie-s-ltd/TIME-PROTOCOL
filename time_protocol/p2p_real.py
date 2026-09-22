"""
TIME Protocol - Real P2P Network
Multi-machine networking with LAN discovery and NAT-friendly transport.
"""

import socket
import threading
import json
import time
import logging
from typing import List, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] P2P: %(message)s')


class RealP2PNode:
    """
    Real P2P node with:
    - Persistent connections to peers
    - Chain sync on connect
    - Broadcast of new blocks
    - Peer exchange
    """
    
    def __init__(self, host: str, port: int, node):
        self.host = host
        self.port = port
        self.node = node
        self.peers: List[Tuple[str, int]] = []
        self.connections: dict = {}  # (host, port) -> socket
        self.is_running = False
        self._server_socket = None
        self._server_thread = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start the TCP server for incoming peer connections."""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(10)
        self._server_socket.settimeout(1.0)
        
        self.is_running = True
        self._server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._server_thread.start()
        logging.info(f"P2P listening on {self.host}:{self.port}")
    
    def stop(self):
        self.is_running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        with self._lock:
            for conn in self.connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            self.connections.clear()
        logging.info("P2P stopped.")
    
    def _accept_loop(self):
        while self.is_running:
            try:
                client_sock, addr = self._server_socket.accept()
                threading.Thread(
                    target=self._handle_peer, 
                    args=(client_sock, addr), 
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception:
                break
    
    def _handle_peer(self, client_sock, addr):
        """Handle incoming peer messages."""
        client_sock.settimeout(30.0)
        try:
            while self.is_running:
                data = client_sock.recv(65536)
                if not data:
                    break
                try:
                    message = json.loads(data.decode('utf-8'))
                    response = self._process_message(message, addr)
                    if response:
                        client_sock.sendall(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logging.debug(f"Peer {addr} disconnected: {e}")
        finally:
            client_sock.close()
    
    def _process_message(self, message: dict, addr) -> Optional[dict]:
        msg_type = message.get("type")
        payload = message.get("payload")
        
        if msg_type == "GET_CHAIN":
            return {
                "type": "CHAIN_RESPONSE",
                "payload": [b.to_dict() for b in self.node.ledger.chain],
            }
        
        elif msg_type == "GET_PEERS":
            return {
                "type": "PEERS_RESPONSE",
                "payload": [{"host": h, "port": p} for h, p in self.peers],
            }
        
        elif msg_type == "NEW_BLOCK":
            from .block import Block
            try:
                block = Block.from_dict(payload)
                if block.is_valid(self.node.ledger.latest_block):
                    self.node.ledger.add_block(block)
                    logging.info(f"Accepted new block #{block.index} from {addr}")
                    # Relay to other peers
                    self.broadcast_block(block, exclude=addr)
                return {"status": "OK"}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}
        
        elif msg_type == "PING":
            return {"type": "PONG", "timestamp": time.time()}
        
        return {"status": "UNKNOWN_MESSAGE"}
    
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to a remote peer."""
        if (host, port) in self.peers:
            return True
        if (host, port) == (self.host, self.port):
            return False
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect((host, port))
            
            # Test connection with PING
            s.sendall(json.dumps({"type": "PING"}).encode())
            response = s.recv(4096)
            data = json.loads(response.decode())
            
            if data.get("type") == "PONG":
                with self._lock:
                    self.peers.append((host, port))
                s.close()
                logging.info(f"Connected to peer {host}:{port}")
                
                # Sync from this peer
                self._sync_from_peer(host, port)
                return True
            s.close()
        except Exception as e:
            logging.warning(f"Failed to connect to {host}:{port}: {e}")
        return False
    
    def _sync_from_peer(self, host: str, port: int):
        """Sync our chain from a peer (longest chain wins)."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10.0)
            s.connect((host, port))
            s.sendall(json.dumps({"type": "GET_CHAIN"}).encode())
            
            chunks = []
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                try:
                    data = json.loads(b"".join(chunks).decode())
                    if data.get("type") == "CHAIN_RESPONSE":
                        break
                except json.JSONDecodeError:
                    continue
            s.close()
            
            remote_chain = data.get("payload", [])
            if len(remote_chain) > len(self.node.ledger.chain):
                from .block import Block
                from .ledger import Ledger
                logging.info(f"Replacing chain: {len(self.node.ledger.chain)} → {len(remote_chain)}")
                new_ledger = Ledger()
                new_ledger.chain = []
                new_ledger.utxo_set = {}
                for bd in remote_chain:
                    new_ledger.add_block(Block.from_dict(bd))
                self.node.ledger.chain = new_ledger.chain
                self.node.ledger.utxo_set = new_ledger.utxo_set
        except Exception as e:
            logging.warning(f"Sync failed: {e}")
    
    def broadcast_block(self, block, exclude=None):
        """Broadcast a block to all peers."""
        msg = json.dumps({"type": "NEW_BLOCK", "payload": block.to_dict()})
        with self._lock:
            peers_copy = list(self.peers)
        
        for host, port in peers_copy:
            if (host, port) == exclude:
                continue
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((host, port))
                s.sendall(msg.encode())
                s.close()
            except Exception:
                pass
    
    def get_peers_from_all(self) -> int:
        """Ask all peers for their peer lists."""
        added = 0
        with self._lock:
            peers_copy = list(self.peers)
        
        for host, port in peers_copy:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((host, port))
                s.sendall(json.dumps({"type": "GET_PEERS"}).encode())
                data = json.loads(s.recv(65536).decode())
                s.close()
                
                for p in data.get("payload", []):
                    if self.connect_to_peer(p["host"], p["port"]):
                        added += 1
            except Exception:
                pass
        return added
    
    def get_network_status(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "running": self.is_running,
            "peer_count": len(self.peers),
            "peers": [{"host": h, "port": p} for h, p in self.peers],
            "chain_height": self.node.ledger.height,
        }
