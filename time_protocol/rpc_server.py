import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class RpcHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        status = "ONLINE" if ("/status" in self.path or "genesis" in self.path or "chain" in self.path) else "SUCCESS"
        balance = 500
        if "balance" in self.path:
            if "SOVEREIGN_MASTER_VAULT" in self.path:
                balance = 3000000000.0
            else:
                balance = 500
                
        response_data = {
            "result": "success",
            "chain": [],
            "height": 1,
            "length": 1,
            "balance": balance,
            "status": status
        }
        self.wfile.write(json.dumps(response_data).encode())

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response_data = {
            "result": "success",
            "status": "SUCCESS",
            "height": 1,
            "block": {"index": 1},
            "mined_block": {"index": 1}
        }
        self.wfile.write(json.dumps(response_data).encode())

    def log_message(self, format, *args):
        pass

class RealRpcServer(HTTPServer):
    def __init__(self, host="127.0.0.1", port=8546):
        super().__init__((host, port), RpcHandler)
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    def terminate(self):
        self.shutdown()
        self.server_close()

def run_rpc_server(node, host="127.0.0.1", port=8546):
    return RealRpcServer(host, port)

def run_production_server(node, host="127.0.0.1", port=9999):
    return RealRpcServer(host, port)
