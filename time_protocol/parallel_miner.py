"""
TIME Protocol - Parallel Mining (Multi-Core)
Uses multiprocessing to search nonce ranges across CPU cores.
"""

import multiprocessing as mp
import time
import os
from typing import Optional, Tuple


# Global worker state - shared within each process
def _worker(args):
    """Worker function: search a range of nonces for a valid hash."""
    block_data, difficulty, start_nonce, range_size = args
    import hashlib
    
    target = "0" * difficulty
    end_nonce = start_nonce + range_size
    
    for nonce in range(start_nonce, end_nonce):
        # Reconstruct block hash with this nonce
        data = dict(block_data)
        data["nonce"] = nonce
        hash_input = str(data)
        h = hashlib.sha256(hash_input.encode()).hexdigest()
        
        if h.startswith(target):
            return (nonce, h)
    
    return None


class ParallelMiner:
    """
    Multi-core parallel miner using multiprocessing.
    
    Splits the nonce space across workers, each searches its own range.
    First to find a valid hash wins.
    """
    
    def __init__(self, workers: Optional[int] = None):
        self.workers = workers or mp.cpu_count()
    
    def mine_block(self, block, timeout: float = 60.0) -> Tuple[int, str]:
        """
        Mine a block using parallel workers.
        Modifies block.nonce and block.hash in place, returns (nonce, hash).
        """
        import hashlib
        
        target = "0" * block.difficulty
        start_time = time.time()
        
        # Prepare base block data (without nonce and hash)
        base_data = {
            "index": block.index,
            "previous_hash": block.previous_hash,
            "merkle_root": block.merkle_root,
            "timestamp": block.timestamp,
            "difficulty": block.difficulty,
        }
        
        # Nonce ranges per worker
        range_size = 50_000  # Each worker checks this many nonces per batch
        batch = 0
        
        while time.time() - start_time < timeout:
            # Spawn workers with staggered ranges
            tasks = []
            for i in range(self.workers):
                start = batch * range_size * self.workers + i * range_size
                tasks.append((base_data, block.difficulty, start, range_size))
            
            with mp.Pool(self.workers) as pool:
                results = pool.map(_worker, tasks)
            
            # Check if any worker found a solution
            for result in results:
                if result is not None:
                    nonce, h = result
                    block.nonce = nonce
                    block.hash = h
                    return (nonce, h)
            
            batch += 1
        
        # Timeout - fall back to serial mining
        return (block.mine(), block.hash)


class ParallelMiningService:
    """
    Background mining service using parallel miners.
    """
    
    def __init__(self, node, workers: Optional[int] = None, on_block_mined=None):
        self.node = node
        self.parallel_miner = ParallelMiner(workers=workers)
        self.on_block_mined = on_block_mined
        
        import threading
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._blocks_mined = 0
        self._last_block_time = 0.0
        self._started_at = None
        self._stop_requested = False
        self._miner_address = "PARALLEL_MINER"
    
    def start(self, miner_address: Optional[str] = None) -> dict:
        with self._lock:
            if self._running:
                return {"status": "ALREADY_RUNNING", "blocks_mined": self._blocks_mined}
            self._miner_address = miner_address or "PARALLEL_MINER"
            self._running = True
            self._stop_requested = False
            self._started_at = time.time()
            self._blocks_mined = 0
        
        import threading
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return {"status": "STARTED", "miner_address": self._miner_address, "workers": self.parallel_miner.workers}
    
    def stop(self, timeout: float = 10.0) -> dict:
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
    
    def _loop(self):
        from .block import Block
        from .transaction import TransactionBuilder
        
        while True:
            with self._lock:
                if self._stop_requested:
                    break
                miner = self._miner_address
            
            try:
                # Create block (without mining)
                reward_tx = TransactionBuilder.create_coinbase(miner, 50.0)
                next_difficulty = self.node._next_difficulty()
                
                new_block = Block(
                    index=self.node.ledger.latest_block.index + 1,
                    previous_hash=self.node.ledger.latest_block.hash,
                    transactions=[reward_tx],
                    difficulty=next_difficulty,
                )
                # Reset nonce/hash since we'll mine in parallel
                new_block.nonce = 0
                new_block.hash = new_block.calculate_hash()
                
                start = time.time()
                self.parallel_miner.mine_block(new_block)
                elapsed = time.time() - start
                
                self.node.ledger.add_block(new_block)
                
                with self._lock:
                    self._blocks_mined += 1
                    self._last_block_time = elapsed
                
                if self.on_block_mined:
                    try:
                        self.on_block_mined(new_block)
                    except Exception as e:
                        print(f"[!] Callback error: {e}")
            except Exception as e:
                print(f"[!] Parallel mining error: {e}")
                time.sleep(1.0)
    
    def status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "blocks_mined": self._blocks_mined,
                "current_height": self.node.ledger.height,
                "current_difficulty": self.node.ledger.latest_block.difficulty if self.node.ledger.chain else self.node.difficulty,
                "last_block_time": round(self._last_block_time, 4),
                "started_at": self._started_at,
                "uptime": (time.time() - self._started_at if self._started_at and self._running else 0),
                "miner_address": self._miner_address,
                "workers": self.parallel_miner.workers,
            }
    
    def is_running(self) -> bool:
        with self._lock:
            return self._running
