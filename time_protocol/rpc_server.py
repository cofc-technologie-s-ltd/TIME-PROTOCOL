"""
TIME Protocol - JSON-RPC / HTTP Server
Allows external applications to interact with the TIME Protocol node.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging


class RPCRequestHandler(BaseHTTPRequestHandler):
    node_instance = None

    def do_GET(self):
        if self.path == "/chain":
            self._send_json({
                "length": len(self.node_instance.ledger.chain),
                "height": self.node_instance.ledger.height,
                "chain": [b.to_dict() for b in self.node_instance.ledger.chain],
            })
        elif self.path.startswith("/balance/"):
            address = self.path.split("/")[-1]
            balance = self.node_instance.ledger.get_balance(address)
            self._send_json({"address": address, "balance": balance})
        elif self.path == "/mining/status":
            self._send_json(self.node_instance.miner.status())
        elif self.path == "/mining/info":
            self._send_json(self.node_instance.get_mining_info())
        elif self.path == "/stats":
            self._send_json({
                "height": self.node_instance.ledger.height,
                "difficulty": self.node_instance.difficulty,
                "chain_valid": self.node_instance.ledger.is_chain_valid(),
                "mining_running": self.node_instance.miner.is_running(),
            })
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            self._send_json({"error": "Invalid JSON"}, status=400)
            return

        if self.path == "/mine":
            miner_address = data.get("miner_address", "DEFAULT_MINER")
            block = self.node_instance.mine_pending_transactions(miner_address, [])
            self._send_json({"status": "SUCCESS", "block": block.to_dict()})
        elif self.path == "/mining/start":
            miner_address = data.get("miner_address", "DEFAULT_MINER")
            result = self.node_instance.miner.start(miner_address)
            self._send_json(result)
        elif self.path == "/mining/stop":
            result = self.node_instance.miner.stop()
            self._send_json(result)
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data: dict, status: int = 200):
        response = json.dumps(data, indent=2, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        return


def run_rpc_server(node, host: str = "127.0.0.1", port: int = 8545):
    RPCRequestHandler.node_instance = node
    server = HTTPServer((host, port), RPCRequestHandler)
    logging.info(f"RPC Server started on http://{host}:{port}")
    return server
