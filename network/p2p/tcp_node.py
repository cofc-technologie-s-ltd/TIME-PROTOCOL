import socket
import threading
import json

class RealP2PNode:
    """
    True TCP Socket P2P Networking layer for cross-server communication.
    """
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.peers = set()  # Set of (host, port) tuples
        self.server_socket = None
        self.is_running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.is_running = True
        
        threading.Thread(target=self._accept_connections, daemon=True).start()

    def _accept_connections(self):
        while self.is_running:
            try:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, client_sock):
        try:
            data = client_sock.recv(4096)
            if data:
                message = json.loads(data.decode('utf-8'))
                # Handle inbound network message
                response = {"status": "received", "echo": message.get("type")}
                client_sock.sendall(json.dumps(response).encode('utf-8'))
        except Exception:
            pass
        finally:
            client_sock.close()

    def connect_to_peer(self, peer_host: str, peer_port: int, message: dict) -> dict:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_host, peer_port))
                s.sendall(json.dumps(message).encode('utf-8'))
                resp = s.recv(4096)
                return json.loads(resp.decode('utf-8'))
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
