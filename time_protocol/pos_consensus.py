"""
TIME Protocol - Proof of Stake Consensus
Alternative to PoW - validators stake tokens to earn the right to produce blocks.
"""

import time
import hashlib
from typing import List, Dict, Optional


class Validator:
    """A staking validator."""
    
    def __init__(self, address: str, stake: float, joined_at: float = None):
        self.address = address
        self.stake = stake
        self.joined_at = joined_at or time.time()
        self.blocks_produced = 0
        self.slashed_amount = 0.0
        self.is_active = True
    
    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "stake": self.stake,
            "joined_at": self.joined_at,
            "blocks_produced": self.blocks_produced,
            "slashed_amount": self.slashed_amount,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Validator":
        v = cls(d["address"], d["stake"], d.get("joined_at"))
        v.blocks_produced = d.get("blocks_produced", 0)
        v.slashed_amount = d.get("slashed_amount", 0.0)
        v.is_active = d.get("is_active", True)
        return v


class ProofOfStakeConsensus:
    """
    Proof of Stake consensus engine.
    
    Validators stake tokens. Block producers are selected proportionally to stake.
    """
    
    MIN_STAKE = 100.0
    BLOCK_REWARD = 10.0
    SLASH_PERCENT = 0.05
    
    def __init__(self):
        self.validators: Dict[str, Validator] = {}
        self.current_epoch = 0
        self.epoch_length = 10
    
    def stake(self, address: str, amount: float) -> bool:
        if amount < self.MIN_STAKE:
            raise ValueError(f"Minimum stake is {self.MIN_STAKE}")
        
        if address in self.validators:
            self.validators[address].stake += amount
            self.validators[address].is_active = True
        else:
            self.validators[address] = Validator(address, amount)
        return True
    
    def unstake(self, address: str, amount: float) -> bool:
        if address not in self.validators:
            raise ValueError(f"Not a validator: {address}")
        
        v = self.validators[address]
        if v.stake < amount:
            raise ValueError(f"Insufficient stake")
        
        v.stake -= amount
        if v.stake < self.MIN_STAKE:
            v.is_active = False
        return True
    
    def select_validator(self, seed: Optional[str] = None) -> Optional[Validator]:
        active = [v for v in self.validators.values() if v.is_active]
        if not active:
            return None
        
        total_stake = sum(v.stake for v in active)
        if seed is None:
            seed = str(time.time())
        
        h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
        target = (h % 1_000_000) / 1_000_000
        cumulative = 0.0
        
        for v in active:
            cumulative += v.stake / total_stake
            if target <= cumulative:
                return v
        return active[-1]
    
    def produce_block(self, node, seed: Optional[str] = None) -> Optional[dict]:
        validator = self.select_validator(seed)
        if not validator:
            return None
        
        block = node.mine_pending_transactions(validator.address, [])
        validator.blocks_produced += 1
        
        if block.index % self.epoch_length == 0:
            self.current_epoch += 1
        
        return {
            "block_index": block.index,
            "producer": validator.address,
            "reward": self.BLOCK_REWARD,
            "epoch": self.current_epoch,
        }
    
    def slash(self, address: str, reason: str) -> float:
        if address not in self.validators:
            return 0.0
        
        v = self.validators[address]
        slash_amount = v.stake * self.SLASH_PERCENT
        v.stake -= slash_amount
        v.slashed_amount += slash_amount
        
        if v.stake < self.MIN_STAKE:
            v.is_active = False
        return slash_amount
    
    def get_stats(self) -> dict:
        active = [v for v in self.validators.values() if v.is_active]
        total_stake = sum(v.stake for v in self.validators.values())
        
        return {
            "total_validators": len(self.validators),
            "active_validators": len(active),
            "total_stake": total_stake,
            "current_epoch": self.current_epoch,
            "epoch_length": self.epoch_length,
            "min_stake": self.MIN_STAKE,
        }
    
    def get_validators_list(self) -> List[dict]:
        return [v.to_dict() for v in self.validators.values()]
