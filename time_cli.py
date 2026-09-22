#!/usr/bin/env python3
import sys
import json
import argparse
from time_sdk import TimeProtocolSDK

def main():
    parser = argparse.ArgumentParser(
        description="TIME Protocol Sovereign CLI - Enterprise Node Management Utility"
    )
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="TIME API Base URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available Commands")

    # Command: status
    subparsers.add_parser("status", help="Get sovereign cluster status")

    # Command: account
    acc_parser = subparsers.add_parser("account", help="Query account balance and state")
    acc_parser.add_argument("address", help="Wallet address to query")

    # Command: propose
    prop_parser = subparsers.add_parser("propose", help="Propose a state transition / transaction")
    prop_parser.add_argument("address", help="Target wallet address")
    prop_parser.add_argument("balance", type=int, help="New balance")
    prop_parser.add_argument("nonce", type=int, help="Monotonic nonce")
    prop_parser.add_argument("--staked", type=int, default=0, help="Staked collateral")

    args = parser.parse_args()
    sdk = TimeProtocolSDK(api_base_url=args.api_url)

    try:
        if args.command == "status":
            res = sdk.get_system_status()
            print(json.dumps(res, indent=2))
        elif args.command == "account":
            res = sdk.get_account(args.address)
            print(json.dumps(res, indent=2))
        elif args.command == "propose":
            res = sdk.propose_transaction(args.address, args.balance, args.nonce, args.staked)
            print(json.dumps(res, indent=2))
        else:
            parser.print_help()
    except Exception as e:
        print(f"❌ CLI Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
