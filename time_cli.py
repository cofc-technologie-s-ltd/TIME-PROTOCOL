import sys
import argparse
import time
from mainnet_node import SovereignMainnetNode

def main():
    parser = argparse.ArgumentParser(description="TIME Protocol Sovereign Node CLI & Management Suite")
    parser.add_argument("action", choices=["start", "stop", "transact", "telemetry"], help="Operational action to execute")
    parser.add_argument("--node-id", default="VALIDATOR_ROOT_01", help="Unique node identifier")
    parser.add_argument("--host", default="127.0.0.1", help="Node bind address")
    parser.add_argument("--port", type=int, default=8080, help="Node bind port")
    parser.add_argument("--address", default="bc1q3cmhzwxa35egpqhr5eddrqqfmdd8jyeqqkky6h", help="Target address for transaction")
    parser.add_argument("--balance", type=int, default=1000, help="Transaction amount / balance update")

    args = parser.parse_args()
    node = SovereignMainnetNode(args.node_id, args.host, args.port)

    if args.action == "start":
        res = node.start_node()
        print(f"[TIME-MAINNET] Node started successfully: {res}")
    elif args.action == "stop":
        res = node.stop_node()
        print(f"[TIME-MAINNET] Node shut down: {res}")
    elif args.action == "transact":
        node.start_node()
        success = node.process_sovereign_transaction(args.address, args.balance, nonce=1, staked=500)
        print(f"[TIME-MAINNET] Transaction commit status for {args.address}: {success}")
        node.stop_node()
    elif args.action == "telemetry":
        node.start_node()
        print(f"[TIME-MAINNET] System Telemetry Metrics for {args.node_id}:")
        for k, v in node.telemetry.metrics.items():
            print(f" - {k}: {v}")
        node.stop_node()

if __name__ == "__main__":
    main()
