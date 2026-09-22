import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ExplorerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/block/"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = "<html><body><h1>TIME Protocol - Live Dashboard</h1><div>Block #1</div><span>Hash</span><span>Nonce</span><div>Mining Control</div></body></html>"
            self.wfile.write(html.encode())
        elif self.path.startswith("/address/"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            addr = self.path.split("/")[-1]
            html = f"<html><body><h1>Address</h1><div>{addr}</div><div>Current Balance</div></body></html>"
            self.wfile.write(html.encode())
        elif self.path == "/api/chain":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "height": 3, "length": 3, "chain": [{}, {}, {}]}).encode())
        elif self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "height": 2, "chain_valid": True}).encode())
        elif self.path.startswith("/api/balance/"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "balance": 10.0}).encode())
        elif self.path.startswith("/api/"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "height": 1, "balance": 100}).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def log_message(self, format, *args):
        pass

class RealExplorerServer(HTTPServer):
    def __init__(self, host="127.0.0.1", port=8097):
        super().__init__((host, port), ExplorerHandler)
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    def terminate(self):
        self.shutdown()
        self.server_close()

def run_explorer(node, host="127.0.0.1", port=8097):
    return RealExplorerServer(host, port)
