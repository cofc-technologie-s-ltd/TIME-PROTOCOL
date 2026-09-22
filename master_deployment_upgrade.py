import os

os.makedirs("deploy/docker", exist_ok=True)
os.makedirs("scripts", exist_ok=True)

# 1. Dockerfile
with open("deploy/docker/Dockerfile", "w", encoding="utf-8") as f:
    f.write('''FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir cryptography

EXPOSE 8080 9091

CMD ["python", "scripts/run_cluster.py"]
''')

# 2. Docker Compose for Multi-Node Cluster
with open("deploy/docker/docker-compose.yml", "w", encoding="utf-8") as f:
    f.write('''version: '3.8'

services:
  time-node-1:
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
    ports:
      - "8080:8080"
      - "9091:9091"
    environment:
      - NODE_ID=1
      - NODE_PORT=9091
      - API_PORT=8080

  time-node-2:
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
    ports:
      - "8081:8080"
      - "9092:9091"
    environment:
      - NODE_ID=2
      - NODE_PORT=9091
      - API_PORT=8080
''')

# 3. Production Cluster Runner Script
with open("scripts/run_cluster.py", "w", encoding="utf-8") as f:
    f.write('''import os
import time
from network.p2p.tcp_node import RealP2PNode
from core.ledger.state_trie import RealStateLedger
from cryptography.hazmat.primitives.asymmetric import ed25519

def main():
    node_id = os.environ.get("NODE_ID", "1")
    port = int(os.environ.get("NODE_PORT", 9091))
    
    print(f"[+] Starting TIME-PROTOCOL Production Node #{node_id} on port {port}...")
    ledger = RealStateLedger()
    priv_key = ed25519.Ed25519PrivateKey.generate()
    
    node = RealP2PNode("0.0.0.0", port)
    node.start()
    print(f"[+] Node #{node_id} is running and listening for P2P/TCP traffic.")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        node.stop()
        print(f"[-] Node #{node_id} stopped gracefully.")

if __name__ == "__main__":
    main()
''')

print("[+] Successfully generated Dockerfile, Docker Compose, and Cluster Runner!")
