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

    print(f"=== {config['project_name']} ({config['enterprise']}) ===")
    print(f"Master Sovereign Wallet: {sovereign_wallet}\n")

    ledgers = {nc["node_id"]: SecureTimeLedger() for nc in nodes_conf}
    for l in ledgers.values():
        l.update_account(sovereign_wallet, 3000000, 0)

    network_nodes = {nc["node_id"]: SecureTimeNetworkNode(nc["node_id"], nc["host"], nc["port"], ledgers[nc["node_id"]], shared_secret) for nc in nodes_conf}

    for nc in nodes_conf:
        curr_id = nc["node_id"]
        for peer in nodes_conf:
            if peer["node_id"] != curr_id:
                network_nodes[curr_id].register_peer(peer["node_id"], peer["host"], peer["port"])

    server_tasks = [asyncio.create_task(run_node_server(node)) for node in network_nodes.values()]
    await asyncio.sleep(1)

    consensus_manager = TimeConsensusManager("Node_A", network_nodes["Node_A"], quorum_threshold=threshold)
    success = await consensus_manager.propose_and_commit(sovereign_wallet, 3500000, 1)
    print(f"TIME Protocol Consensus Result: {'COMMITTED' if success else 'REJECTED'}")

    for task in server_tasks:
        task.cancel()
    for ledger in ledgers.values():
        ledger.close()

if __name__ == "__main__":
    asyncio.run(main())
