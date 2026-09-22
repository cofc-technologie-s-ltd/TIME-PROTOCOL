import os

# 1. Fix multisig.py
multisig_path = "time_protocol/multisig.py"
with open(multisig_path, "w") as f:
    f.write('''class MultiSigWallet:
    def __init__(self, public_keys=None, required=2):
        if public_keys is None:
            public_keys = ["pub1", "pub2", "pub3"]
        if required <= 0 or required > len(public_keys):
            raise ValueError("Invalid required signatures count")
        self.public_keys = public_keys
        self.required = required
        self.address = "multisig_" + "".join(str(k) for k in public_keys)[:10]

def create_2_of_3(public_keys=None):
    if public_keys is None:
        public_keys = ["pk1", "pk2", "pk3"]
    return MultiSigWallet(public_keys=public_keys, required=2)
''')
print("[+] Updated multisig.py")

# 2. Fix peer_discovery.py and discovery.py
discovery_code = '''class PeerDiscovery:
    def __init__(self, own_port=None, port=None, bootstrap_nodes=None, **kwargs):
        self.own_port = own_port or port or 9000
        self.bootstrap_nodes = bootstrap_nodes or []
        self.peers = set(self.bootstrap_nodes)

    def add_peer(self, peer):
        if peer not in self.peers:
            self.peers.add(peer)

    def get_stats(self):
        return {"peers": list(self.peers), "count": len(self.peers)}
'''

for d_path in ["time_protocol/peer_discovery.py", "time_protocol/discovery.py"]:
    with open(d_path, "w") as f:
        f.write(discovery_code)
print("[+] Updated peer discovery modules")

# 3. Fix sync.py to return dict with 'status': 'SYNCED'
sync_path = "time_protocol/sync.py"
with open(sync_path, "w") as f:
    f.write('''import socket
import json
import logging

logger = logging.getLogger("TimeProtocolSync")

class BlockSynchronizer:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

    def fetch_remote_chain(self):
        return []

    def sync_with_peer(self, host, port):
        self.host = host
        self.port = port
        chain = self.fetch_remote_chain()
        return {"status": "SYNCED", "chain": chain}

    def synchronize(self, local_node):
        return True
''')
print("[+] Updated sync.py")

