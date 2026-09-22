"""
TIME Protocol - Interactive CLI Wallet
Real command-line interface for managing wallets and sending transactions.
"""

import cmd
import os
import json
import time
from typing import Optional
from .wallet import Wallet
from .node import Node
from .ledger import Ledger


WALLET_DIR = os.path.expanduser("~/.time_protocol/wallets")


class TimeCLI(cmd.Cmd):
    """
    Interactive command-line interface for TIME Protocol wallet operations.
    """
    
    intro = """
╔══════════════════════════════════════════════════════════════╗
║  TIME Protocol CLI Wallet v1.0                                ║
║  Type 'help' for commands, 'quit' to exit                     ║
╚══════════════════════════════════════════════════════════════╝
"""
    prompt = "time> "
    
    def __init__(self, wallet_file: Optional[str] = None):
        super().__init__()
        os.makedirs(WALLET_DIR, exist_ok=True)
        self.wallet: Optional[Wallet] = None
        self.node = Node(difficulty=3)
        self.wallet_file = wallet_file
        
        if wallet_file and os.path.exists(wallet_file):
            try:
                self.wallet = Wallet.load(wallet_file)
                print(f"[✓] Loaded wallet: {self.wallet.address}")
            except Exception as e:
                print(f"[!] Failed to load wallet: {e}")
    
    # ---------- Core commands ----------
    
    def do_new(self, arg):
        """new [label] - Create a new wallet."""
        label = arg.strip() or "default"
        self.wallet = Wallet()
        self.wallet.label = label
        print(f"[✓] New wallet created")
        print(f"    Address:     {self.wallet.address}")
        print(f"    Public key:  {self.wallet.public_key[:32]}...")
        print(f"    Label:       {label}")
        print(f"    ⚠️  Save it with: save <password>")
    
    def do_save(self, arg):
        """save <password> - Save current wallet to encrypted file."""
        if not self.wallet:
            print("[!] No wallet loaded")
            return
        password = arg.strip()
        if not password:
            print("[!] Usage: save <password>")
            return
        
        filepath = os.path.join(WALLET_DIR, f"{self.wallet.address[:16]}.wallet")
        self.wallet.save(filepath, password=password)
        self.wallet_file = filepath
        print(f"[✓] Wallet saved to: {filepath}")
    
    def do_load(self, arg):
        """load <filepath> <password> - Load an existing wallet."""
        parts = arg.strip().split(maxsplit=1)
        if len(parts) < 2:
            print("[!] Usage: load <filepath> <password>")
            return
        filepath, password = parts
        try:
            self.wallet = Wallet.load(filepath, password=password)
            self.wallet_file = filepath
            print(f"[✓] Wallet loaded: {self.wallet.address}")
        except Exception as e:
            print(f"[!] Failed to load: {e}")
    
    def do_info(self, arg):
        """info - Show wallet information."""
        if not self.wallet:
            print("[!] No wallet loaded")
            return
        balance = self.wallet.get_balance(self.node.ledger)
        print(f"""
╭─ Wallet Info ─────────────────────────────────────╮
│ Address:  {self.wallet.address}
│ Label:    {self.wallet.label or '(none)'}
│ Balance:  {balance:.8f} TIME
│ File:     {self.wallet_file or '(not saved)'}
╰───────────────────────────────────────────────────╯
""")
    
    def do_mine(self, arg):
        """mine <num_blocks> - Mine blocks to this wallet."""
        if not self.wallet:
            print("[!] No wallet loaded")
            return
        
        count = int(arg.strip()) if arg.strip() else 1
        print(f"[⛏]  Mining {count} block(s) to {self.wallet.address}...")
        
        for i in range(count):
            start = time.time()
            block = self.node.mine_pending_transactions(self.wallet.address, [])
            elapsed = time.time() - start
            print(f"[✓] Block #{block.index} mined in {elapsed:.2f}s "
                  f"(nonce: {block.nonce}, hash: {block.hash[:12]}...)")
        
        balance = self.wallet.get_balance(self.node.ledger)
        print(f"[💰] New balance: {balance:.8f} TIME")
    
    def do_send(self, arg):
        """send <recipient_address> <amount> - Send TIME to another address."""
        if not self.wallet:
            print("[!] No wallet loaded")
            return
        
        parts = arg.strip().split()
        if len(parts) != 2:
            print("[!] Usage: send <recipient_address> <amount>")
            return
        
        recipient, amount_str = parts
        try:
            amount = float(amount_str)
        except ValueError:
            print(f"[!] Invalid amount: {amount_str}")
            return
        
        try:
            tx = self.wallet.create_transaction(
                ledger=self.node.ledger,
                recipient=recipient,
                amount=amount,
                fee=1000  # минимальная комиссия
            )
            print(f"[✓] Transaction created: {tx.txid[:16]}...")
            print(f"    From:   {self.wallet.address}")
            print(f"    To:     {recipient}")
            print(f"    Amount: {amount}")
            print(f"[⛏]  Mining block to confirm...")
            self.node.mine_pending_transactions(self.wallet.address, [tx])
            print(f"[✓] Transaction confirmed")
        except Exception as e:
            print(f"[!] Transaction failed: {e}")
    
    def do_chain(self, arg):
        """chain - Display current blockchain summary."""
        print(f"""
╭─ Blockchain Status ──────────────────────────────╮
│ Height:       {self.node.ledger.latest_block.index}
│ Total blocks: {len(self.node.ledger.chain)}
│ Latest hash:  {self.node.ledger.latest_block.hash[:32]}...
│ Valid:        {self.node.ledger.is_chain_valid()}
╰──────────────────────────────────────────────────╯
""")
    
    def do_quit(self, arg):
        """quit - Exit the CLI."""
        print("Goodbye!")
        return True
    
    do_exit = do_quit
    do_EOF = do_quit


def main():
    import sys
    wallet_file = sys.argv[1] if len(sys.argv) > 1 else None
    TimeCLI(wallet_file).cmdloop()


if __name__ == "__main__":
    main()
