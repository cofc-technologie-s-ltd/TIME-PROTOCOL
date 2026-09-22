"""
TIME Protocol - SQLite Persistence Layer
Saves and loads the blockchain state to/from disk.
"""

import os
import json
import sqlite3
import time
from typing import Optional, List
from .block import Block
from .transaction import Transaction, TxInput, TxOutput
from .ledger import Ledger, UTXO


DEFAULT_DB_PATH = os.path.expanduser("~/.time_protocol/chain.db")


class Storage:
    """
    SQLite-backed storage for the TIME Protocol blockchain.
    Handles saving/loading blocks and UTXO set.
    """
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS blocks (
        block_index INTEGER PRIMARY KEY,
        block_hash TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        timestamp REAL NOT NULL,
        nonce INTEGER NOT NULL,
        merkle_root TEXT NOT NULL,
        block_json TEXT NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_block_hash ON blocks(block_hash);
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()
    
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ---------- Save operations ----------
    
    def save_block(self, block: Block):
        """Save a single block (idempotent - replaces if exists)."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO blocks 
                (block_index, block_hash, previous_hash, timestamp, nonce, merkle_root, block_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    block.index,
                    block.hash,
                    block.previous_hash,
                    block.timestamp,
                    block.nonce,
                    block.merkle_root,
                    json.dumps(block.to_dict(), default=str)
                )
            )
            conn.commit()
    
    def save_chain(self, chain: List[Block]):
        """Save an entire chain (bulk operation)."""
        with self._connect() as conn:
            # Clear existing (full replace)
            conn.execute("DELETE FROM blocks")
            
            for block in chain:
                conn.execute(
                    """
                    INSERT INTO blocks 
                    (block_index, block_hash, previous_hash, timestamp, nonce, merkle_root, block_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        block.index,
                        block.hash,
                        block.previous_hash,
                        block.timestamp,
                        block.nonce,
                        block.merkle_root,
                        json.dumps(block.to_dict(), default=str)
                    )
                )
            conn.commit()
    
    def save_metadata(self, key: str, value):
        """Save arbitrary metadata (version, last_save_time, etc.)."""
        if not isinstance(value, str):
            value = json.dumps(value, default=str)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
    
    # ---------- Load operations ----------
    
    def load_chain(self) -> List[Block]:
        """Load all blocks ordered by index."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT block_json FROM blocks ORDER BY block_index ASC"
            )
            blocks = []
            for row in cursor:
                block_dict = json.loads(row["block_json"])
                blocks.append(Block.from_dict(block_dict))
            return blocks
    
    def load_block(self, block_index: int) -> Optional[Block]:
        """Load a single block by index."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT block_json FROM blocks WHERE block_index = ?",
                (block_index,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Block.from_dict(json.loads(row["block_json"]))
    
    def load_metadata(self, key: str) -> Optional[str]:
        """Load metadata value."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT value FROM metadata WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            return row["value"] if row else None
    
    def get_block_count(self) -> int:
        """Return total number of blocks stored."""
        with self._connect() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM blocks")
            return cursor.fetchone()["cnt"]
    
    def get_latest_block_index(self) -> int:
        """Return the highest block index stored."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT MAX(block_index) as mx FROM blocks"
            )
            result = cursor.fetchone()["mx"]
            return result if result is not None else -1
    
    # ---------- Maintenance ----------
    
    def clear(self):
        """Wipe all data (use with caution!)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM blocks")
            conn.execute("DELETE FROM metadata")
            conn.commit()
    
    def export_json(self, filepath: str):
        """Export the chain to a JSON file (backup)."""
        chain = self.load_chain()
        data = {
            "exported_at": time.time(),
            "block_count": len(chain),
            "chain": [b.to_dict() for b in chain]
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def import_json(self, filepath: str):
        """Import a chain from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        
        blocks = [Block.from_dict(b) for b in data["chain"]]
        self.save_chain(blocks)
        return len(blocks)
    
    def stats(self) -> dict:
        """Return database statistics."""
        with self._connect() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as block_count,
                    MAX(block_index) as max_index,
                    MIN(timestamp) as first_timestamp,
                    MAX(timestamp) as last_timestamp
                FROM blocks
            """)
            row = cursor.fetchone()
            
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                "db_path": self.db_path,
                "db_size_bytes": db_size,
                "db_size_kb": round(db_size / 1024, 2),
                "block_count": row["block_count"],
                "max_index": row["max_index"],
                "first_block_time": row["first_timestamp"],
                "last_block_time": row["last_timestamp"],
            }


class PersistentNode:
    """
    A Node that persists its state to disk automatically.
    Wraps the standard Node and adds save/load capability.
    """
    
    def __init__(self, node, db_path: Optional[str] = None, autosave: bool = True):
        self.node = node
        self.storage = Storage(db_path)
        self.autosave = autosave
    
    def save(self):
        """Save the current chain to disk."""
        self.storage.save_chain(self.node.ledger.chain)
        self.storage.save_metadata("last_save", time.time())
        self.storage.save_metadata("height", self.node.ledger.height)
        self.storage.save_metadata("difficulty", self.node.difficulty)
    
    def load(self) -> bool:
        """
        Load chain from disk. Returns True if loaded successfully, 
        False if no data exists.
        """
        blocks = self.storage.load_chain()
        
        if not blocks:
            return False
        
        # Replace node's ledger with loaded chain
        self.node.ledger.chain = []
        self.node.ledger.utxo_set = {}
        
        for block in blocks:
            self.node.ledger.add_block(block)
        
        # Restore difficulty if saved
        saved_difficulty = self.storage.load_metadata("difficulty")
        if saved_difficulty:
            self.node.difficulty = int(saved_difficulty)
        
        return True
    
    def save_on_new_block(self, block):
        """Callback: save block as soon as it's mined."""
        self.storage.save_block(block)
    
    def clear(self):
        """Wipe all persisted data."""
        self.storage.clear()
    
    def stats(self) -> dict:
        return self.storage.stats()


class DifficultyPersistence:
    """
    Helper to persist DifficultyManager settings alongside the chain.
    """
    
    @staticmethod
    def save_settings(storage: Storage, manager):
        storage.save_metadata("difficulty_target_block_time", manager.target_block_time)
        storage.save_metadata("difficulty_retarget_interval", manager.retarget_interval)
    
    @staticmethod
    def load_settings(storage: Storage, default_target: float = 10.0, default_interval: int = 10) -> dict:
        target = storage.load_metadata("difficulty_target_block_time")
        interval = storage.load_metadata("difficulty_retarget_interval")
        return {
            "target_block_time": float(target) if target else default_target,
            "retarget_interval": int(interval) if interval else default_interval,
        }


class DifficultyPersistence:
    """Helper to persist DifficultyManager settings."""

    @staticmethod
    def save_settings(storage, manager):
        storage.save_metadata("difficulty_target_block_time", manager.target_block_time)
        storage.save_metadata("difficulty_retarget_interval", manager.retarget_interval)

    @staticmethod
    def load_settings(storage, default_target: float = 10.0, default_interval: int = 10) -> dict:
        target = storage.load_metadata("difficulty_target_block_time")
        interval = storage.load_metadata("difficulty_retarget_interval")
        return {
            "target_block_time": float(target) if target else default_target,
            "retarget_interval": int(interval) if interval else default_interval,
        }
