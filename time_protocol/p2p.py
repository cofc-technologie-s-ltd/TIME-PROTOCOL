"""
TIME Protocol - Peer-to-Peer Network Layer
TCP socket communication for blockchain node synchronization.
"""

import socket
import threading
import json
import logging
from typing import List, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] P2P: %(message)s')


class P2PNode:
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
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.is_running = True
            self._server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self._server_thread.start()
            logging.info(f"P2P Node started on {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Failed to start P2P: {e}")

    def stop(self):
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
            # Read all data until we have a complete JSON message
            data = b""
            while True:
                chunk = client_sock.recv(65536)
                if not chunk:
                    break
                data += chunk
                try:
                    message = json.loads(data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue
            
            if not data:
                return
            
            response = self._process_message(message)
            if response:
                response_bytes = json.dumps(response).encode('utf-8')
                client_sock.sendall(response_bytes)
        except Exception as e:
            logging.error(f"Error handling peer: {e}")
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def _process_message(self, message: dict) -> dict:
        msg_type = message.get("type")
        payload = message.get("payload")
        
        if msg_type == "GET_CHAIN":
            try:
                chain_data = [b.to_dict() for b in self.node_instance.ledger.chain]
                return {
                    "type": "CHAIN_RESPONSE",
                    "payload": chain_data,
                }
            except Exception as e:
                return {"type": "CHAIN_RESPONSE", "payload": [], "error": str(e)}
        
        elif msg_type == "PING":
            return {"type": "PONG", "timestamp": __import__("time").time()}
        
        elif msg_type == "GET_PEERS":
            return {
                "type": "PEERS_RESPONSE",
                "payload": [{"host": h, "port": p} for h, p in self.peers],
            }
        
        return {"status": "UNKNOWN_MESSAGE"}

    def connect_to_peer(self, host: str, port: int) -> bool:
        if (host, port) in self.peers or (host == self.host and port == self.port):
            return True
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((host, port))
            s.sendall(json.dumps({"type": "PING"}).encode())
            response = s.recv(4096)
            data = json.loads(response.decode())
            s.close()
            if data.get("type") == "PONG":
                self.peers.append((host, port))
                logging.info(f"Connected to {host}:{port}")
                return True
        except Exception as e:
            logging.debug(f"Connect to {host}:{port} failed: {e}")
        return False

    def broadcast_block(self, block, exclude=None):
        msg = json.dumps({"type": "NEW_BLOCK", "payload": block.to_dict()})
        for host, port in self.peers:
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

    def get_network_status(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "running": self.is_running,
            "peer_count": len(self.peers),
            "peers": [{"host": h, "port": p} for h, p in self.peers],
        }
