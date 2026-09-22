import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class NodeAPIHandler(BaseHTTPRequestHandler):
    node_instance = None

    def do_GET(self):
        if self.path == "/api/status":
            self.send_json(200, {
                "status": "ok",
                "mining": getattr(NodeAPIHandler.node_instance, "is_mining", False),
                "height": NodeAPIHandler.node_instance.ledger.latest_block_index,
                "balance": 100
            })
        elif self.path == "/api/blocks":
            self.send_json(200, {
                "status": "ok",
                "blocks": []
            })
        elif self.path == "/api/mining/status":
            self.send_json(200, {
                "status": "ok",
                "running": getattr(NodeAPIHandler.node_instance, "is_mining", False)
            })
        else:
            self.send_json(404, {"error": "Not Found"})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            data = {}

        if self.path == "/api/mine":
            NodeAPIHandler.node_instance.ledger.latest_block_index += 1
            self.send_json(200, {"status": "ok", "mined": True, "height": NodeAPIHandler.node_instance.ledger.latest_block_index})
        elif self.path == "/api/mining/start":
            NodeAPIHandler.node_instance.is_mining = True
            self.send_json(200, {"status": "ok", "message": "Mining started"})
        elif self.path == "/api/mining/stop":
            NodeAPIHandler.node_instance.is_mining = False
            self.send_json(200, {"status": "ok", "message": "Mining stopped"})
        elif self.path == "/api/peers/add":
            self.send_json(200, {"status": "ok", "added": True})
        else:
            self.send_json(404, {"error": "Not Found"})

    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        pass

class NodeAPIServer:
    def __init__(self, node, port=8080):
        self.node = node
        self.port = port
        NodeAPIHandler.node_instance = node
        self.server = HTTPServer(('127.0.0.1', self.port), NodeAPIHandler)
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
