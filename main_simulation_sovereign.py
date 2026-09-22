import asyncio
import json
from time_ledger import SecureTimeLedger
from time_network import SecureTimeNetworkNode
from time_consensus import TimeConsensusManager

async def run_node_server(node: SecureTimeNetworkNode):
    await node.start_server()

async def main():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    sovereign_wallet = config["sovereign_master_wallet"]
    shared_secret = config["network"]["shared_secret_key"]
    threshold = config["network"]["quorum_threshold"]
    nodes_conf = config["network"]["nodes"]
    initial_reward = config["economics"]["block_reward"]

    print(f"==================================================")
    print(f"🚀 {config['project_name']} v{config['version']}")
    print(f"🏢 Enterprise: {config['enterprise']}")
    print(f"🏛️ Master Sovereign Wallet: {sovereign_wallet}")
    print(f"==================================================\n")

    ledgers = {nc["node_id"]: SecureTimeLedger() for nc in nodes_conf}
    
    # Initialize Master Sovereign Wallet with genesis supply
    for l in ledgers.values():
        l.update_account(sovereign_wallet, 1000000000, 0, staked=500000)

    network_nodes = {nc["node_id"]: SecureTimeNetworkNode(nc["node_id"], nc["host"], nc["port"], ledgers[nc["node_id"]], shared_secret) for nc in nodes_conf}

    for nc in nodes_conf:
        curr_id = nc["node_id"]
        for peer in nodes_conf:
            if peer["node_id"] != curr_id:
                network_nodes[curr_id].register_peer(peer["node_id"], peer["host"], peer["port"])

    server_tasks = [asyncio.create_task(run_node_server(node)) for node in network_nodes.values()]
    await asyncio.sleep(1)

    consensus_manager = TimeConsensusManager("Node_A", network_nodes["Node_A"], quorum_threshold=threshold, block_reward=initial_reward)
    
    print(f"[Simulation] Proposing sovereign economic transaction from Master Wallet...")
    success = await consensus_manager.propose_and_commit(sovereign_wallet, 1000000050, 1, staked=500000)
    print(f"⚡ TIME Protocol Consensus Result: {'COMMITTED ✅' in ['COMMITTED ✅' if success else 'REJECTED ❌'] or ('COMMITTED' if success else 'REJECTED')}")

    print(f"\n--- Sovereign Node Verification Status ---")
    for node_id, ledger in ledgers.items():
        print(f"[{node_id}] Account Data: {ledger.get_account(sovereign_wallet)}")

    for task in server_tasks:
        task.cancel()
    for ledger in ledgers.values():
        ledger.close()

    print(f"\n=== Sovereign Simulation Completed Successfully ===")

if __name__ == "__main__":
    asyncio.run(main())
