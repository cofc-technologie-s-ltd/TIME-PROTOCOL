import hashlib
from typing import List, Dict, Any

class BFTMessage:
    def __init__(self, stage: str, view: int, block_hash: str, validator_id: str, signature: str):
        self.stage = stage
        self.view = view
        self.block_hash = block_hash
        self.validator_id = validator_id
        self.signature = signature

class ProductionBFTConsensus:
    def __init__(self, validator_id: str, validators: List[str]):
        self.validator_id = validator_id
        self.validators = validators
        self.view = 0
        self.state: Dict[str, Dict[str, List[BFTMessage]]] = {}

    def threshold(self) -> int:
        n = len(self.validators)
        return (2 * n) // 3 + 1

    def create_proposal(self, block_data: Dict[str, Any]) -> str:
        raw = str(block_data).encode('utf-8')
        return hashlib.sha3_256(raw).hexdigest()

    def process_message(self, msg: BFTMessage) -> bool:
        if msg.block_hash not in self.state:
            self.state[msg.block_hash] = {"prepare": [], "precommit": [], "commit": []}
            
        stage_list = self.state[msg.block_hash][msg.stage]
        if not any(v.validator_id == msg.validator_id for v in stage_list):
            stage_list.append(msg)
            
        return len(stage_list) >= self.threshold()

    def has_consensus(self, block_hash: str, stage: str) -> bool:
        if block_hash not in self.state:
            return False
        return len(self.state[block_hash][stage]) >= self.threshold()
