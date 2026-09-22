import asyncio
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from time_ledger import SecureTimeLedger
from time_crypto import PostQuantumSigner
from time_network import SecureTimeNetworkNode
from time_consensus import TimeConsensusManager

# Load system configuration
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

app = FastAPI(
    title="TIME Protocol Sovereign REST API",
    description="Enterprise-grade REST interface for exchange integration (e.g., CoinEx, Bitget), custodial wallets, and external node synchronization.",
    version=CONFIG.get("version", "2.0.0-Sovereign"),
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global State & Node Cluster Initialization
sovereign_wallet = CONFIG["sovereign_master_wallet"]
shared_secret = CONFIG["network"]["shared_secret_key"]
threshold = CONFIG["network"]["quorum_threshold"]
nodes_conf = CONFIG["network"]["nodes"]
initial_reward = CONFIG["economics"]["block_reward"]

ledgers: Dict[str, SecureTimeLedger] = {nc["node_id"]: SecureTimeLedger() for nc in nodes_conf}
for l in ledgers.values():
    l.update_account(sovereign_wallet, 1000000000, 0, staked=500000)

network_nodes: Dict[str, SecureTimeNetworkNode] = {
    nc["node_id"]: SecureTimeNetworkNode(nc["node_id"], nc["host"], nc["port"], ledgers[nc["node_id"]], shared_secret) 
    for nc in nodes_conf
}

for nc in nodes_conf:
    curr_id = nc["node_id"]
    for peer in nodes_conf:
        if peer["node_id"] != curr_id:
            network_nodes[curr_id].register_peer(peer["node_id"], peer["host"], peer["port"])

consensus_manager = TimeConsensusManager(
    "Node_A", 
    network_nodes["Node_A"], 
    quorum_threshold=threshold, 
    block_reward=initial_reward
)

# Request & Response Data Models
class AccountResponse(BaseModel):
    address: str
    balance: int
    nonce: int
    staked: int

class TransactionProposal(BaseModel):
    address: str = Field(..., description="Target wallet address")
    balance: int = Field(..., description="New account balance post-state transition")
    nonce: int = Field(..., description="Monotonically increasing nonce")
    staked: int = Field(default=0, description="Staked collateral amount")

class TransactionResult(BaseModel):
    status: str
    committed: bool
    address: str
    nonce: int

class SignatureVerifyRequest(BaseModel):
    payload: Dict[str, Any]
    signature: str

class SignatureVerifyResponse(BaseModel):
    valid: bool

# API Endpoints
@app.get("/v1/status", tags=["System Status"])
async def get_system_status():
    return {
        "project": CONFIG["project_name"],
        "version": CONFIG["version"],
        "enterprise": CONFIG["enterprise"],
        "master_sovereign_wallet": sovereign_wallet,
        "quorum_threshold": threshold,
        "active_nodes": len(nodes_conf),
        "status": "OPERATIONAL"
    }

@app.get("/v1/account/{address}", response_model=AccountResponse, tags=["Ledger Queries"])
async def get_account_balance(address: str):
    account_data = ledgers["Node_A"].get_account(address)
    if not account_data:
        raise HTTPException(status_code=404, detail="Account not found in ledger state")
    return {
        "address": address,
        "balance": account_data["balance"],
        "nonce": account_data["nonce"],
        "staked": account_data["staked"]
    }

@app.post("/v1/transaction/propose", response_model=TransactionResult, tags=["Consensus Operations"])
async def propose_transaction(tx: TransactionProposal):
    success = await consensus_manager.propose_and_commit(
        tx.address, 
        tx.balance, 
        tx.nonce, 
        tx.staked
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Consensus rejected state transition (nonce collision or quorum failure)"
        )
    return {
        "status": "COMMITTED",
        "committed": True,
        "address": tx.address,
        "nonce": tx.nonce
    }

@app.post("/v1/crypto/verify-signature", response_model=SignatureVerifyResponse, tags=["Cryptography"])
async def verify_signature(req: SignatureVerifyRequest):
    is_valid = PostQuantumSigner.verify_payload(req.payload, req.signature, shared_secret)
    return {"valid": is_valid}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
