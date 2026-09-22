"""
TIME Protocol - Web Block Explorer
Flask-free HTTP server using only stdlib http.server.
Zero external dependencies.
"""

import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
from typing import Optional

from .template_engine import render_template


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


class ExplorerHandler(BaseHTTPRequestHandler):
    """
    HTTP handler for the TIME Protocol explorer.
    """
    
    ledger = None  # Injected by run_explorer
    node = None    # Injected by run_explorer
    
    # ---------- HTTP routing ----------
    
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            
            if path == "/" or path == "/index.html":
                self._render_index()
            elif path.startswith("/block/"):
                block_index = path.split("/")[-1]
                self._render_block(block_index)
            elif path.startswith("/address/"):
                address = unquote(path.split("/", 2)[-1])
                self._render_address(address)
            elif path == "/api/chain":
                self._api_chain()
            elif path == "/api/stats":
                self._api_stats()
            elif path == "/api/difficulty":
                self._api_difficulty()
            elif path.startswith("/api/block/"):
                block_index = path.split("/")[-1]
                self._api_block(block_index)
            elif path.startswith("/api/balance/"):
                address = unquote(path.split("/", 3)[-1])
                self._api_balance(address)
            else:
                self._error(404, "Not Found")
        except Exception as e:
            self._error(500, f"Server Error: {e}")
    
    # ---------- Page renderers ----------
    
    def _render_index(self):
        ledger = self.ledger
        chain = ledger.chain
        
        # Build blocks list for the table (most recent first, limit 20)
        blocks = []
        for block in reversed(chain[-20:]):
            blocks.append({
                "index": block.index,
                "hash": block.hash,
                "short_hash": block.hash[:16],
                "timestamp": block.timestamp,
                "time_str": self._format_time(block.timestamp),
                "nonce": f"{block.nonce:,}",
                "tx_count": len(block.transactions),
            })
        
        # Stats
        unspent = sum(1 for u in ledger.utxo_set.values())
        
        # Difficulty info
        difficulty_info = {}
        hashrate_str = "N/A"
        if self.node and hasattr(self.node, "difficulty_manager"):
            difficulty_info = self.node.difficulty_manager.get_retarget_info(chain)
            hashrate = self.node.difficulty_manager.estimate_hashrate(chain)
            hashrate_str = self.node.difficulty_manager.format_hashrate(hashrate)
        
        context = {
            "height": ledger.height,
            "total_blocks": len(chain),
            "total_utxos": unspent,
            "difficulty": ledger.latest_block.difficulty if ledger.chain else "?",
            "chain_valid": ledger.is_chain_valid(),
            "blocks": blocks,
            "blocks_until_retarget": difficulty_info.get("blocks_until_retarget", "?"),
            "avg_block_time": difficulty_info.get("average_block_time", 0),
            "target_block_time": difficulty_info.get("target_block_time", 10),
            "hashrate": hashrate_str,
        }
        
        html = self._load_template("index.html")
        rendered = render_template(html, context)
        self._send_html(rendered)
    
    def _render_block(self, block_index_str: str):
        try:
            block_index = int(block_index_str)
        except ValueError:
            return self._error(400, "Invalid block index")
        
        ledger = self.ledger
        if block_index < 0 or block_index >= len(ledger.chain):
            return self._error(404, f"Block #{block_index} not found")
        
        block = ledger.chain[block_index]
        
        # Prepare transactions data
        txs = []
        for tx in block.transactions:
            outputs = [
                {
                    "amount": f"{out.amount:.8f}",
                    "recipient_address": out.recipient_address,
                }
                for out in tx.outputs
            ]
            txs.append({
                "txid": tx.txid,
                "is_coinbase": any(inp.txid == "COINBASE" for inp in tx.inputs),
                "input_count": len(tx.inputs),
                "output_count": len(tx.outputs),
                "outputs": outputs,
            })
        
        context = {
            "block": {
                "index": block.index,
                "hash": block.hash,
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root,
                "timestamp": f"{block.timestamp:.2f}",
                "time_str": self._format_time(block.timestamp),
                "nonce": f"{block.nonce:,}",
                "tx_count": len(block.transactions),
                "transactions": txs,
            }
        }
        
        html = self._load_template("block.html")
        rendered = render_template(html, context)
        self._send_html(rendered)
    
    def _render_address(self, address: str):
        ledger = self.ledger
        
        balance = ledger.get_balance(address)
        utxos = [
            {
                "short_txid": u.txid[:24] + "...",
                "output_index": u.output_index,
                "amount": f"{u.amount:.8f}",
            }
            for u in ledger.get_utxos_for(address)
        ]
        
        context = {
            "address": address,
            "balance": f"{balance:.8f}",
            "utxo_count": len(utxos),
            "utxos": utxos,
        }
        
        html = self._load_template("address.html")
        rendered = render_template(html, context)
        self._send_html(rendered)
    
    # ---------- API endpoints ----------
    
    def _api_chain(self):
        ledger = self.ledger
        data = {
            "height": ledger.height,
            "length": len(ledger.chain),
            "chain": [b.to_dict() for b in ledger.chain],
        }
        self._send_json(data)
    
    def _api_difficulty(self):
        """Return current difficulty info."""
        ledger = self.ledger
        if not self.node or not hasattr(self.node, "difficulty_manager"):
            return self._send_json({"error": "Difficulty manager not available"}, status=404)
        
        info = self.node.difficulty_manager.get_retarget_info(ledger.chain)
        hashrate = self.node.difficulty_manager.estimate_hashrate(ledger.chain)
        info["hashrate"] = hashrate
        info["hashrate_formatted"] = self.node.difficulty_manager.format_hashrate(hashrate)
        self._send_json(info)
    
    def _api_stats(self):
        ledger = self.ledger
        data = {
            "height": ledger.height,
            "total_blocks": len(ledger.chain),
            "total_utxos": len(ledger.utxo_set),
            "difficulty": self.node.difficulty if self.node else None,
            "chain_valid": ledger.is_chain_valid(),
        }
        self._send_json(data)
    
    def _api_block(self, block_index_str: str):
        try:
            block_index = int(block_index_str)
        except ValueError:
            return self._send_json({"error": "Invalid index"}, status=400)
        
        ledger = self.ledger
        if block_index < 0 or block_index >= len(ledger.chain):
            return self._send_json({"error": "Block not found"}, status=404)
        
        block = ledger.chain[block_index]
        self._send_json(block.to_dict())
    
    def _api_balance(self, address: str):
        ledger = self.ledger
        balance = ledger.get_balance(address)
        self._send_json({
            "address": address,
            "balance": balance,
            "utxo_count": len(ledger.get_utxos_for(address)),
        })
    
    # ---------- Utilities ----------
    
    def _load_template(self, name: str) -> str:
        filepath = os.path.join(TEMPLATES_DIR, name)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    def _send_html(self, html: str, status: int = 200):
        encoded = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
    
    def _send_json(self, data: dict, status: int = 200):
        encoded = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
    
    def _error(self, status: int, message: str):
        html = f"""
        <!DOCTYPE html><html><head><title>Error {status}</title>
        <style>body{{background:#0a0e27;color:#e0e6ed;font-family:sans-serif;
        padding:50px;text-align:center}}h1{{font-size:4em;color:#ef4444}}
        a{{color:#4a9eff}}</style></head><body>
        <h1>{status}</h1><p>{message}</p>
        <p><a href="/">← Back to Explorer</a></p></body></html>
        """
        self._send_html(html, status=status)
    
    @staticmethod
    def _format_time(timestamp: float) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))
    
    def log_message(self, format, *args):
        # Clean console output
        return


def run_explorer(node, host: str = "127.0.0.1", port: int = 8080):
    """
    Start the Web Explorer server.
    Returns the HTTPServer instance (call .serve_forever() or run in thread).
    """
    ExplorerHandler.ledger = node.ledger
    ExplorerHandler.node = node
    server = HTTPServer((host, port), ExplorerHandler)
    print(f"[🌐] TIME Explorer running at http://{host}:{port}")
    return server
