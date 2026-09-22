"""
TIME Protocol - Web Block Explorer + Interactive Dashboard
Zero external dependencies.
"""

import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

from .template_engine import render_template


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class ExplorerHandler(BaseHTTPRequestHandler):
    ledger = None
    node = None

    # ---------- HTTP routing ----------
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            
            # Static files
            if path.startswith("/static/"):
                return self._serve_static(path)
            
            # Pages
            if path == "/" or path == "/index.html":
                return self._render_index()
            elif path.startswith("/block/"):
                return self._render_block(path.split("/")[-1])
            elif path.startswith("/address/"):
                return self._render_address(unquote(path.split("/", 2)[-1]))
            
            # API endpoints
            if path == "/api/status":
                return self._api_status()
            elif path == "/api/chain":
                return self._api_chain()
            elif path == "/api/stats":
                return self._api_stats()
            elif path == "/api/difficulty":
                return self._api_difficulty()
            elif path == "/api/blocks":
                return self._api_blocks()
            elif path.startswith("/api/block/"):
                return self._api_block(path.split("/")[-1])
            elif path.startswith("/api/balance/"):
                return self._api_balance(unquote(path.split("/", 3)[-1]))
            elif path == "/api/mining/status":
                return self._api_mining_status()
            
            self._error(404, "Not Found")
        except Exception as e:
            self._error(500, f"Server Error: {e}")
    
    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            
            # Read body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body.decode('utf-8')) if body else {}
            except Exception:
                return self._send_json({"error": "Invalid JSON"}, status=400)
            
            # Endpoints
            if path == "/api/mining/start":
                return self._api_mining_start(data)
            elif path == "/api/mining/stop":
                return self._api_mining_stop(data)
            elif path == "/api/mine":
                return self._api_mine_one(data)
            elif path == "/api/tx/send":
                return self._api_tx_send(data)
            
            self._error(404, "Not Found")
        except Exception as e:
            self._error(500, f"Server Error: {e}")
    
    # ---------- Static file serving ----------
    def _serve_static(self, path):
        rel = path[len("/static/"):]
        filepath = os.path.join(STATIC_DIR, rel)
        
        # Security: prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(STATIC_DIR)):
            return self._error(403, "Forbidden")
        
        if not os.path.exists(filepath):
            return self._error(404, "Not Found")
        
        with open(filepath, "rb") as f:
            content = f.read()
        
        # Content type
        if rel.endswith(".js"):
            ctype = "application/javascript"
        elif rel.endswith(".css"):
            ctype = "text/css"
        elif rel.endswith(".png"):
            ctype = "image/png"
        elif rel.endswith(".svg"):
            ctype = "image/svg+xml"
        else:
            ctype = "application/octet-stream"
        
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "public, max-age=60")
        self.end_headers()
        self.wfile.write(content)
    
    # ---------- Page renderers ----------
    def _render_index(self):
        ledger = self.ledger
        
        # Difficulty info
        difficulty_info = {}
        hashrate_str = "0 H/s"
        avg_block_time = 0
        blocks_until = "?"
        
        if self.node and hasattr(self.node, "difficulty_manager"):
            difficulty_info = self.node.difficulty_manager.get_retarget_info(ledger.chain)
            hashrate = self.node.difficulty_manager.estimate_hashrate(ledger.chain)
            hashrate_str = self.node.difficulty_manager.format_hashrate(hashrate)
            avg_block_time = difficulty_info.get("average_block_time", 0)
            blocks_until = difficulty_info.get("blocks_until_retarget", "?")
        
        # Blocks list
        blocks = []
        for block in reversed(ledger.chain[-20:]):
            blocks.append({
                "index": block.index,
                "hash": block.hash,
                "short_hash": block.hash[:16],
                "difficulty": block.difficulty,
                "time_str": self._format_time(block.timestamp),
                "tx_count": len(block.transactions),
                "nonce": block.nonce,
            })
        
        context = {
            "height": ledger.height,
            "total_blocks": len(ledger.chain),
            "total_utxos": len(ledger.utxo_set),
            "difficulty": ledger.latest_block.difficulty if ledger.chain else "?",
            "chain_valid": ledger.is_chain_valid(),
            "blocks": blocks,
            "blocks_until_retarget": blocks_until,
            "avg_block_time": avg_block_time,
            "target_block_time": difficulty_info.get("target_block_time", 10),
            "hashrate": hashrate_str,
        }
        
        html = self._load_template("index.html")
        rendered = render_template(html, context)
        self._send_html(rendered)
    
    def _render_block(self, idx_str):
        try:
            idx = int(idx_str)
        except ValueError:
            return self._error(400, "Invalid index")
        
        if idx < 0 or idx >= len(self.ledger.chain):
            return self._error(404, f"Block #{idx} not found")
        
        block = self.ledger.chain[idx]
        
        txs = []
        for tx in block.transactions:
            outputs = [{"amount": f"{o.amount:.8f}", "recipient_address": o.recipient_address} for o in tx.outputs]
            txs.append({
                "txid": tx.txid,
                "is_coinbase": any(i.txid == "COINBASE" for i in tx.inputs),
                "input_count": len(tx.inputs),
                "output_count": len(tx.outputs),
                "outputs": outputs,
            })
        
        context = {"block": {
            "index": block.index,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "merkle_root": block.merkle_root,
            "timestamp": f"{block.timestamp:.2f}",
            "time_str": self._format_time(block.timestamp),
            "nonce": f"{block.nonce:,}",
            "difficulty": block.difficulty,
            "tx_count": len(block.transactions),
            "transactions": txs,
        }}
        
        html = self._load_template("block.html")
        self._send_html(render_template(html, context))
    
    def _render_address(self, address):
        ledger = self.ledger
        balance = ledger.get_balance(address)
        utxos = [
            {"short_txid": u.txid[:24] + "...", "output_index": u.output_index, "amount": f"{u.amount:.8f}"}
            for u in ledger.get_utxos_for(address)
        ]
        
        context = {
            "address": address,
            "balance": f"{balance:.8f}",
            "utxo_count": len(utxos),
            "utxos": utxos,
        }
        
        html = self._load_template("address.html")
        self._send_html(render_template(html, context))
    
    # ---------- API ----------
    def _api_status(self):
        """Combined status for dashboard auto-refresh."""
        ledger = self.ledger
        
        # Mining
        mining_status = self.node.miner.status() if self.node and hasattr(self.node, "miner") else {"running": False, "blocks_mined": 0}
        
        # Difficulty info
        hashrate_str = "0 H/s"
        avg_time = 0
        if self.node and hasattr(self.node, "difficulty_manager"):
            hashrate = self.node.difficulty_manager.estimate_hashrate(ledger.chain)
            hashrate_str = self.node.difficulty_manager.format_hashrate(hashrate)
            info = self.node.difficulty_manager.get_retarget_info(ledger.chain)
            avg_time = info.get("average_block_time", 0)
        
        self._send_json({
            "height": ledger.height,
            "total_blocks": len(ledger.chain),
            "total_utxos": len(ledger.utxo_set),
            "current_difficulty": ledger.latest_block.difficulty if ledger.chain else 0,
            "chain_valid": ledger.is_chain_valid(),
            "mining": {
                "running": mining_status.get("running", False),
                "blocks_mined": mining_status.get("blocks_mined", 0),
                "last_block_time": mining_status.get("last_block_time", 0),
                "uptime": mining_status.get("uptime", 0),
            },
            "estimated_hashrate": hashrate_str,
            "avg_block_time": avg_time,
        })
    
    def _api_chain(self):
        ledger = self.ledger
        self._send_json({
            "height": ledger.height,
            "length": len(ledger.chain),
            "chain": [b.to_dict() for b in ledger.chain],
        })
    
    def _api_stats(self):
        ledger = self.ledger
        self._send_json({
            "height": ledger.height,
            "total_blocks": len(ledger.chain),
            "total_utxos": len(ledger.utxo_set),
            "difficulty": ledger.latest_block.difficulty if ledger.chain else None,
            "chain_valid": ledger.is_chain_valid(),
        })
    
    def _api_difficulty(self):
        if not self.node or not hasattr(self.node, "difficulty_manager"):
            return self._send_json({"error": "not available"}, status=404)
        info = self.node.difficulty_manager.get_retarget_info(self.ledger.chain)
        hashrate = self.node.difficulty_manager.estimate_hashrate(self.ledger.chain)
        info["hashrate"] = hashrate
        info["hashrate_formatted"] = self.node.difficulty_manager.format_hashrate(hashrate)
        self._send_json(info)
    
    def _api_blocks(self):
        """Get recent blocks (limit query param)."""
        parsed = urlparse(self.path)
        from urllib.parse import parse_qs
        params = parse_qs(parsed.query)
        limit = int(params.get("limit", ["10"])[0])
        limit = min(limit, 100)
        
        chain = self.ledger.chain[-limit:][::-1]  # Reverse for newest first
        blocks = [{
            "index": b.index,
            "hash": b.hash,
            "difficulty": b.difficulty,
            "time_str": self._format_time(b.timestamp),
            "tx_count": len(b.transactions),
            "nonce": b.nonce,
        } for b in chain]
        
        self._send_json({"blocks": blocks, "count": len(blocks)})
    
    def _api_block(self, idx_str):
        try:
            idx = int(idx_str)
        except ValueError:
            return self._send_json({"error": "Invalid index"}, status=400)
        if idx < 0 or idx >= len(self.ledger.chain):
            return self._send_json({"error": "Not found"}, status=404)
        self._send_json(self.ledger.chain[idx].to_dict())
    
    def _api_balance(self, address):
        self._send_json({
            "address": address,
            "balance": self.ledger.get_balance(address),
            "utxo_count": len(self.ledger.get_utxos_for(address)),
        })
    
    def _api_mining_status(self):
        if not self.node or not hasattr(self.node, "miner"):
            return self._send_json({"running": False}, status=404)
        self._send_json(self.node.miner.status())
    
    # ---------- POST handlers ----------
    def _api_mining_start(self, data):
        if not self.node or not hasattr(self.node, "miner"):
            return self._send_json({"error": "Mining not available"}, status=500)
        addr = data.get("miner_address", "WEB_MINER")
        result = self.node.miner.start(addr)
        self._send_json(result)
    
    def _api_mining_stop(self, data):
        if not self.node or not hasattr(self.node, "miner"):
            return self._send_json({"error": "Mining not available"}, status=500)
        result = self.node.miner.stop()
        self._send_json(result)
    
    def _api_mine_one(self, data):
        if not self.node:
            return self._send_json({"error": "Node not available"}, status=500)
        addr = data.get("miner_address", "WEB_MINER")
        try:
            block = self.node.mine_pending_transactions(addr, [])
            self._send_json({"status": "SUCCESS", "block": block.to_dict()})
        except Exception as e:
            self._send_json({"status": "ERROR", "error": str(e)}, status=500)
    
    def _api_tx_send(self, data):
        """Send a transaction from a wallet (using private key) to an address."""
        if not self.node:
            return self._send_json({"error": "Node not available"}, status=500)
        
        from ..wallet import Wallet
        from ..crypto import KeyPair
        
        try:
            from_addr = data.get("from", "").strip()
            to_addr = data.get("to", "").strip()
            amount = float(data.get("amount", 0))
            
            if not from_addr or not to_addr or amount <= 0:
                return self._send_json({"status": "ERROR", "error": "Missing or invalid fields"}, status=400)
            
            # If "from" looks like a private key (hex), create wallet from it
            if len(from_addr) == 64 and all(c in "0123456789abcdefABCDEF" for c in from_addr):
                kp = KeyPair(private_key=bytes.fromhex(from_addr))
                wallet = Wallet(key_pair=kp)
            else:
                return self._send_json({
                    "status": "ERROR",
                    "error": "Please provide a private key (hex) in 'from' field"
                }, status=400)
            
            tx = wallet.create_transaction(
                recipient=to_addr,
                amount=amount,
                ledger=self.node.ledger,
                fee=0.0,
            )
            
            # Auto-mine to confirm
            self.node.mine_pending_transactions(wallet.address, [tx])
            
            self._send_json({
                "status": "SUCCESS",
                "txid": tx.txid,
                "from": wallet.address,
                "to": to_addr,
                "amount": amount,
            })
        except Exception as e:
            self._send_json({"status": "ERROR", "error": str(e)}, status=500)
    
    # ---------- Helpers ----------
    def _load_template(self, name):
        with open(os.path.join(TEMPLATES_DIR, name), "r", encoding="utf-8") as f:
            return f.read()
    
    def _send_html(self, html, status=200):
        enc = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(enc)))
        self.end_headers()
        self.wfile.write(enc)
    
    def _send_json(self, data, status=200):
        enc = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(enc)))
        self.end_headers()
        self.wfile.write(enc)
    
    def _error(self, status, message):
        html = f"""<!DOCTYPE html><html><head><title>Error {status}</title>
        <style>body{{background:#0a0e27;color:#e0e6ed;font-family:sans-serif;padding:50px;text-align:center}}
        h1{{font-size:4em;color:#ef4444}}a{{color:#4a9eff}}</style></head><body>
        <h1>{status}</h1><p>{message}</p><p><a href="/">← Back</a></p></body></html>"""
        self._send_html(html, status=status)
    
    @staticmethod
    def _format_time(timestamp):
        return time.strftime("%H:%M:%S", time.gmtime(timestamp))
    
    def log_message(self, format, *args):
        return


def run_explorer(node, host="127.0.0.1", port=8080):
    ExplorerHandler.ledger = node.ledger
    ExplorerHandler.node = node
    server = HTTPServer((host, port), ExplorerHandler)
    print(f"[🌐] TIME Explorer at http://{host}:{port}")
    return server
