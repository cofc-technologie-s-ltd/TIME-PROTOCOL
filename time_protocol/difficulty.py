"""
TIME Protocol - Difficulty Adjustment
Dynamic proof-of-work difficulty retargeting to maintain stable block times.
"""

import time
from typing import List


class DifficultyManager:
    """
    Bitcoin-style dynamic difficulty adjustment.
    
    Note: MAX_DIFFICULTY is capped at 6 because 16^6 ≈ 16.7M hashes
    is the practical limit for Python-based mining. Real blockchains
    use optimized C code and can handle much higher difficulties.
    """

    DEFAULT_TARGET_BLOCK_TIME = 10.0
    DEFAULT_RETARGET_INTERVAL = 10
    MIN_DIFFICULTY = 1
    MAX_DIFFICULTY = 6          # ← Reduced from 10 to prevent infinite mining
    MAX_ADJUSTMENT_FACTOR = 4.0
    MIN_ADJUSTMENT_FACTOR = 0.25

    def __init__(self, target_block_time: float = DEFAULT_TARGET_BLOCK_TIME,
                 retarget_interval: int = DEFAULT_RETARGET_INTERVAL):
        self.target_block_time = target_block_time
        self.retarget_interval = retarget_interval

    def should_retarget(self, next_block_index: int) -> bool:
        """Check if the NEXT block will trigger a retarget."""
        if next_block_index < self.retarget_interval:
            return False
        return next_block_index % self.retarget_interval == 0

    def calculate_next_difficulty(self, chain: List) -> int:
        """
        Calculate the difficulty for the next block.
        Returns the current difficulty if no retarget is due.
        """
        if not chain:
            return self.MIN_DIFFICULTY
        
        if len(chain) < 2:
            return chain[0].difficulty

        next_index = chain[-1].index + 1
        
        # Not a retarget point
        if not self.should_retarget(next_index):
            return chain[-1].difficulty

        # Need enough blocks for a full measurement window
        # We need retarget_interval intervals, so retarget_interval + 1 blocks
        if len(chain) < self.retarget_interval + 1:
            return chain[-1].difficulty

        # Take the last (retarget_interval + 1) blocks
        window = chain[-(self.retarget_interval + 1):]
        actual_time = window[-1].timestamp - window[0].timestamp

        if actual_time <= 0:
            return chain[-1].difficulty

        expected_time = self.retarget_interval * self.target_block_time
        current_difficulty = chain[-1].difficulty
        ratio = actual_time / expected_time

        # Clamp the ratio to prevent extreme changes
        if ratio > self.MAX_ADJUSTMENT_FACTOR:
            ratio = self.MAX_ADJUSTMENT_FACTOR
        elif ratio < self.MIN_ADJUSTMENT_FACTOR:
            ratio = self.MIN_ADJUSTMENT_FACTOR

        new_difficulty = int(current_difficulty / ratio)
        new_difficulty = max(self.MIN_DIFFICULTY, min(self.MAX_DIFFICULTY, new_difficulty))
        return new_difficulty

    def get_retarget_info(self, chain: List) -> dict:
        if not chain:
            return {
                "current_difficulty": 1,
                "next_difficulty": 1,
                "blocks_until_retarget": self.retarget_interval,
                "target_block_time": self.target_block_time,
                "average_block_time": 0,
                "retarget_interval": self.retarget_interval,
            }
        
        if len(chain) < 2:
            return {
                "current_difficulty": chain[0].difficulty,
                "next_difficulty": chain[0].difficulty,
                "blocks_until_retarget": self.retarget_interval,
                "target_block_time": self.target_block_time,
                "average_block_time": 0,
                "retarget_interval": self.retarget_interval,
            }

        next_index = chain[-1].index + 1
        blocks_since = next_index % self.retarget_interval
        if blocks_since == 0:
            blocks_until = self.retarget_interval
        else:
            blocks_until = self.retarget_interval - blocks_since

        window_size = min(self.retarget_interval, len(chain) - 1)
        window = chain[-(window_size + 1):]

        if len(window) >= 2 and window[-1].timestamp > window[0].timestamp:
            avg_block_time = (window[-1].timestamp - window[0].timestamp) / window_size
        else:
            avg_block_time = 0.0

        return {
            "current_difficulty": chain[-1].difficulty,
            "next_difficulty": self.calculate_next_difficulty(chain),
            "blocks_until_retarget": blocks_until,
            "target_block_time": self.target_block_time,
            "average_block_time": round(avg_block_time, 3),
            "retarget_interval": self.retarget_interval,
        }

    def estimate_hashrate(self, chain: List) -> float:
        if len(chain) < 2:
            return 0.0
        window_size = min(self.retarget_interval, len(chain) - 1)
        window = chain[-(window_size + 1):]
        if len(window) < 2:
            return 0.0
        actual_time = window[-1].timestamp - window[0].timestamp
        if actual_time <= 0:
            return 0.0
        difficulty = chain[-1].difficulty
        expected_hashes_per_block = 16 ** difficulty
        total_hashes = window_size * expected_hashes_per_block
        return total_hashes / actual_time

    def format_hashrate(self, hashrate: float) -> str:
        if hashrate < 1000:
            return f"{hashrate:.2f} H/s"
        elif hashrate < 1_000_000:
            return f"{hashrate / 1000:.2f} KH/s"
        elif hashrate < 1_000_000_000:
            return f"{hashrate / 1_000_000:.2f} MH/s"
        else:
            return f"{hashrate / 1_000_000_000:.2f} GH/s"
