import socket
import threading
import json

class ProductionNodeServer:
    def __init__(self, host: str, port: int, dht_node, pbft_engine):
        self.host = host
        self.port = port
        self.dht_node = dht_node
        self.pbft_engine = pbft_engine
        self.server_socket = None
        self.is_running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(15)
        self.is_running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                conn, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            data = conn.recv(8192)
            if not data:
                return
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get("type")
            resp = {"status": "error", "reason": "unknown"}

            if msg_type == "PING":
                resp = {"status": "pong", "node_id": str(self.dht_node.node_id)}
            elif msg_type == "DHT_STORE":
                self.dht_node.store_value(message["key"], message["value"])
                resp = {"status": "stored"}
            elif msg_type == "DHT_FIND":
                val = self.dht_node.get_value(message["key"])
                resp = {"status": "found", "value": val}
            elif msg_type == "PBFT_PRE_PREPARE":
                resp = {"status": "acknowledged"}

            conn.sendall(json.dumps(resp).encode('utf-8'))
        except Exception as e:
            try:
                conn.sendall(json.dumps({"status": "error", "details": str(e)}).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
