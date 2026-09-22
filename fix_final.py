import os

print("Applying final fixes for Storage height and P2P Sync...")

# 1. Fix storage load_chain height assignment
storage_path = "time_protocol/storage.py"
if os.path.exists(storage_path):
    with open(storage_path, "r") as f:
        code = f.read()
    
    # Ensure that when loading a chain, ledger height is correctly updated to match the loaded chain
    if "def load_chain" in code and "height" not in code:
        pass
    
    # Let's inject a safe height recalculation or assignment in load_chain if present
    replacement = """    def load_chain(self,"""
    # We can ensure ledger.height = len(ledger.chain) - 1 (or len) upon loading
    code = code.replace("return ledger", "if hasattr(ledger, 'height') and hasattr(ledger, 'chain'): ledger.height = len(ledger.chain) - 1 if len(ledger.chain) > 0 else 0\n        return ledger")
    
    with open(storage_path, "w") as f:
        f.write(code)
    print("[+] Updated time_protocol/storage.py")

# 2. Fix sync.py to handle ConnectionRefusedError gracefully in multi-node tests
sync_path = "time_protocol/sync.py"
if os.path.exists(sync_path):
    with open(sync_path, "r") as f:
        sync_code = f.read()
    
    # Catch socket/connection errors in request_chain_from_peer
    if "ConnectionRefusedError" not in sync_code and "except" in sync_code:
        sync_code = sync_code.replace("except Exception", "except (ConnectionRefusedError, socket.error, OSError)")
    
    with open(sync_path, "w") as f:
        f.write(sync_code)
    print("[+] Updated time_protocol/sync.py")

print("Final fixes applied successfully!")
