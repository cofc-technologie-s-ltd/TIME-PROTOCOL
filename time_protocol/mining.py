"""
TIME Protocol - Background Mining Service
Runs continuous mining in a background thread.
"""

import threading
import time
from typing import Optional, Callable


class MiningService:
    """
    Background mining service.
    
    Runs mining in a separate thread so the node can continue
    serving RPC/P2P requests while mining blocks.
    """
    
    def __init__(self, node, on_block_mined: Optional[Callable] = None):
        self.node = node
        self.on_block_mined = on_block_mined
        
        # State (thread-safe access via lock)
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._blocks_mined = 0
        self._last_block_time = 0.0
        self._started_at: Optional[float] = None
        self._stop_requested = False
    
    # ---------- Control ----------
    
    def start(self, miner_address: Optional[str] = None) -> dict:
        """Start mining in the background."""
        with self._lock:
            if self._running:
                return {"status": "ALREADY_RUNNING", "blocks_mined": self._blocks_mined}
            
            self._miner_address = miner_address or "DEFAULT_MINER"
            self._running = True
            self._stop_requested = False
            self._started_at = time.time()
            self._blocks_mined = 0
        
        self._thread = threading.Thread(target=self._mining_loop, daemon=True)
        self._thread.start()
        
        return {
            "status": "STARTED",
            "miner_address": self._miner_address,
            "started_at": self._started_at,
        }
    
    def stop(self, timeout: float = 10.0) -> dict:
        """Stop mining gracefully."""
        with self._lock:
            if not self._running:
                return {"status": "NOT_RUNNING", "blocks_mined": self._blocks_mined}
            self._stop_requested = True
        
        if self._thread:
            self._thread.join(timeout=timeout)
        
        with self._lock:
            self._running = False
        
        return {
            "status": "STOPPED",
            "blocks_mined": self._blocks_mined,
            "duration": time.time() - self._started_at if self._started_at else 0,
        }
    
    # ---------- Mining loop ----------
    
    def _mining_loop(self):
        """The main mining loop - runs until stopped."""
        while True:
            with self._lock:
                if self._stop_requested:
                    break
                miner = self._miner_address
            
            try:
                start = time.time()
                block = self.node.mine_pending_transactions(miner, [])
                elapsed = time.time() - start
                
                with self._lock:
                    self._blocks_mined += 1
                    self._last_block_time = elapsed
                
                # Callback (e.g., auto-save to disk)
                if self.on_block_mined:
                    try:
                        self.on_block_mined(block)
                    except Exception as e:
                        print(f"[!] Mining callback error: {e}")
            
            except Exception as e:
                print(f"[!] Mining error: {e}")
                time.sleep(1.0)
    
    # ---------- Status ----------
    
    def status(self) -> dict:
        """Return current mining status."""
        with self._lock:
            return {
                "running": self._running,
                "blocks_mined": self._blocks_mined,
                "current_height": self.node.ledger.height,
                "current_difficulty": (
                    self.node.ledger.latest_block.difficulty
                    if self.node.ledger.chain else self.node.difficulty
                ),
                "last_block_time": round(self._last_block_time, 4),
                "started_at": self._started_at,
                "uptime": (
                    time.time() - self._started_at if self._started_at and self._running
                    else 0
                ),
                "miner_address": getattr(self, "_miner_address", None),
            }
    
    def is_running(self) -> bool:
        with self._lock:
            return self._running




class AutoSaveMiningService(MiningService):
    """
    Mining service that auto-saves each block to persistent storage.
    """
    
    def __init__(self, node, storage=None, on_block_mined=None):
        self.storage = storage
        
        def combined_callback(block):
            # Save block to disk
            if self.storage:
                try:
                    self.storage.save_block(block)
                except Exception as e:
                    print(f"[!] Auto-save failed: {e}")
            
            # Call user callback
            if on_block_mined:
                on_block_mined(block)
        
        super().__init__(node, on_block_mined=combined_callback)
