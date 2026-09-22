import asyncio
import json
from time_crypto import PostQuantumSigner

class SecureTimeNetworkNode:
    def __init__(self, node_id: str, host: str, port: int, ledger, secret_key: str):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.ledger = ledger
        self.secret_key = secret_key
        self.peers = {}
        self.server = None

    def register_peer(self, peer_id: str, host: str, port: int):
        self.peers[peer_id] = (host, port)

    async def start_server(self):
        self.server = await asyncio.start_server(self._handle_incoming_connection, self.host, self.port)
        async with self.server:
            await self.server.serve_forever()

    async def _handle_incoming_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        data = await reader.read(4096)
        if not data:
            writer.close()
            return
        try:
            packet = json.loads(data.decode('utf-8'))
            action = packet.get("action")
            signature = packet.get("signature")
            message_data = packet.get("data")

            if not PostQuantumSigner.verify_payload(message_data, signature, self.secret_key):
                response = {"status": "error", "message": "Invalid cryptographic signature"}
            elif action == "update":
                success = self.ledger.update_account(message_data.get("address"), message_data.get("balance"), message_data.get("nonce"))
                response = {"status": "success" if success else "failed"}
            else:
                response = {"status": "error", "message": "Unknown action"}

            writer.write(json.dumps(response).encode('utf-8'))
            await writer.drain()
        except Exception as e:
            writer.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def broadcast_signed_update(self, address: str, balance: int, nonce: int) -> dict:
        message_data = {"address": address, "balance": balance, "nonce": nonce}
        signature = PostQuantumSigner.sign_payload(message_data, self.secret_key)
        packet = {"action": "update", "sender_id": self.node_id, "data": message_data, "signature": signature}
        payload = json.dumps(packet).encode('utf-8')
        results = {}

        for peer_id, (peer_host, peer_port) in self.peers.items():
            try:
                reader, writer = await asyncio.open_connection(peer_host, peer_port)
                writer.write(payload)
                await writer.drain()
                res = json.loads((await reader.read(1024)).decode('utf-8'))
                results[peer_id] = (res.get("status") == "success")
                writer.close()
                await writer.wait_closed()
            except Exception:
                results[peer_id] = False
        return results
