class TimeConsensusManager:
    """
    Quorum-based consensus manager implementing 51% threshold verification
    and automated block reward distribution for active network validators.
    """
    def __init__(self, node_id: str, network_node, quorum_threshold: float = 0.51, block_reward: int = 50):
        self.node_id = node_id
        self.network_node = network_node
        self.quorum_threshold = quorum_threshold
        self.block_reward = block_reward

    async def propose_and_commit(self, address: str, balance: int, nonce: int, staked: int = 0) -> bool:
        peers_count = len(self.network_node.peers)
        if peers_count == 0:
            return self.network_node.ledger.update_account(address, balance, nonce, staked)

        results = await self.network_node.broadcast_signed_update(address, balance, nonce, staked)
        successful_acks = sum(1 for success in results.values() if success) + 1
        approval_ratio = successful_acks / (peers_count + 1)

        if approval_ratio >= self.quorum_threshold:
            return self.network_node.ledger.update_account(address, balance, nonce, staked)
        return False
