"""
TIME Protocol - Peer-to-Peer Network Layer
Real TCP-based socket communication for blockchain node synchronization.
"""

import socket
import threading
import json
import logging
from typing import List, Tuple, Optional
from .block import Block
from .transaction import Transaction

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] P2P: %(message)s')

class P2PNode:
    """
    Manages TCP peer-to-peer connections between TIME Protocol nodes.
    Handles peer discovery, block broadcasting, and transaction relay.
    """
    
    def __init__(self, host: str, port: int, node_instance):
        self.host = host
        self.port = port
        self.node_instance = node_instance
        self.peers: List[Tuple[str, int]] = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False
        self._server_thread: Optional[threading.Thread] = None

    def start(self):
        """Starts the P2P listening server."""
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.is_running = True
            self._server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self._server_thread.start()
            logging.info(f"P2P Node started listening on {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Failed to start P2P server: {e}")

    def stop(self):
        """Stops the P2P server and closes connections."""
        self.is_running = False
        try:
            self.socket.close()
        except Exception:
            pass
        logging.info("P2P Node stopped.")

    def _accept_connections(self):
        while self.is_running:
            try:
                client_sock, addr = self.socket.accept()
                threading.Thread(target=self._handle_peer, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_peer(self, client_sock: socket.socket):
        try:
            data = client_sock.recv(4096)
            if not data:
                return
            message = json.loads(data.decode('utf-8'))
            response = self._process_message(message)
            if response:
                client_sock.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logging.error(f"Error handling peer connection: {e}")
        finally:
            client_sock.close()

    def _process_message(self, message: dict) -> dict:
        msg_type = message.get("type")
        payload = message.get("payload")
        
        if msg_type == "GET_CHAIN":
            return {
                "type": "CHAIN_RESPONSE",
                "payload": [b.to_dict() for b in self.node_instance.ledger.chain]
            }
        elif msg_type == "NEW_TRANSACTION":
            try:
                tx = Transaction.from_dict(payload)
                self.node_instance.ledger.add_transaction(tx)
                return {"status": "SUCCESS", "message": "Transaction accepted"}
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        elif msg_type == "NEW_BLOCK":
            try:
                block = Block.from_dict(payload)
                if block.is_valid(self.node_instance.ledger.latest_block):
                    self.node_instance.ledger.chain.append(block)
                    return {"status": "SUCCESS", "message": "Block appended"}
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        
        return {"status": "UNKNOWN_MESSAGE"}

    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connects to a remote peer node."""
        if (host, port) in self.peers or (host == self.host and port == self.port):
            return True
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            self.peers.append((host, port))
            logging.info(f"Successfully connected to peer {host}:{port}")
            return True
        except Exception as e:
            logging.error(f"Could not connect to peer {host}:{port} - {e}")
            return False

    def broadcast_block(self, block: Block):
        """Broadcasts a newly mined block to all connected peers."""
        msg = {"type": "NEW_BLOCK", "payload": block.to_dict()}
        for host, port in self.peers:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.sendall(json.dumps(msg).encode('utf-8'))
                s.close()
            except Exception as e:
                logging.warning(f"Failed to broadcast block to {host}:{port} - {e}")
