import os

print("Cleaning up and applying precise fixes...")

# 1. Fix sync.py syntax error by restoring a clean try/except block with retry
sync_path = "time_protocol/sync.py"
if os.path.exists(sync_path):
    with open(sync_path, "r") as f:
        content = f.read()
    
    # Remove our previous broken block if present and restore clean sync call
    # Let's replace the block containing the syntax error with a valid try-except loop
    clean_retry_block = """
        import time
        import socket
        remote_chain = []
        for _ in range(5):
            try:
                remote_chain = self.request_chain_from_peer(host, port)
                if remote_chain:
                    break
            except (ConnectionRefusedError, socket.error, OSError):
                time.sleep(0.3)
    """
    
    # If old or broken code exists, let's rewrite/clean sync.py section or replace safely
    if "for _ in range(5):" in content:
        # Clean up potential duplicates
        content = content.replace(clean_retry_block, "")
    
    # Replace standard request with clean safe retry
    target_str = "remote_chain = self.request_chain_from_peer(host, port)"
    if target_str in content:
        content = content.replace(target_str, clean_retry_block.strip())
        
    with open(sync_path, "w") as f:
        f.write(content)
    print("[+] Cleaned and fixed sync.py")

# 2. Fix storage.py height assignment for test_save_and_load_chain (expecting height 2)
storage_path = "time_protocol/storage.py"
if os.path.exists(storage_path):
    with open(storage_path, "r") as f:
        storage_code = f.read()
    
    # Ensure ledger.height gets assigned correctly (e.g. len(chain) - 1)
    storage_code = storage_code.replace("ledger.height = len(ledger.chain) - 1 if len(ledger.chain) > 1 else len(ledger.chain)", "ledger.height = len(ledger.chain) - 1 if len(ledger.chain) > 0 else 0")
    
    # Alternatively, ensure height matches original if stored in metadata
    with open(storage_path, "w") as f:
        f.write(storage_code)
    print("[+] Fixed storage.py height logic")

print("Cleanup and fixes applied successfully!")
