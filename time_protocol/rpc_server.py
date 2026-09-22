"""
TIME Protocol - JSON-RPC / HTTP Server
Allows external applications to interact with the TIME Protocol node.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from .node import Node
from .transaction import Transaction

class RPCRequestHandler(BaseHTTPRequestHandler):
    node_instance: Node = None

    def do_GET(self):
        if self.path == "/chain":
            self._send_json({
                "length": len(self.node_instance.ledger.chain),
                "chain": [b.to_dict() for b in self.node_instance.ledger.chain]
            })
        elif self.path.startswith("/balance/"):
            address = self.path.split("/")[-1]
            balance = self.node_instance.ledger.get_balance(address)
            self._send_json({"address": address, "balance": balance})
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode('utf-8'))
        except Exception:
            self._send_json({"error": "Invalid JSON"}, status=400)
            return

        if self.path == "/mine":
            miner_address = data.get("miner_address", "DEFAULT_MINER")
            block = self.node_instance.mine_pending_transactions(miner_address, [])
            self._send_json({"status": "SUCCESS", "block": block.to_dict()})
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data: dict, status: int = 200):
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        # Silence default access logs to keep console clean during tests
        return

def run_rpc_server(node: Node, host: str = "127.0.0.1", port: int = 8545):
    RPCRequestHandler.node_instance = node
    server = HTTPServer((host, port), RPCRequestHandler)
    logging.info(f"RPC Server started on http://{host}:{port}")
    return server
