"""
TIME Protocol - Prometheus Metrics
"""

import time


class MetricsCollector:
    """Collects node metrics for Prometheus scraping."""
    
    def __init__(self, node):
        self.node = node
        self.start_time = time.time()
    
    def render_prometheus(self) -> str:
        ledger = self.node.ledger
        lines = []
        
        lines.append("# HELP time_protocol_height Current block height")
        lines.append("# TYPE time_protocol_height gauge")
        lines.append(f"time_protocol_height {ledger.height}")
        
        lines.append("# HELP time_protocol_total_blocks Total number of blocks")
        lines.append("# TYPE time_protocol_total_blocks counter")
        lines.append(f"time_protocol_total_blocks {len(ledger.chain)}")
        
        lines.append("# HELP time_protocol_difficulty Current difficulty")
        lines.append("# TYPE time_protocol_difficulty gauge")
        diff = ledger.latest_block.difficulty if ledger.chain else 0
        lines.append(f"time_protocol_difficulty {diff}")
        
        lines.append("# HELP time_protocol_utxos Total unspent outputs")
        lines.append("# TYPE time_protocol_utxos gauge")
        lines.append(f"time_protocol_utxos {len(ledger.utxo_set)}")
        
        lines.append("# HELP time_protocol_chain_valid Chain validity (1=valid)")
        lines.append("# TYPE time_protocol_chain_valid gauge")
        valid = 1 if ledger.is_chain_valid() else 0
        lines.append(f"time_protocol_chain_valid {valid}")
        
        if hasattr(self.node, "miner"):
            status = self.node.miner.status()
            lines.append("# HELP time_protocol_mining_running Mining status (1=running)")
            lines.append("# TYPE time_protocol_mining_running gauge")
            lines.append(f"time_protocol_mining_running {1 if status['running'] else 0}")
            
            lines.append("# HELP time_protocol_blocks_mined_total Blocks mined this session")
            lines.append("# TYPE time_protocol_blocks_mined_total counter")
            lines.append(f"time_protocol_blocks_mined_total {status['blocks_mined']}")
        
        uptime = time.time() - self.start_time
        lines.append("# HELP time_protocol_uptime_seconds Node uptime in seconds")
        lines.append("# TYPE time_protocol_uptime_seconds counter")
        lines.append(f"time_protocol_uptime_seconds {uptime:.1f}")
        
        return "\n".join(lines) + "\n"
